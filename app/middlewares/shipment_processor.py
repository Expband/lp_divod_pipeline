from typing import Literal
from collections import defaultdict

from app.middlewares.dilovod_client.dilovod_query_builder import (
    DilovodQueryBuilder as DQBuilder,)
from app.middlewares.dilovod_client.dilovod_statistics_middleware import (
    DilovodStatisticsMiddleware as DStatistics
)
from app.middlewares.logger.loguru_logger import LoguruLogger
from app.middlewares.dilovod_client.dilovod_client import DilovodClient
from app.middlewares.dilovod_client.dilovod_operator import DilovodOperator


class ShipmentProcessor:

    def __init__(self):
        self.__logger = LoguruLogger().logger
        self.__dilovod_qb = DQBuilder()
        self.__dilovod_stat = DStatistics()
        self.__dilovod_client = DilovodClient(
            dilovod_statistics=self.__dilovod_stat)
        self.__dilvood_operator = DilovodOperator()

    async def find_key_by_ttn_number(
            self,
            ttn: str,
            data: dict[str, dict[str, str]],
            key: Literal['ttn_number', 'new_ttn_number']) -> str | None:
        for outer_key, inner_dict in data.items():
            if inner_dict.get(key) == ttn:
                return outer_key
        return None

    async def sort_orders_by_delivery(
            self,
            dilovod_orders: list[dict]) -> None:
        sorted_orders = defaultdict(list)
        for order in dilovod_orders:
            delivery_method: str = (
                order['header']['deliveryMethod_forDel']['id'])
            sorted_orders[delivery_method].append(order)
        return dict(sorted_orders)

    async def handle_delivery_update(
            self,
            ttn_mapper: dict,
            trigger_status: str,
            target_status: Literal[
                    'completed', 'sent_to_post_office',
                    'refund_on_the_road', 'returned_to_branch',
                    'utilization', 'refund_taken', 'error']):
        for dilovod_id, shipment_data in ttn_mapper.items():
            status_id: str = shipment_data.get('shipment_status')
            new_ttn: str = shipment_data.get('new_ttn_number')
            if status_id == trigger_status:
                dilovod_request = await self.__dilovod_qb.change_order_status(
                    dilovod_id=dilovod_id,
                    status=target_status)
                if new_ttn:
                    header: dict = dilovod_request['params']['header']
                    header['deliveryRemark_forDel'] = new_ttn
                await self.__dilovod_client.change_status(
                    request_body=dilovod_request)

    async def get_in_status(
            self,
            ttn_mapper: dict,
            target_status: str) -> list[str]:
        dilovod_id_in_status: list['str'] = []
        for dilovod_id, shipment_data in ttn_mapper.items():
            shipment_status: str = shipment_data.get(
                'shipment_status')
            if shipment_status == target_status:
                dilovod_id_in_status.append(dilovod_id)
        return dilovod_id_in_status

    async def process_refunded_shipments(
            self,
            orders: list[dict],
            dilovod_id_in_status: list[str]):
        dilovod_orders_objects: list[dict] = await (
                self.__dilovod_client.select_orders_by_id_list(
                    dilovod_orders=orders,
                    dilovod_ids=dilovod_id_in_status
                )
            )
        request_body: dict = await self.__dilovod_qb.get_data_to_mass_move(
            dilovod_orders=dilovod_orders_objects,
            from_storage='Novapost'
        )
        if not request_body:
            self.__logger.error('Unable to get request body for mass move')
            return None
        tpGoods: dict = request_body['params']['tableParts']['tpGoods']
        formated_tpGoods: dict = await self.__dilovod_qb.transform_goods_data(
            raw_goods=tpGoods)
        request_body['params']['tableParts']['tpGoods'] = formated_tpGoods
        processed_orders_id: list[str] = await (
            self.__dilvood_operator.get_id_from_list_order(
                orders=orders))
        response: dict = await self.__dilovod_client.make_request(
            request_body=request_body
        )
        error: str = response.get('error')
        if error:
            self.__logger.error(f'''Error occured while mass movement:
                                {response}''')
        await self.__dilovod_client.list_orders_change_status(
            orders_ids=processed_orders_id,
            status='refund_taken'
        )
