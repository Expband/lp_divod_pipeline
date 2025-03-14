from app.config.config_parser import ConfigParser


class DilovodQueryBuilder:
    def __init__(self):
        self.__config_parser: ConfigParser = ConfigParser()

    async def configure_payload(self,
                                action: str,
                                fields: dict = None,
                                params: dict = None,
                                document: str = None,
                                filters_list: list[dict] = None) -> dict:
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

    async def get_data_to_shipment(self, dilovod_object: dict, saveType: int) -> dict:
        request_body: dict = await self.configure_payload(action='saveObject')
        tableParts_raw: dict = dilovod_object['tableParts']
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
                'priceAmount': good_object_raw['priceAmount'],
                'amountCur': good_object_raw['amountCur'],
                'accGood': good_object_raw['accGood'],
                'qty': good_object_raw['qty'],
                'unit': good_object_raw['unit'],
                'vatAmount': good_object_raw['vatAmount'],
                'printName': good_object_raw['printName']
            }
            request_body['params']['tableParts']['tpGoods'][f'{good}'] = good_object
        header_raw: dict = dilovod_object['header']
        header: dict = {
            'id': 'documents.sale',
            'date': header_raw['date'],
            'baseDoc': header_raw['id']['id'],
            'contract': header_raw['id']['id'],
            'firm': header_raw['firm']['id'],
            'person': header_raw['person']['id'],
            'docMode': '1004000000000350',
            'currency': '1101200000001001',
            'remark': header_raw['remark']
        }
        delivery_method: str = header_raw['deliveryMethod_forDel']['pr']
        storage_id: str = ''
        if delivery_method == 'Укр пошта':
            storage_id = '1100100000001003'
        if delivery_method == 'Нова пошта':
            storage_id = '1100100000001002'
        header['storage'] = storage_id
        request_body['params'].setdefault('header', {})
        request_body['params']['header'] = header
        return request_body

    async def get_data_to_cashIn(self, dilovod_object: dict, shipment_id: str, saveType: int = 1):
        request_body: dict = await self.configure_payload(action='saveObject')
        request_body['params'] = {}
        request_body['params']['saveType'] = saveType
        request_body['params'].setdefault('tableParts', {})
        request_body['params']['tableParts'].setdefault('tpAnalytics', [])
        header_raw: dict = dilovod_object['header']
        good_object: dict = {
            'rowNum': "1",
            'analytics1': header_raw['id'],
            "analytics2": 0,
            "analytics3": 0,
            "amountCur": header_raw['amountCur'],
            "vatTax": "1105800000000023",
            "vatAmount": 98.33,
            "amountCurExchange": 0,
            "amountCurCommission": 0,
            "exchangeRate": 0,
            "cashGoal": 0
        }
        request_body['params']['tableParts']['tpAnalytics'].append(good_object)
        header: dict = {
            'id': 'documents.cashIn',
            'date': header_raw['date'],
            'remark': header_raw['remark'],
            'baseDoc': shipment_id,
            'firm': header_raw['firm']['id'],
            'person': header_raw['person']['id'],
            'currency': '1101200000001001',
            'cashItem': '1104300000001022',
            'department': '1101900000000001',
            'rate': 1,
            'business': '1115000000000001',
            "corAccount": "1119000000001079",
            "account": "1119000000001023",
            "appendix": "",
            "settlementsKind": "1103300000000001",
            "refund": 0,
            "content": "",
            "contract_forDel": 0,
            "amountCur": header_raw['amountCur'],
            "operType_forDel": 0,
            "tax_forDel": 0,
            "orderNumber": 0,
            "loan_forDel": 0,
            "taxAccount": 0,
            "paymentID": "",
            "posted": True,
            "currencyExchange": 0,
            "amountCurCommission": 0,
            "exchangeRate_forDel": 0
        }
        delivery_method: str = header_raw['deliveryMethod_forDel']['pr']
        cashAccount: str = ''
        if delivery_method == 'Укр пошта':
            cashAccount = '1101100000001052'
        elif delivery_method == 'Нова пошта':
            cashAccount = '1101100000001053'
        header['cashAccount'] = cashAccount
        request_body['params'].setdefault('header', {})
        request_body['params']['header'] = header
        return request_body
