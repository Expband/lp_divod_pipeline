from app.config.config_parser import ConfigParser
from app.middlewares.logger.loguru_logger import LoguruLogger


class NovaPostQueryBuilder:
    def __init__(self):
        self.__loguru_logger: LoguruLogger = LoguruLogger()
        self.__logger = self.__loguru_logger.logger
        self.__config: ConfigParser = ConfigParser()

    async def chunk_ttn_list(
            self,
            ttn: list[str],
            units_per_chunl: int
            ) -> list[str]:
        result: list[str] = []
        for i in range(0, len(ttn), units_per_chunl):
            chunk = ttn[i:i + units_per_chunl]
            result.append(chunk)
        return result

    async def prepare_request(
            self,
            dilovod_orders: list[dict] ) -> list[list[dict]]:
        ttn_numbers: list[str] = []
        ttn_dilovod_id_mapper: dict = {}
        for order in dilovod_orders:
            order_id: str = order['header']['id']['id']
            ttn_number: str | None = order['header']['deliveryRemark_forDel']
            if not ttn_number:
                self.__logger.error(f'''
                                    Unable to get TTN "dilovod_id": {order_id}
                                    Order will be skiped
                                    Dilovod order: {order}''')
                continue
            ttn_dilovod_id_mapper[ttn_number] = {'dilovod_id': order_id}
            ttn_numbers.append(ttn_number)
        if not ttn_numbers:
            raise ValueError('None TTN found. Unable to continue process')
        ttn_chunked_list: list[str] = await self.chunk_ttn_list(
            ttn=ttn_numbers,
            units_per_chunl=99
        )
        requests_body_list: list[dict] = []
        for chunk in ttn_chunked_list:
            documents_list_chunked: list[dict] = []
            for ttn in chunk:
                document: dict = {
                    'DocumentNumber': ttn
                }
                documents_list_chunked.append(document)
            base_request: dict = {
                'apiKey': self.__config.novapost_api_key,
                'modelName': 'TrackingDocumentGeneral',
                'calledMethod': 'getStatusDocuments',
                'methodProperties': {
                    'Documents': documents_list_chunked
                }
            }
            requests_body_list.append(base_request)
        return requests_body_list, ttn_dilovod_id_mapper
