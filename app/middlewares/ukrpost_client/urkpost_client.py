from app.config.config_parser import ConfigParser
from app.middlewares.http_client.http_client import HTTPClient
from app.middlewares.logger.loguru_logger import LoguruLogger


class UkrpostClient:
    def __init__(self):
        self.__config = ConfigParser()
        self.__logger = LoguruLogger().logger
        self.__url: str = self.__config.ukrpost_url
        self.__api_key: str = self.__config.ukrpost_api_key
        self.__http_client = HTTPClient()

    async def check_bunch_ttn_statuses(
            self,
            dilovod_orders: list[dict],
            ttn_mapper: dict):
        api_endpoint: str = '/status-tracking/0.0.1/statuses/last/with-not-found'
        barcodes: list[str] = []
        for order in dilovod_orders:
            order_id: str = order['header']['id']['id']
            ttn_number: str = order['header']['deliveryRemark_forDel']
            if not ttn_number:
                self.__logger.error(f'''
                                    Unable to get TTN "dilovod_id": {order_id}
                                    Order will be skiped
                                    Dilovod order: {order}''')
                continue
            barcodes.append(ttn_number)
            ttn_mapper[ttn_number] = {'dilovod_id': order_id}
        request_url: str = self.__url + api_endpoint
        request_headers: dict = {
            'Authorization': 'Bearer ' + self.__api_key
        }
        response = await self.__http_client.post(
            url=request_url,
            headers=request_headers,
            payload=barcodes)
        print('response: ', response.json())
        barcodes_mapped = await self.ukrpost_status_mapper(
            ttn_mapper=ttn_mapper,
            ukrpost_data=response.json())
        if not barcodes_mapped:
            raise ValueError('No barcodes tracked')
        print('ttn_mapper: ', ttn_mapper)
        return response.json()

    async def ukrpost_status_mapper(self, ttn_mapper: dict, ukrpost_data: dict):
        found_data: dict = ukrpost_data.get('found')
        not_found_data: list[str] = ukrpost_data.get('notFound')
        if not found_data:
            self.__logger.error(f'''None of shipments wasn`t tracked.
                                Not found ttn`s: {not_found_data}''')
            return None
        for barcode, shipment in found_data.items():
            shipment_data: dict = shipment[0]
            status_id: str = shipment_data.get('event')
            ttn_mapper[barcode]['status_id'] = status_id
        return ttn_mapper
