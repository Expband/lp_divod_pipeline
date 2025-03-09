import asyncio

from app.middlewares.dilovod_client.dilovod_query_builder import DilovodQueryBuilder
from app.middlewares.http_client.http_client import HTTPClient
from app.middlewares.logger.loguru_logger import LoguruLogger
from app.config.config_parser import ConfigParser


class DilovodClient:
    _semaphore = asyncio.Semaphore(1)

    def __init__(self):
        self.__http_client: HTTPClient = HTTPClient()
        self.__dilovod_query_builder: DilovodQueryBuilder = DilovodQueryBuilder()
        self.__logger = LoguruLogger().logger
        self.__config_parser: ConfigParser = ConfigParser()

    async def _limited_post(self, url: str, payload: dict):
        async with self._semaphore:
            response = await self.__http_client.post(
                url=url,
                payload=payload,
                parse_mode='json')
            await asyncio.sleep(1)
            return response

    async def get_oreder_id_by_crm_id(self, crm_id: str):
        fields: dict = {"id": "id", "remark": "remark"}
        filters_list: list[dict] = [
            {
                "alias": "remark",
                "operator": "%",
                "value": crm_id}
            ]

        request_body: dict = await self.__dilovod_query_builder.configure_payload(
            action="request",
            document="documents.saleOrder",
            fields=fields,
            filters_list=filters_list
        )

        response = await self._limited_post(
            self.__config_parser.dilovod_api_url,
            request_body)
        response_data = response.json()

        if response_data:
            if response_data:
                return response_data
            else:
                self.__logger.error(
                    f'No records with LP CRM "order_id": {crm_id}')
                return None
        else:
            self.__logger.error(
                f'Unable to get Dilovod response for "order_id": {crm_id}')
            return None

    async def get_dilovod_order(self, dilovod_id: str) -> dict:
        params: dict = {
            'id': dilovod_id
            }
        request_body: dict = await self.__dilovod_query_builder.configure_payload(
            action='getObject',
            params=params)

        response = await self._limited_post(
            self.__config_parser.dilovod_api_url,
            request_body)
        response_data: dict = response.json()

        if response_data:
            if response_data.get('error'):
                self.__logger.error(
                    f'''Error occurred while getting dilovod order\n
                    DILOVOD ID: {dilovod_id}''')
                return None
            return response_data
        else:
            self.__logger.error(
                f'''Unable to get dilovod order object\n
                DILOVOD ID: {dilovod_id}''')
            return None

    async def make_move(self, dilovod_response: dict) -> None:
        dilovod_move_body = await self.__dilovod_query_builder.get_data_to_move(
            dilovod_response,
            saveType=1)

        response = await self._limited_post(
            self.__config_parser.dilovod_api_url,
            dilovod_move_body)
        response_data = response.json()

        if response_data.get('error'):
            self.__logger.info(
                f'''Unable to register document\n
                DILOVOD ID: {dilovod_response["header"]["id"]}\n
                Will store unregistered\nResponse: {response_data}'''
            )
            dilovod_move_body = await self.__dilovod_query_builder.get_data_to_move(
                dilovod_response,
                saveType=0)
            await self._limited_post(
                self.__config_parser.dilovod_api_url,
                dilovod_move_body)

    async def make_shipment(self, dilovod_response: dict) -> str | None:
        dilovod_shipment_body: dict = await self.__dilovod_query_builder.get_data_to_shipment(
            dilovod_response,
            saveType=1)

        response = await self._limited_post(
            self.__config_parser.dilovod_api_url,
            dilovod_shipment_body)
        response_data: dict = response.json()

        if response_data.get('error'):
            self.__logger.info(
                f'''Unable to register shipment\n
                DILOVOD ID: {dilovod_response["header"]["id"]}\n
                Will store unregistered\nResponse: {response_data}'''
            )
            dilovod_shipment_body = await self.__dilovod_query_builder.get_data_to_shipment(
                dilovod_response,
                saveType=0)
            response = await self._limited_post(
                self.__config_parser.dilovod_api_url,
                dilovod_shipment_body)

        return response_data.get('id')

    async def make_cashIn(self, dilovod_response: dict, shipment_id: str) -> None:
        dilovod_cashIn_body: dict = await self.__dilovod_query_builder.get_data_to_cashIn(
            dilovod_response,
            shipment_id)

        response = await self._limited_post(
            self.__config_parser.dilovod_api_url,
            dilovod_cashIn_body)
        response_data: dict = response.json()

        if response_data.get('error'):
            self.__logger.error(
                f'Error while processing cashIn: {response_data}')
