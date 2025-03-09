from app.middlewares.dilovod_client.dilovod_query_builder import DilovodQueryBuilder
from app.middlewares.http_client.http_client import HTTPClient
from app.middlewares.logger.loguru_logger import LoguruLogger, logger
from app.config.config_parser import ConfigParser


class DilovodClient:
    def __init__(self):
        self.__http_client: HTTPClient = HTTPClient()
        self.__dilovod_query_builder: DilovodQueryBuilder = DilovodQueryBuilder()
        self.__logger = LoguruLogger().logger
        self.__config_parser: ConfigParser = ConfigParser()

    async def get_oreder_id_by_crm_id(self, crm_id: str):
        fields: dict = {
            "id": "id",
            "remark": "remark"
        }
        filters_list: list[dict] = [
            {
                "alias": "remark",
                "operator": "%",
                "value": crm_id
            }
        ]
        request_body: dict = await self.__dilovod_query_builder.configure_payload(
            action="request",
            document="documents.saleOrder",
            fields=fields,
            filters_list=filters_list
        )
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
                self.__logger.error(f'No records with LP CRM "order_id": {crm_id}')
                return None
        else:
            self.__logger.error(f'Unable to get Dilovod response for "order_id": {crm_id}')
            return None

    async def get_dilovod_order(self, dilovod_id: str) -> dict:
        params: dict = {
            'id': dilovod_id
        }
        request_body: dict = await self.__dilovod_query_builder.configure_payload(
            action='getObject',
            params=params
        )
        response = await self.__http_client.post(
            url=self.__config_parser.dilovod_api_url,
            payload=request_body,
            parse_mode='json'
        )
        response_data: dict = response.json()
        if response_data:
            error = response_data.get('error')
            if error:
                self.__logger(f'''Error occured while getting dilovod order\n
                                dilovod "id": {dilovod_id}''')
                return None
            else:
                return response_data
        else:
            self.__logger.error(f'''Unable to get dilovod order object\n
                                dilovod id from "documents.saleOrders": {dilovod_id}''')
            return None

    async def make_move(self, dilovod_response: dict) -> None:
        dilovod_move_body = await self.__dilovod_query_builder.get_data_to_move(
            dilovod_response=dilovod_response,
            saveType=1
        )
        response = await self.__http_client.post(
            url=self.__config_parser.dilovod_api_url,
            payload=dilovod_move_body,
            parse_mode='json'
        )
        response_data = response.json()
        error: str | None = response_data.get('error')
        if error:
            self.__logger.info(f'''Unable to register document\n
                            dilovod id: {dilovod_response['header']['id']}\n
                            Will stored unregistred\n
                            Response: {response_data}''')
            dilovod_move_body = await self.__dilovod_query_builder.get_data_to_move(
                dilovod_response=dilovod_response,
                saveType=0
            )
            response = await self.__http_client.post(
                url=self.__config_parser.dilovod_api_url,
                payload=dilovod_move_body,
                parse_mode='json'
            )

    async def make_shipment(self, dilovod_response: dict) -> None:
        dilovod_shipment_body: dict = await self.__dilovod_query_builder.get_data_to_shipment(
            dilovod_object=dilovod_response,
            saveType=1)
        response = await self.__http_client.post(
            url=self.__config_parser.dilovod_api_url,
            payload=dilovod_shipment_body,
            parse_mode='json'
        )
        response_data: dict = response.json()
        error: str | None = response_data.get('error')
        if error:
            self.__logger.info(f'''Unable to register document\n
                            dilovod id: {dilovod_response['header']['id']}\n
                            Will stored unregistred\n
                            Response: {response_data}''')
            dilovod_shipment_body = await self.__dilovod_query_builder.get_data_to_shipment(
                dilovod_response=dilovod_response,
                saveType=0
            )
            response = await self.__http_client.post(
                url=self.__config_parser.dilovod_api_url,
                payload=dilovod_shipment_body,
                parse_mode='json'
            )
            shipment_id: str = response_data.get('id')
            return shipment_id
        shipment_id: str = response_data.get('id')
        return shipment_id

    async def make_cashIn(self, dilovod_response: dict, shipment_id: str) -> None:
        dilovod_cashIn_body: dict = await self.__dilovod_query_builder.get_data_to_cashIn(
            dilovod_object=dilovod_response,
            shipment_id=shipment_id
        )
        response = await self.__http_client.post(
            url=self.__config_parser.dilovod_api_url,
            payload=dilovod_cashIn_body,
            parse_mode='json'
        )
        response_data: dict = response.json()
        error: str | None = response_data.get('error')
        if error:
            print(response_data)
