import pytz
from collections import defaultdict
from typing import Any
from datetime import datetime


from app.middlewares.logger.loguru_logger import LoguruLogger
from app.middlewares.dilovod_client.dilovod_client import DilovodClient
from app.middlewares.dilovod_client.dilovod_statistics_middleware import DilovodStatisticsMiddleware
from app.middlewares.novapost_client.novapost_client import NovaPostClient
from app.middlewares.novapost_client.novapost_query_builder import NovaPostQueryBuilder
from app.middlewares.ukrpost_client.urkpost_client import UkrpostClient


kyiv_tz = pytz.timezone("Europe/Kiev")
logger = LoguruLogger().logger
dilovod_statistics: DilovodStatisticsMiddleware = DilovodStatisticsMiddleware()
dilovod_client: DilovodClient = DilovodClient(
    dilovod_statistics=dilovod_statistics)
ukrpost_client: UkrpostClient = UkrpostClient()
novapost_client: NovaPostClient = NovaPostClient()
novapost_qb: NovaPostQueryBuilder = NovaPostQueryBuilder()


async def mail_tracking():
    date: str = datetime.now(tz=kyiv_tz).strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f'''Mail tracking job started at {date}''')
    refund_on_the_road: dict = await dilovod_client.get_orders_in_status(
        status='refund_on_the_road')
    returned_to_branch: dict = await dilovod_client.get_orders_in_status(
        status='returned_to_branch'
    )
    if refund_on_the_road:
        sorted_orders_on_road: dict = await sort_orders_by_delivery(
            dilovod_orders=refund_on_the_road)
        await process_sorted_orders(sorted_orders=sorted_orders_on_road)
    else:
        logger.info('No mails in "on the road" state')
    if returned_to_branch:
        sorted_orders_on_branch: dict = await sort_orders_by_delivery(
            dilovod_orders=returned_to_branch)
    else:
        logger.info('No mails in "on branch" state')


async def process_sorted_orders(sorted_orders: dict[str, list[dict]]):
    ttn_statuses: dict = {}
    for delivery_method, orders in sorted_orders.items():
        if delivery_method == '1110400000001001':
            resp = await track_novapost(ttn_statuses=ttn_statuses, dilovod_orders=orders)
        if delivery_method == '1110400000001002':
            resp = await track_ukr_post(ttn_statuses=ttn_statuses, dilovod_orders=orders)
    print('ttn statuses: ', ttn_statuses)


async def sort_orders_by_delivery(dilovod_orders: list[dict]):
    sorted_orders = defaultdict(list)
    for order in dilovod_orders:
        delivery_method: str = order['header']['deliveryMethod_forDel']['id']
        sorted_orders[delivery_method].append(order)
    return dict(sorted_orders)


async def track_novapost(ttn_statuses: dict, dilovod_orders: list[dict]):
    try:
        np_responses: list[dict] = await novapost_client.check_bunch_ttn_statuses(
            dilovod_orders=dilovod_orders,
            ttn_statuses=ttn_statuses
        )
        return np_responses
    except ValueError:
        logger.warning('0 TTN`s was found in "refund_on_the_road"')


async def track_ukr_post(dilovod_orders: list[dict], ttn_statuses: dict):
    try:
        request_chunked: list[dict] = await ukrpost_client.check_bunch_ttn_statuses(
            ttn_mapper=ttn_statuses,
            dilovod_orders=dilovod_orders
        )
    except ValueError:
        logger.warning('0 TTN`s was found in "refund_on_the_road"')
    print(request_chunked)
