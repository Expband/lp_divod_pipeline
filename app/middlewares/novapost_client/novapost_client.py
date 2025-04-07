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

    async def check_bunch_ttn_statuses(self, dilovod_orders: list[dict]):
        try:
            novapost_requests, ttn_mapper = await self.__novapost_query_builder.prepare_request(
                dilovod_orders=dilovod_orders
            )
        except ValueError as e:
            self.__logger(f'Error occured while ttn retviring: {e}')
            return None
        novapost_reponses: list[dict] = []
        ttn_mapper_copy: dict = ttn_mapper.copy()
        for request in novapost_requests:
            try:
                response: dict = await self.__http_client.post(
                    url=self.__config.novapost_url,
                    payload=request,
                    parse_mode='json'
                )
                response_dict: dict = response.json()
                novapost_reponses.append(response_dict)
                if not response_dict:
                    self.__logger(f'''Malvared Novapost response.
                                    Response: {response}''')
                    continue
                await self.process_response(
                    ttn_mapper=ttn_mapper_copy,
                    response_dict=response_dict)
            except RequestError as e:
                self.__logger.error(f'''NovaPost API http error occured
                                    while getting ttn`s
                                    status code: {e.status_code}
                                    error message: {e.message}''')
                continue
        # print('novapost response: ', novapost_reponses)
        print('ttn mapper copy:', ttn_mapper_copy)
        return novapost_reponses

    async def novapost_status_mapper(
            self,
            ttn_mapper: dict[str],
            np_data: list[dict]) -> dict:

        shipment_number: str = np_data.get('Number')
        if shipment_number:
            shipment_status_code: str = np_data.get('StatusCode')
            if shipment_status_code:
                ttn_mapper[shipment_number]['status_id'] = shipment_status_code
            else:
                self.__logger.error(f'''Unable to get StatusCode
                                    for shipment.
                                    TTN number {shipment_number}''')
                return None
        else:
            self.__logger.warning(f'''Unable to get TTN for
                                    some of mentioned.
                                    Novapost response: {np_data}''')
            return None
        print('ttn mapper with status :', ttn_mapper)
        return ttn_mapper

    async def process_response(
            self,
            ttn_mapper: dict,
            response_dict: dict) -> dict:
        response_status: bool = response_dict.get('success')
        if not response_status:
            self.__logger.error(f'''Unsuccess response chunk.
                                Response chunk: {response_dict}''')
            return None
        mapper: dict = await self.novapost_status_mapper(
            ttn_mapper=ttn_mapper,
            np_data=response_dict)
        return mapper
