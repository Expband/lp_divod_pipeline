from asyncio import Lock
from typing import Literal
from requests import Response

from app.middlewares.dilovod_client.dilovod_query_builder import (
    DilovodQueryBuilder as DQBuilder)
from app.middlewares.dilovod_client.dilovod_statistics_middleware import (
    DilovodStatisticsMiddleware as DSMiddleware)
from app.middlewares.http_client.http_client import HTTPClient
from app.middlewares.logger.loguru_logger import LoguruLogger
from app.config.config_parser import ConfigParser


class DilovodClient:
    def __init__(self, dilovod_statistics: DSMiddleware):
        self.__dilovod_statistics = dilovod_statistics
        self.__http_client: HTTPClient = HTTPClient()
        self.__dilovod_query_builder = DQBuilder()
        self.__logger = LoguruLogger().logger
        self.__config_parser: ConfigParser = ConfigParser()
        self.__lock: Lock = Lock()

    async def get_order_id_by_crm_id(
            self,
            crm_id: str,
            order_id: str,
            document: str):
        fields: dict = {
            "id": "id",
            "remark": "remark"
        }
        filters_list: list[dict] = [
            {
                "alias": "remark",
                "operator": "%",
                "value": crm_id
            },
            {
                "alias": "remark",
                "operator": "%",
                "value": order_id
            }
        ]
        request_body: dict = await (
            self.__dilovod_query_builder.configure_payload(
                action="request",
                document=document,
                fields=fields,
                filters_list=filters_list
                )
            )
        async with self.__lock:
            response = await self.__http_client.post(
                url=self.__config_parser.dilovod_api_url,
                payload=request_body,
                parse_mode='json'
            )
        response_data = response.json()
        if response_data:
            if len(response_data) != 0:
                return response_data
            else:
                self.__logger.error(f'''No records with
                                    LP CRM "order_id": {crm_id}''')
                return None
        else:
            self.__dilovod_statistics.update_statistics(
                status='unsuccess',
                description='error_not_found'
            )
            self.__logger.error(f'''Unable to get Dilovod
                                response for "order_id": {crm_id}''')
            return None

    async def make_request(self, request_body: dict) -> dict:
        async with self.__lock:
            response = await self.__http_client.post(
                url=self.__config_parser.dilovod_api_url,
                payload=request_body,
                parse_mode='json'
            )
        response_data = response.json()
        return response_data

    async def get_dilovod_object_by_id(self, dilovod_id: str) -> dict:
        params: dict = {
            'id': dilovod_id
        }
        request_body: dict = await (
            self.__dilovod_query_builder.configure_payload(
                action='getObject',
                params=params
                )
            )
        async with self.__lock:
            response = await self.__http_client.post(
                url=self.__config_parser.dilovod_api_url,
                payload=request_body,
                parse_mode='json'
            )
        response_data: dict = response.json()
        if response_data:
            error = response_data.get('error')
            if error:
                self.__logger.error(f'''Error occured while getting dilovod
                                    object\n
                                    dilovod "id": {dilovod_id}''')
                return None
            else:
                return response_data
        else:
            self.__logger.error(f'''Unable to get dilovod order object\n
                                dilovod id from "documents.saleOrders":
                                {dilovod_id}''')
            return None

    async def get_orders_in_status(self, status: Literal[
                                'completed',
                                'sent_to_post_office',
                                'refund_on_the_road',
                                'returned_to_branch',
                                'utilization',
                                'refund_taken',
                                'error',
                            ]):
        status_mapper: dict = {
            'completed': '1111500000001002',
            'sent_to_post_office': '1111500000001003',
            'refund_on_the_road': '1111500000001004',
            'returned_to_branch': '1111500000001005',
            'utilization': '1111500000001006',
            'refund_taken': '1111500000001007',
            'error': '1111500000001008'
        }
        fields: dict = {
            "id": "id",
            "remark": "remark",
            "name": "name",
            "state": "state"
        }
        filters: dict = {
            "alias": "state",
            "operator": "=",
            "value": status_mapper[status]
            }
        request_body: dict = await (
                self.__dilovod_query_builder.configure_payload(
                    fields=fields,
                    document='documents.saleOrder',
                    filters_list=[filters],
                    action='request')
                )
        async with self.__lock:
            response: Response = await self.__http_client.post(
                    url=self.__config_parser.dilovod_api_url,
                    payload=request_body,
                    parse_mode='json'
                )
        response: dict = response.json()
        if len(response) == 0:
            self.__logger.info(f'0 orders in status: {status}')
            return None
        order_objects: list[dict] = []
        if not isinstance(response, list):
            self.__logger.info(f'Unexpected dilovod response: {response}')
            return None
        for order in response:
            order_id: str = order['id']
            params: dict = {
                'id': order_id
            }
            get_object_payload: dict = await (
                self.__dilovod_query_builder.configure_payload(
                    action='getObject',
                    params=params)
                )
            order_object: dict = await self.request_handler(
                request_payload=get_object_payload)
            if order_object:
                order_objects.append(order_object)
            else:
                self.__logger.error(f'''Unable to get order
                                    from dilovod by "id": {order_id}''')
        return order_objects

    async def request_handler(self, request_payload: dict) -> str | bool:
        async with self.__lock:
            response: Response = await self.__http_client.post(
                url=self.__config_parser.dilovod_api_url,
                payload=request_payload,
                parse_mode='json'
            )
        response: dict = response.json()
        error: bool = await self.response_handler(response=response)
        if error:
            self.__logger.info(f'''Unsuccessfull request
                                Response: {response}''')
            return False
        else:
            self.__logger.info('Successfull request')
            return response

    async def response_handler(self, response: dict):
        error: dict | None = response.get('error')
        if error:
            return True
        return False

    async def make_move(
            self,
            dilovod_response: dict,
            move_type: Literal[
                'from_sale',
                'from_movement'],
            save_type: Literal[
                'registred',
                'unregistred'
                ]) -> bool:
        if save_type == 'registred':
            save_type = 1
        if save_type == 'unregistred':
            save_type = 0
        dilovod_move_body = await (
            self.__dilovod_query_builder.get_data_to_move(
                dilovod_response=dilovod_response,
                saveType=save_type,
                move_type=move_type
            ))
        if not dilovod_move_body:
            self.__logger.error(f'''Unable to configure "move" request body
                                for dilovod order. Dilovod order:
                                {dilovod_response}''')
            return False
        response: str | bool = await self.request_handler(
            request_payload=dilovod_move_body)
        if response:
            return response['id']
        else:
            return False

    async def change_status(self,
                            dilovod_order_id: str = None,
                            status: Literal[
                                'completed',
                                'sent_to_post_office',
                                'refund_on_the_road',
                                'returned_to_branch',
                                'utilization',
                                'refund_taken',
                                'error',
                            ] = None,
                            request_body: dict = None):
        if request_body:
            dilovod_change_status_body = request_body
        else:
            dilovod_change_status_body: dict = await (
                self.__dilovod_query_builder.change_order_status(
                    dilovod_id=dilovod_order_id,
                    status=status)
                )
        async with self.__lock:
            await self.__http_client.post(
                url=self.__config_parser.dilovod_api_url,
                payload=dilovod_change_status_body,
                parse_mode='json'
            )

    async def list_orders_change_status(
        self,
        orders_ids: list[str],
        status: Literal[
                                'completed',
                                'sent_to_post_office',
                                'refund_on_the_road',
                                'returned_to_branch',
                                'utilization',
                                'refund_taken',
                                'error',
                            ]):
        for order_id in orders_ids:
            await self.change_status(
                dilovod_order_id=order_id,
                status=status
            )

    async def make_shipment(self, dilovod_response: dict) -> None:
        dilovod_order_id: str = dilovod_response['header']['id']['id']
        dilovod_shipment_body: dict = await (
            self.__dilovod_query_builder.get_data_to_shipment(
                dilovod_object=dilovod_response,
                saveType=1)
            )
        async with self.__lock:
            response = await self.__http_client.post(
                url=self.__config_parser.dilovod_api_url,
                payload=dilovod_shipment_body,
                parse_mode='json'
            )
        response_data: dict = response.json()
        error: str | None = response_data.get('error')
        if error:
            self.__logger.info(f'''Unable to register document\n
                            dilovod id: {dilovod_order_id}\n
                            Will stored unregistred\n
                            Response: {response_data}''')
            dilovod_shipment_body = await (
                self.__dilovod_query_builder.get_data_to_shipment(
                    dilovod_object=dilovod_response,
                    saveType=0))
            async with self.__lock:
                response = await self.__http_client.post(
                    url=self.__config_parser.dilovod_api_url,
                    payload=dilovod_shipment_body,
                    parse_mode='json'
                )
            shipment_id: str = response_data.get('id')
            self.__dilovod_statistics.update_statistics(
                status='success',
                description='unregistred_docs'
            )
            await self.change_status(
                dilovod_order_id=dilovod_order_id,
                status='error')
            if not shipment_id:
                self.__logger.error(f'''Shipmen wasn`t created
                                    "dilovod_order_id": {dilovod_order_id}''')
                return None
            await self.change_status(
                dilovod_order_id=shipment_id,
                status='error'
            )
            return shipment_id
        await self.change_status(
            dilovod_order_id=dilovod_order_id,
            status='completed')
        await self.change_status(
            dilovod_order_id=response_data['id'],
            status='completed'
        )
        self.__dilovod_statistics.update_statistics(
                status='success',
                description='registred_docs'
            )
        shipment_id: str = response_data.get('id')
        return shipment_id

    async def make_cashIn(
            self,
            dilovod_response: dict,
            shipment_id: str) -> None:
        dilovod_cashIn_body: dict = await (
            self.__dilovod_query_builder.get_data_to_cashIn(
                dilovod_object=dilovod_response,
                shipment_id=shipment_id))
        async with self.__lock:
            response = await self.__http_client.post(
                url=self.__config_parser.dilovod_api_url,
                payload=dilovod_cashIn_body,
                parse_mode='json'
            )
        response_data: dict = response.json()
        error: str | None = response_data.get('error')
        if error:
            self.__logger.error(f'''Unable to registher "cashIn for" for
                                "dilovod_id":
                                {dilovod_response['header']['id']['id']}\n
                                Response: {response_data}''')
            dilovod_cashIn_body: dict = await (
                self.__dilovod_query_builder.get_data_to_cashIn(
                    dilovod_object=dilovod_response,
                    shipment_id=shipment_id,
                    saveType=0))

    async def select_orders_by_id_list(
            self,
            dilovod_orders: list[dict],
            dilovod_ids: list[str]) -> list[dict]:
        selected_orders: list[dict] = []
        print('dilovod orders: ', dilovod_orders)
        print('type dilovod orders: ', type(dilovod_orders))
        print('dilovod ids: ', dilovod_ids)
        print('type dilovod ids: ', type(dilovod_ids))
        for order in dilovod_orders:
            order_id: str = order['header']['id']['id']
            if order_id in dilovod_ids:
                selected_orders.append(order)
        return selected_orders
