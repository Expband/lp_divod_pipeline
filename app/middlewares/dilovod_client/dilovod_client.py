from app.middlewares.http_client.http_client import HTTPClient
from app.middlewares.logger.loguru_logger import LoguruLogger
from app.config.config_parser import ConfigParser


class DilovodClient:
    def __init__(self):
        self.__http_client = HTTPClient()
        self.__logger = LoguruLogger().logger
        self.__config_parser = ConfigParser()

    async def configure_payload(self, action: str, fields: dict = None, params: dict = None, document: str = None, filters_list: list[dict] = None) -> dict:
        base_request: dict = {
            "version": "0.25",
            "key": self.__config_parser.dilovod_api_key,
            "action": action,
            "params": params
        }
        if action not in ['getObject', 'saveObject', 'setDelMark']:
            base_request['params'] = {
                "from": document,
                "fields": fields
                }
        if filters_list:
            base_request['params']['filters'] = filters_list
        return base_request

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

    async def get_dilovod_order(self, dilovod_id: str) -> dict:
        params: dict = {
            'id': dilovod_id
        }
        request_body: dict = await self.configure_payload(
            action='getObject',
            params=params
        )
        response = await self.__http_client.post(
            url=self.__config_parser.dilovod_api_url,
            payload=request_body,
            parse_mode='json'
        )
        response_data = response.json()
        if response_data:
            return response_data
        else:
            self.__logger.error(f'''Unable to get dilovod order object\n
                                dilovod id from "documents.saleOrders": {dilovod_id}''')
            return None

    async def make_move(self, dilovod_response: dict) -> None:
        dilovod_move_body = await self.get_data_to_move(
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
                            Will stored unregistred''')
            dilovod_move_body = await self.get_data_to_move(
                dilovod_response=dilovod_response,
                saveType=0
            )
            response = await self.__http_client.post(
                url=self.__config_parser.dilovod_api_url,
                payload=dilovod_move_body,
                parse_mode='json'
            )

    async def get_data_to_move(self, dilovod_response: dict, saveType: int) -> dict:
        request_body: dict = await self.configure_payload(action='saveObject')
        tableParts_raw: dict = dilovod_response['tableParts']
        tpGoods_raw: dict = tableParts_raw['tpGoods']
        goods_list: list[str] = tpGoods_raw.keys()
        request_body['params'] = {}
        request_body['params']['saveType'] = saveType
        request_body['params'].setdefault('tableParts', {})
        request_body['params']['tableParts'].setdefault('tpGoods', {})
        
        for good in goods_list:
            good_object_raw: dict = tpGoods_raw[good]
            good_object: dict = {
                'rowNum': good_object_raw['rowNum'],
                'good': good_object_raw['good'],
                'price': good_object_raw['price'],
                'qty': good_object_raw['qty'],
                'unit': good_object_raw['unit'],
                'vatAmount': good_object_raw['vatAmount'],
                'printName': good_object_raw['printName']
            }
            request_body['params']['tableParts']['tpGoods'][f'{good}'] = good_object
        header_raw: dict = dilovod_response['header']
        header: dict = {
            'id': 'documents.goodMoving',
            'date': header_raw['date'],
            'baseDoc': header_raw['id']['id'],
            'firm': header_raw['firm']['id'],
            'storage': '1100700000000001',
            'author': '1000200000001019',
            'business': '1115000000000001',
            'docMode': '1004000000000409',
            'priceType': '1101300000001001',
            'remark': header_raw['remark']
        }
        delivery_method: str = header_raw['deliveryMethod_forDel']['pr']
        storageTo_id: str = ''
        if delivery_method == 'Укр пошта':
            storageTo_id = '1100100000001003'
        if delivery_method == 'Нова пошта':
            storageTo_id = '1100100000001002'
        header['storageTo'] = storageTo_id
        request_body['params'].setdefault('header', {})
        request_body['params']['header'] = header
        return request_body
