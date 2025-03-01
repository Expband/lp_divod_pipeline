from app.middlewares.http_client.http_client import HTTPClient
from app.middlewares.logger.loguru_logger import LoguruLogger
from app.config.config_parser import ConfigParser


class DilovodClient:
    def __init__(self):
        self.__http_client = HTTPClient()
        self.__logger = LoguruLogger().logger
        self.__config_parser = ConfigParser()

    async def configure_payload(self, action: str, document: str, fields: dict, filters_list: list[dict] = None) -> dict:
        base_request: dict = {
            "version": "0.25",
            "key": self.__config_parser.dilovod_api_key,
            "action": action,
            "params": {
                "from": document,
                "fields": fields
            }
        }
        if filters_list:
            base_request['params']['filters'] = filters_list
        return base_request

    async def get_oreder_by_crm_id(self, crm_id: str):
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
        request_body: dict = await self.configure_payload(
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
