from app.middlewares.http_client.http_client import HTTPClient
from app.middlewares.logger.loguru_logger import LoguruLogger
from app.config.config_parser import ConfigParser


class LpCrmClient:
    def __init__(self):
        self.__http_client = HTTPClient()
        self.__logger = LoguruLogger().logger
        self.__config_parser = ConfigParser()
        self.__output_api_key = self.__config_parser.lp_output_api_key
        self.__api_url = self.__config_parser.lp_api_url

    async def get_statuses(self) -> dict:
        payload: dict = {
            'key': self.__output_api_key
        }
        statuses: dict = await self.__http_client.post(
            url=self.__api_url+'/api/getStatuses.html',
            payload=payload,
            parse_mode='xml'
        )
        if statuses is None:
            self.__logger.error('Unable to retrive data from LP CRM')
            return None
        else:
            return statuses.json()

    async def get_status_and_id(self, status: str) -> str:
        statuses_data: dict = await self.get_statuses()
        if statuses_data is not None:
            statuses: dict = statuses_data['data']
            status_id: str = None
            for _id, crm_status in statuses.items():
                if crm_status == status:
                    status_id = _id
                    return status_id
            return status_id
        else:
            return None
