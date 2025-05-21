import pytz
from datetime import datetime
from typing import TypeVar, Literal


from app.middlewares.logger.loguru_logger import LoguruLogger
from app.middlewares.dilovod_client.dilovod_statistics_middleware import (
    DilovodStatisticsMiddleware)
from app.middlewares.dilovod_client.dilovod_client import DilovodClient
from app.middlewares.dilovod_client.dilovod_query_builder import (
    DilovodQueryBuilder as DQBuilder
)
from app.middlewares.shipment_processor import ShipmentProcessor
from app.middlewares.novapost_client.novapost_client import NovaPostClient
from app.middlewares.novapost_client.novapost_query_builder import (
    NovaPostQueryBuilder)
from app.middlewares.ukrpost_client.urkpost_client import UkrpostClient


kyiv_tz = pytz.timezone("Europe/Kiev")
logger = LoguruLogger().logger
dilovod_statistics: DilovodStatisticsMiddleware = DilovodStatisticsMiddleware()
dilovod_client: DilovodClient = DilovodClient(
    dilovod_statistics=dilovod_statistics)
dq_builder = DQBuilder()
shipment_processor = ShipmentProcessor()
novapost_client: NovaPostClient = NovaPostClient()
novapost_qb: NovaPostQueryBuilder = NovaPostQueryBuilder()
ukrpost_client: UkrpostClient = UkrpostClient()

T = TypeVar("T")

async def chunk_list(data: list[T], chunk_size: int) -> list[list[T]]:
    if chunk_size <= 0:
        raise ValueError("chunk_size має бути більшим за 0")

    result: list[list[T]] = []
    for i in range(0, len(data), chunk_size):
        result.append(data[i:i + chunk_size])
    return result


async def mail_tracking_on_branch():
    date: str = datetime.now(tz=kyiv_tz).strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f'''Mail tracking job started at {date}''')
    refund_on_the_branch: dict = await dilovod_client.get_orders_in_status(
        status='returned_to_branch')
    if refund_on_the_branch:
        sorted_orders: dict = await shipment_processor.sort_orders_by_delivery(
            dilovod_orders=refund_on_the_branch
        )
        await process_on_the_branch(sorted_orders=sorted_orders)


async def process_on_the_branch(sorted_orders: dict[str, list[dict]]):
    for delivery_method, orders in sorted_orders.items():
        if delivery_method == '1110400000001001':
            await handle_novapost_tracking(orders=orders)
        if delivery_method == '1110400000001002':
            await handle_ukrpost_tracking(orders=orders)


async def handle_ukrpost_tracking(orders: list[dict]):
    ukrpost_data, ttn_mapper = await retrieve_ukr_post_data(
        dilovod_orders=orders,
        ttn_statuses={}
    )
    await ukrpost_client.ukrpost_status_mapper(
        ttn_mapper=ttn_mapper,
        ukrpost_data=ukrpost_data)
    dilovod_id_in_status: list[str] = await (
        shipment_processor.get_in_status(
            ttn_mapper=ttn_mapper,
            target_status='41010'))
    target_count: int = 3
    await proccess_refund_if_condition(
        orders=orders,
        target_count=target_count,
        dilovod_ids_in_status=dilovod_id_in_status,
        from_storage='Ukrpost'
    )


async def retrieve_ukr_post_data(
        dilovod_orders: list[dict],
        ttn_statuses: dict):
    try:
        request_chunked, ttn_mapper = await (
            ukrpost_client.check_bunch_ttn_statuses(
                ttn_mapper=ttn_statuses,
                dilovod_orders=dilovod_orders))
        return request_chunked, ttn_mapper
    except ValueError:
        logger.warning('0 TTN`s was found in "refund_on_the_road"')
        return None


async def handle_novapost_tracking(orders: list[dict]):
    novapost_resps, novapost_ttn_statuses = await retrieve_novapost_data(
                dilovod_orders=orders)
    target_count: int = 3
    await novapost_client.remap_if_new_ttn(
        np_responses=novapost_resps,
        ttn_statuses=novapost_ttn_statuses,
        key='ttn_number'
    )
    dilovod_id_in_status: list[str] = await (
        shipment_processor.get_in_status(
            ttn_mapper=novapost_ttn_statuses,
            target_status='9'))
    await proccess_refund_if_condition(
        orders=orders,
        target_count=target_count,
        dilovod_ids_in_status=dilovod_id_in_status,
        from_storage='Novapost'
    )


async def proccess_refund_if_condition(
        orders: list[dict],
        target_count: int,
        dilovod_ids_in_status: list[str],
        from_storage: Literal['Novapost', 'Ukrpost']):
    current_count: int = len(dilovod_ids_in_status)
    print('np current count of orders for trigger: ', current_count)
    if current_count >= target_count:
        chunked_id_list: list[list[T]] = await chunk_list(
            data=dilovod_ids_in_status,
            chunk_size=target_count)
        print('np triggered')
        for chunk in chunked_id_list:
            print(type(chunk))
            print(chunk)
            if len(chunk) < target_count:
                continue
            await shipment_processor.process_refunded_shipments(
                orders=orders,
                dilovod_id_in_status=chunk,
                from_storage=from_storage
            )


async def retrieve_novapost_data(
        dilovod_orders: list[dict]) -> tuple[list[dict], dict]:
    np_request_body, ttn_statuses = await novapost_qb.prepare_request(
                dilovod_orders=dilovod_orders
            )
    try:
        np_responses: list[dict] = await (
            novapost_client.check_bunch_ttn_statuses(
                request_body_list=np_request_body))
        return np_responses, ttn_statuses
    except ValueError:
        logger.warning('0 TTN`s was found in "refund_on_the_road"')
