import pytz
from datetime import datetime


from app.middlewares.logger.loguru_logger import LoguruLogger
from app.middlewares.dilovod_client.dilovod_client import DilovodClient
from app.middlewares.dilovod_client.dilovod_query_builder import (
    DilovodQueryBuilder)
from app.middlewares.dilovod_client.dilovod_statistics_middleware import (
    DilovodStatisticsMiddleware)
from app.middlewares.novapost_client.novapost_client import NovaPostClient
from app.middlewares.novapost_client.novapost_query_builder import (
    NovaPostQueryBuilder)
from app.middlewares.ukrpost_client.urkpost_client import UkrpostClient
from app.middlewares.shipment_processor import ShipmentProcessor


kyiv_tz = pytz.timezone("Europe/Kiev")
logger = LoguruLogger().logger
dilovod_statistics: DilovodStatisticsMiddleware = DilovodStatisticsMiddleware()
dilovod_client: DilovodClient = DilovodClient(
    dilovod_statistics=dilovod_statistics)
dilovod_qb = DilovodQueryBuilder()
ukrpost_client: UkrpostClient = UkrpostClient()
novapost_client: NovaPostClient = NovaPostClient()
novapost_qb: NovaPostQueryBuilder = NovaPostQueryBuilder()
shipment_processor = ShipmentProcessor()


async def mail_tracking_on_road():
    date: str = datetime.now(tz=kyiv_tz).strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f'''Mail "on road" tracking job started at {date}''')
    refund_on_the_road: dict = await dilovod_client.get_orders_in_status(
        status='refund_on_the_road')
    if refund_on_the_road:
        sorted_orders_on_road: dict = await (
            shipment_processor.sort_orders_by_delivery(
                dilovod_orders=refund_on_the_road))
        try:
            await process_on_the_road(sorted_orders=sorted_orders_on_road)
            logger.info('"mail_tracking_on_road" finished successfully')
        except Exception as e:
            logger.error(f'''Something went wrong while
                            "mail_tracking_on_road" execution
                            Message: {e}''')
    # else:
    #     logger.info('No mails in "on the road" state')


async def process_on_the_road(sorted_orders: dict[str, list[dict]]):
    for delivery_method, orders in sorted_orders.items():
        if delivery_method == '1110400000001001':
            await handle_novapost_tracking(orders=orders)
        if delivery_method == '1110400000001002':
            await handle_ukrpost_tracking(
                orders=orders)


async def handle_novapost_tracking(orders: list[dict]):
    novapost_resps, novapost_ttn_statuses = await retrieve_novapost_data(
                dilovod_orders=orders)
    remap_ttn_statuses = await novapost_client.remap_if_new_ttn(
            np_responses=novapost_resps,
            ttn_statuses=novapost_ttn_statuses,
            key='ttn_number')
    new_ttns: list[str] = []
    for s_data in remap_ttn_statuses.values():
        print(s_data)
        new_ttn: str = s_data.get('new_ttn_number')
        if not new_ttn:
            continue
        new_ttns.append(new_ttn)
    print('new_ttns: ', new_ttns)
    np_ttn_chunked: list[str] = await novapost_qb.chunk_ttn_list(
        ttn=new_ttns,
        units_per_chunl=99)
    print('np_ttn_chunked: ', np_ttn_chunked)
    np_request_body: list[dict] = await novapost_qb.fortam_shipment_doc(
        ttn_chunked_list=np_ttn_chunked
    )
    print('np_request_body: ', np_request_body)
    np_responses: list[dict] = await (
        novapost_client.check_bunch_ttn_statuses(
            request_body_list=np_request_body))
    print('np_responses: ', np_responses)
    remap_ttn_statuses: dict = await novapost_client.remap_if_new_ttn(
        np_responses=np_responses,
        ttn_statuses=remap_ttn_statuses,
        key='new_ttn_number')
    print('remap_ttn_statuses: ', remap_ttn_statuses)
    # print('remup ttn statuses after checking: ', remap_ttn_statuses)
    if not remap_ttn_statuses:
        logger.warning('0 orders in NovaPost Delivery')
        return
    await (
        shipment_processor.handle_delivery_update(
            ttn_mapper=remap_ttn_statuses,
            trigger_status='9',
            target_status='returned_to_branch'))


async def handle_ukrpost_tracking(orders: list[dict]):
    ukrpost_data, ttn_mapper = await retrieve_ukr_post_data(
        dilovod_orders=orders,
        ttn_statuses={}
    )
    await ukrpost_client.ukrpost_status_mapper(
        ttn_mapper=ttn_mapper,
        ukrpost_data=ukrpost_data)
    # print('urk post data after mapping with shipments statuses:', ttn_mapper)
    # await shipment_processor.handle_delivery_update(
        # ttn_mapper=ttn_mapper,
        # trigger_status='41000',
        # target_status='returned_to_branch'
    # )


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
