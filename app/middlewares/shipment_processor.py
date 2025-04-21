from typing import Literal
from collections import defaultdict

from app.middlewares.dilovod_client.dilovod_query_builder import (
    DilovodQueryBuilder as DQBuilder,)
from app.middlewares.dilovod_client.dilovod_statistics_middleware import (
    DilovodStatisticsMiddleware as DStatistics
)
from app.middlewares.dilovod_client.dilovod_client import DilovodClient


class ShipmentProcessor:

    def __init__(self):
        self.__dilovod_qb = DQBuilder()
        self.__dilovod_stat = DStatistics()
        self.__dilovod_client = DilovodClient(
            dilovod_statistics=self.__dilovod_stat)

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
        for dilovod_id, shipment_data in ttn_mapper:
            shipment_status: str = shipment_data.get(
                'shipment_status')
            if shipment_status == target_status:
                dilovod_id_in_status.append(dilovod_id)
