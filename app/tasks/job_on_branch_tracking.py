import pytz
from datetime import datetime


from app.middlewares.logger.loguru_logger import LoguruLogger
from app.middlewares.dilovod_client.dilovod_statistics_middleware import (
    DilovodStatisticsMiddleware)
from app.middlewares.dilovod_client.dilovod_client import DilovodClient
from app.middlewares.shipment_processor import ShipmentProcessor
from app.middlewares.novapost_client.novapost_client import NovaPostClient
from app.middlewares.novapost_client.novapost_query_builder import (
    NovaPostQueryBuilder)


kyiv_tz = pytz.timezone("Europe/Kiev")
logger = LoguruLogger().logger
dilovod_statistics: DilovodStatisticsMiddleware = DilovodStatisticsMiddleware()
dilovod_client: DilovodClient = DilovodClient(
    dilovod_statistics=dilovod_statistics)
shipment_processor = ShipmentProcessor()
novapost_client: NovaPostClient = NovaPostClient()
novapost_qb: NovaPostQueryBuilder = NovaPostQueryBuilder()


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
            ...
            # await handle_ukrpost_tracking(
            # orders=orders)


async def handle_novapost_tracking(orders: list[dict]):
    novapost_resps, novapost_ttn_statuses = await retrieve_novapost_data(
                dilovod_orders=orders)
    target_count: int = 20
    await novapost_client.remap_if_new_ttn(
        np_responses=novapost_resps,
        ttn_statuses=novapost_ttn_statuses,
        key='ttn_number'
    )
    dilovod_id_in_status: list[str] = await (
        shipment_processor.get_in_status(
            ttn_mapper=novapost_ttn_statuses,
            target_status='9'))
    current_count: int = len(dilovod_id_in_status)
    # if current_count > target_count:
        # for order in orders



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
