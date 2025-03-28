from app.config.config_parser import ConfigParser
from app.middlewares.logger.loguru_logger import LoguruLogger
from app.middlewares.http_client.http_client import HTTPClient
from app.middlewares.http_client.request_error import RequestError
from app.middlewares.novapost_client.novapost_query_builder import NovaPostQueryBuilder


class NovaPostClient:
    def __init__(self):
        self.__config: ConfigParser = ConfigParser()
        self.__loguru_logger: LoguruLogger = LoguruLogger()
        self.__logger = self.__loguru_logger.logger
        self.__http_client: HTTPClient = HTTPClient()
        self.__novapost_query_builder: NovaPostQueryBuilder = NovaPostQueryBuilder()

    async def check_ttn_status(self, dilovod_orders: list[dict]):
        try:
            novapost_requests: list[dict] = await self.__novapost_query_builder.prepare_request(
                dilovod_orders=dilovod_orders
            )
        except ValueError as e:
            self.__logger(f'Error occured while ttn retviring: {e}')
            return None
        novapost_reponses: list[dict] = []
        for request in novapost_requests:
            try:
                response: dict = await self.__http_client.post(
                    url=self.__config.novapost_url,
                    payload=request,
                    parse_mode='json'
                )
                novapost_reponses.append(response)
            except RequestError as e:
                self.__logger.error(f'''NovaPost API http error occured
                                    while getting ttn`s
                                    status code: {e.status_code}
                                    error message: {e.message}''')
                continue
