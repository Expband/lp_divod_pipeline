from app.config.config_parser import ConfigParser
from app.middlewares.http_client.http_client import HTTPClient


class UkrpostClient:
    def __init__(self):
        self.__config = ConfigParser()
        self.__url: str = self.__config.ukrpost_url
        self.__api_key: str = self.__config.ukrpost_api_key
        self.__http_client = HTTPClient()

    async def check_bunch_ttn_statuses(self, dilovod_orders: list[dict]):
        api_endpoint: str = '/status-tracking/0.0.1/statuses/last?barcode='
        ttn_dilovod_id_mapper: dict = {}
        for order in dilovod_orders:
            order_id: str = order['header']['id']['id']
            ttn_number: str = order['header']['deliveryRemark_forDel']
            if not ttn_number:
                self.__logger.error(f'''
                                    Unable to get TTN "dilovod_id": {order_id}
                                    Order will be skiped
                                    Dilovod order: {order}''')
                continue
            ttn_dilovod_id_mapper[ttn_number] = order_id
            request_url: str = self.__url + api_endpoint + ttn_number
            request_headers: dict = {
                'Authorization': 'Bearer' + self.__api_key
            }
            response = await self.__http_client.get(
                url=request_url,
                headers=request_headers)
            print(response)
