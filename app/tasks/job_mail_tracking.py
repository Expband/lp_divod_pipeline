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
    # if returned_to_branch:
    #     sorted_orders_on_branch: dict = await sort_orders_by_delivery(
    #         dilovod_orders=returned_to_branch)
    #     await process_sorted_orders(sorted_orders=sorted_orders_on_branch)
    # else:
    #     logger.info('No mails in "on branch" state')


async def process_sorted_orders(sorted_orders: dict[str, list[dict]]):
    novapost_ttn_statuses: dict = {}
    ukrpost_ttn_statuses: dict = {}
    sum_of_shimpents: int = 0
    for delivery_method, orders in sorted_orders.items():
        if delivery_method == '1110400000001001':
            novapost_resps, novapost_ttn_statuses = await track_novapost(
                dilovod_orders=orders)
            novapost_ttn_statuses = await remap_if_new_ttn(
                np_responses=novapost_resps,
                ttn_statuses=novapost_ttn_statuses)
            new_ttns: list[str] = []
            for s_data in novapost_ttn_statuses.values():
                new_ttns.append(s_data['ttn_number'])
            np_ttn_chunked: list[str] = await novapost_qb.chunk_ttn_list(new_ttns, 99)
            np_request_body: list[dict] = await novapost_qb.fortam_shipment_doc(
                ttn_chunked_list=np_ttn_chunked
            )
            np_responses: list[dict] = await novapost_client.check_bunch_ttn_statuses(
                request_body_list=np_request_body)
            print(np_responses)
        if delivery_method == '1110400000001002':
            await track_ukr_post(ttn_statuses=ukrpost_ttn_statuses, dilovod_orders=orders)
    # if novapost_ttn_statuses:
    #     nova_shipments_in_statuse: list[str] = await get_shipment_in_status(
    #         ttn_statuses_store=novapost_ttn_statuses,
    #         criteria='9'
    #     )
    # if ukrpost_ttn_statuses:
    #     ukr_shipments_in_statuse: list[str] = await get_shipment_in_status(
    #         ttn_statuses_store=ukrpost_ttn_statuses,
    #         criteria='41'
    #     )
    # sum_of_shimpents: int = len(nova_shipments_in_statuse) + len(ukr_shipments_in_statuse)
    # print('sum_of_shimpents: ', sum_of_shimpents)
    # print('novapost ttn statuses: ', novapost_ttn_statuses)
    # print('ukrpost ttn statuses: ', ukrpost_ttn_statuses)


async def get_shipment_in_status(
        ttn_statuses_store: dict,
        criteria: str) -> list[str]:
    orders_by_criteria: list[str] = []
    for dilovod_id, order_info in ttn_statuses_store.items():
        order_statuse: str = order_info['status_id']
        if order_statuse == criteria:
            orders_by_criteria.append(dilovod_id)
    return orders_by_criteria


async def process_np_response(
        np_responses: list[dict],
        np_ttn_statuses: dict) -> dict:
    for response in np_responses:
        status = response.get('success')
        if not status:
            logger.error(f'''Malvared or unsuccessfull Novapost Response:
                        {response}''')
            continue
        shipments_data: list[dict] = response.get('data')
        for shipment in shipments_data:
            shipment_ttn: str = shipment.get('Number')
            shipment_status: str = shipment.get('StatusCode')
            if not shipment_ttn or not shipment_status:
                logger.error(f'''Malvared or unsuccessfull shipment object:
                        {shipment}''')


async def sort_orders_by_delivery(dilovod_orders: list[dict]):
    sorted_orders = defaultdict(list)
    for order in dilovod_orders:
        delivery_method: str = order['header']['deliveryMethod_forDel']['id']
        sorted_orders[delivery_method].append(order)
    return dict(sorted_orders)


async def track_novapost(dilovod_orders: list[dict]):
    np_request_body, ttn_statuses = await novapost_qb.prepare_request(
                dilovod_orders=dilovod_orders
            )
    try:
        np_responses: list[dict] = await novapost_client.check_bunch_ttn_statuses(
            request_body_list=np_request_body,
        )
        return np_responses, ttn_statuses
    except ValueError:
        logger.warning('0 TTN`s was found in "refund_on_the_road"')


async def remap_if_new_ttn(
        np_responses: list[dict],
        ttn_statuses: dict) -> dict:
    for np_resp in np_responses:
        success: str = np_resp.get('success')
        if not success:
            logger.error(f'''Unsuccess NovaPost response:
                        {np_resp}''')
            continue
        np_resp_data: list[dict] = np_resp.get('data')
        if not np_resp_data:
            logger.error(f'''Unable to get data from NovaPost response:
                        {np_resp}''')
            continue
        for shipment in np_resp_data:
            old_ttn = shipment.get('Number')
            new_ttn = shipment.get('LastCreatedOnTheBasisNumber')
            if new_ttn:
                dilovod_id: str = await find_key_by_ttn_number(
                    ttn=old_ttn,
                    data=ttn_statuses
                )
                ttn_statuses[dilovod_id]['ttn_number'] = new_ttn
    return ttn_statuses


async def find_key_by_ttn_number(ttn, data):
    for key, value in data.items():
        if value.get('ttn_number') == ttn:
            return key
    return None


async def track_ukr_post(dilovod_orders: list[dict], ttn_statuses: dict):
    try:
        request_chunked: list[dict] = await ukrpost_client.check_bunch_ttn_statuses(
            ttn_mapper=ttn_statuses,
            dilovod_orders=dilovod_orders
        )
    except ValueError:
        logger.warning('0 TTN`s was found in "refund_on_the_road"')
