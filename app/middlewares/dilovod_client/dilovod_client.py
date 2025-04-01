from asyncio import Lock
from typing import Literal

from app.middlewares.dilovod_client.dilovod_query_builder import DilovodQueryBuilder
from app.middlewares.dilovod_client.dilovod_statistics_middleware import DilovodStatisticsMiddleware
from app.middlewares.http_client.http_client import HTTPClient
from app.middlewares.logger.loguru_logger import LoguruLogger
from app.config.config_parser import ConfigParser


class DilovodClient:
    def __init__(self, dilovod_statistics: DilovodStatisticsMiddleware):
        self.__dilovod_statistics: DilovodStatisticsMiddleware = dilovod_statistics
        self.__http_client: HTTPClient = HTTPClient()
        self.__dilovod_query_builder: DilovodQueryBuilder = DilovodQueryBuilder()
        self.__logger = LoguruLogger().logger
        self.__config_parser: ConfigParser = ConfigParser()
        self.__lock: Lock = Lock()

    async def get_object_id_by_crm_id(self, crm_id: str, order_id: str, document: str):
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
        request_body: dict = await self.__dilovod_query_builder.configure_payload(
            action="request",
            document=document,
            fields=fields,
            filters_list=filters_list
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
            self.__logger.error(f'Unable to get Dilovod response for "order_id": {crm_id}')
            return None

    async def get_dilovod_object_by_id(self, dilovod_id: str) -> dict:
        params: dict = {
            'id': dilovod_id
        }
        request_body: dict = await self.__dilovod_query_builder.configure_payload(
            action='getObject',
            params=params
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

    async def make_move(
            self,
            dilovod_response: dict,
            move_type: Literal[
                'from_sale',
                'from_movement']) -> None:
        dilovod_move_body = await self.__dilovod_query_builder.get_data_to_move(
            dilovod_response=dilovod_response,
            saveType=1,
            move_type=move_type
        )
        async with self.__lock:
            response = await self.__http_client.post(
                url=self.__config_parser.dilovod_api_url,
                payload=dilovod_move_body,
                parse_mode='json'
            )
        dilovod_order_id: str = dilovod_response['header']['id']['id']
        response_data = response.json()
        error: str | None = response_data.get('error')
        if error:
            self.__logger.info(f'''Unable to register document\n
                            dilovod id: {dilovod_order_id}\n
                            Will stored unregistred\n
                            Response: {response_data}''')
            dilovod_move_body['params']['saveType'] = 0
            async with self.__lock:
                response = await self.__http_client.post(
                    url=self.__config_parser.dilovod_api_url,
                    payload=dilovod_move_body,
                    parse_mode='json'
                )
            self.__dilovod_statistics.update_statistics(
                status='success',
                description='unregistred_docs'
            )
            await self.change_status(
                dilovod_order_id=dilovod_order_id,
                status='error')
            return
        await self.change_status(
            dilovod_order_id=dilovod_order_id,
            status='sent_to_post_office')
        self.__dilovod_statistics.update_statistics(
            status='success',
            description='registred_docs'
        )

    async def change_status(self,
                            dilovod_order_id: str,
                            status: Literal[
                                'completed',
                                'sent_to_post_office',
                                'refund_on_the_road',
                                'returned_to_branch',
                                'utilization',
                                'refund_taken',
                                'error',
                            ]):
        dilovod_change_status_body: dict = await self.__dilovod_query_builder.change_order_status(
            dilovod_id=dilovod_order_id,
            status=status
        )
        async with self.__lock:
            resp = await self.__http_client.post(
                url=self.__config_parser.dilovod_api_url,
                payload=dilovod_change_status_body,
                parse_mode='json'
            )
        print(resp.json())

    async def make_shipment(self, dilovod_response: dict) -> None:
        dilovod_order_id: str = dilovod_response['header']['id']['id']
        dilovod_shipment_body: dict = await self.__dilovod_query_builder.get_data_to_shipment(
            dilovod_object=dilovod_response,
            saveType=1)
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
            dilovod_shipment_body = await self.__dilovod_query_builder.get_data_to_shipment(
                dilovod_object=dilovod_response,
                saveType=0
            )
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
            return shipment_id
        await self.change_status(
            dilovod_order_id=dilovod_order_id,
            status='completed')
        self.__dilovod_statistics.update_statistics(
                status='success',
                description='registred_docs'
            )
        shipment_id: str = response_data.get('id')
        return shipment_id

    async def make_cashIn(self, dilovod_response: dict, shipment_id: str) -> None:
        dilovod_cashIn_body: dict = await self.__dilovod_query_builder.get_data_to_cashIn(
            dilovod_object=dilovod_response,
            shipment_id=shipment_id
        )
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
                                "dilovod_id": {dilovod_response['header']['id']['id']}\n
                                Response: {response_data}''')
            dilovod_cashIn_body: dict = await self.__dilovod_query_builder.get_data_to_cashIn(
                dilovod_object=dilovod_response,
                shipment_id=shipment_id,
                saveType=0
            )
