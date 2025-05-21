import datetime
import pytz
from typing import Literal, Any

from app.config.config_parser import ConfigParser


class DilovodQueryBuilder:
    def __init__(self):
        self.__config_parser: ConfigParser = ConfigParser()
        self.__kyiv_tz = pytz.timezone("Europe/Kiev")

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

    async def get_data_to_move(
            self,
            dilovod_response: dict,
            saveType: int,
            move_type: Literal[
                'from_sale',
                'from_movement'],
            date: str = None) -> dict:
        if not date:
            date: str = datetime.datetime.now(
                tz=self.__kyiv_tz).strftime("%Y-%m-%d %H:%M:%S")
        request_body: dict = await self.configure_payload(action='saveObject')
        tableParts_raw: dict = dilovod_response['tableParts']
        tpGoods_raw: dict = tableParts_raw['tpGoods']
        if not isinstance(tpGoods_raw, dict):
            return None
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
            table_parts: dict = request_body['params']['tableParts']
            table_parts['tpGoods'][f'{good}'] = good_object
        header_raw: dict = dilovod_response['header']
        header: dict = {
            'id': 'documents.goodMoving',
            'date': date,
            'baseDoc': header_raw['id']['id'],
            'firm': header_raw['firm']['id'],
            'author': '1000200000001019',
            'business': '1115000000000001',
            'docMode': '1004000000000409',
            'priceType': '1101300000001001',
            'remark': header_raw['remark']
        }
        storageTo_id: str = ''
        if move_type == 'from_sale':
            header['storage'] = '1100700000000001'
            delivery_method: str = (
                header_raw.get('deliveryMethod_forDel', {}).get('pr'))
            if delivery_method == 'Укр пошта':
                storageTo_id = '1100100000001003'
            if delivery_method == 'Нова пошта':
                storageTo_id = '1100100000001002'
        if move_type == 'from_movement':
            pervious_storage: str = header_raw['storageTo']['id']
            header['storage'] = pervious_storage
            if pervious_storage == '1100100000001002':
                storageTo_id = '1100100000058677'
            if pervious_storage == '1100100000001003':
                storageTo_id = '1100100000058678'
        header['storageTo'] = storageTo_id
        request_body['params'].setdefault('header', {})
        request_body['params']['header'] = header
        return request_body

    async def change_order_status(
            self,
            dilovod_id: str,
            status: Literal[
                'completed',
                'sent_to_post_office',
                'refund_on_the_road',
                'returned_to_branch',
                'utilization',
                'refund_taken',
                'error',
                ]) -> dict:
        status_mapper: dict = {
            'completed': '1111500000001002',
            'sent_to_post_office': '1111500000001003',
            'refund_on_the_road': '1111500000001004',
            'returned_to_branch': '1111500000001005',
            'utilization': '1111500000001006',
            'refund_taken': '1111500000001007',
            'error': '1111500000001008'
        }
        params: dict = {
            'saveType': 1,
            'header': {
                'id': dilovod_id,
                'state': status_mapper[status]
            }
        }
        base_request: dict = await self.configure_payload(
            action='saveObject',
            params=params
            )
        return base_request

    async def get_data_to_shipment(
            self,
            dilovod_object: dict,
            saveType: int,
            date: str = None) -> dict:
        if not date:
            date: str = datetime.datetime.now(
                tz=self.__kyiv_tz).strftime("%Y-%m-%d %H:%M:%S")
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
            table_parts: dict = request_body['params']['tableParts']
            table_parts['tpGoods'][f'{good}'] = good_object
        header_raw: dict = dilovod_object['header']
        header: dict = {
            'id': 'documents.sale',
            'date': date,
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

    async def get_data_to_cashIn(
            self,
            dilovod_object: dict,
            shipment_id: str,
            saveType: int = 1,
            date: str = None):
        if not date:
            date: str = datetime.datetime.now(
                tz=self.__kyiv_tz).strftime("%Y-%m-%d %H:%M:%S")
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
            'date': date,
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

    async def get_data_to_mass_move(
            self,
            dilovod_orders: list[dict],
            from_storage: Literal[
                'Novapost',
                'Ukrpost'
                ],
            save_type: int = 0) -> dict:
        request_body: dict = await self.configure_payload(action='saveObject')
        date: str = datetime.datetime.now(
                tz=self.__kyiv_tz).strftime("%Y-%m-%d %H:%M:%S")
        request_body['params'] = {}
        request_body['params']['saveType'] = save_type
        request_body['params'].setdefault('tableParts', {})
        request_body['params']['tableParts'].setdefault('tpGoods', {})
        header: dict = {
            'id': 'documents.goodMoving',
            'date': date,
            'firm': dilovod_orders[0]['header']['firm']['id'],
            'author': '1000200000001019',
            'business': '1115000000000001',
            'docMode': '1004000000000409',
            'priceType': '1101300000001001',
            "storage": "1100100000001002"
        }
        if from_storage == 'Novapost':
            header['storageTo'] = '1100700000000001'
        if from_storage == 'Ukrpost':
            header['storageTo'] = '1100700000000002'
        remark: str =  await self.handle_orders(
            dilovod_orders=dilovod_orders,
            raw_dilovod_request_body=request_body
        )
        header['remark'] = remark
        request_body['params']['header'] = header
        return request_body
        # for order in dilovod_orders:
        #     tp_goods: dict = order.get('tableParts').get('tpGoods')
        #     for good_data in tp_goods.values():
        #         body_goods: dict = (
        #             request_body['params']['tableParts']['tpGoods'])
        #         good_id: str = good_data.get('good')
        #         is_exist: bool = any(
        #             bg.get("good") == good_id
        #             for bg in body_goods.values())
        #         if is_exist:
        #             for good in tp_goods:
        #                 if good['good'] == good_id:
        #                     pass
        #                 else:
        #                     pass

    async def extract_tp_goods(
            self,
            object: dict[str, Any]) -> dict:
        return object.get('tableParts', {}).get('tpGoods', {})

    async def extract_body_goods(
            self,
            request_body: dict[str, Any]) -> dict:
        return request_body.get(
            'params', {}).get('tableParts', {}).get('tpGoods', {})

    async def good_exists_in_body(
            self,
            body_goods: dict[str, Any],
            good_id: str) -> bool:
        return any(g.get("good") == good_id for g in body_goods.values())

    async def process_goods_if_exist(
            self,
            tp_goods: dict[str, Any],
            good_id: str,
            increase_qty: float) -> None:
        tp_goods_copy: dict = tp_goods.copy()
        for _good_id, good in tp_goods_copy.items():
            if not isinstance(good, dict):
                print(f'''Good: {good}
                        Good is not dict''')
                continue
            if good['good'] == good_id:
                raw_base_qty: str = tp_goods[f'{_good_id}']['baseQty']
                raw_qty: str = tp_goods[f'{_good_id}']['qty']
                if not raw_base_qty:
                    raw_base_qty: float = 0.0
                if not raw_qty:
                    raw_qty: float = 0.0
                qty: float = float(raw_qty)
                tp_goods[f'{_good_id}']['qty'] = str(
                    qty + increase_qty)
        return tp_goods

    async def transform_goods_data(self, raw_goods: dict) -> dict:
        fields_to_keep = ["rowNum", "good", "price", "qty", "unit"]
        transformed_data = {}
        for good_id, good_data in raw_goods.items():
            filtered_data = {}
            for field in fields_to_keep:
                if field in good_data:
                    filtered_data[field] = good_data[field]
            transformed_data[good_id] = filtered_data
        return transformed_data

    async def handle_orders(
            self,
            dilovod_orders: list[dict[str, Any]],
            raw_dilovod_request_body: dict[str, Any]) -> str:
        remark: str = ''
        for dilovod_order in dilovod_orders:
            raw_remark: str = dilovod_order.get('remark')
            if raw_remark:
                raw_remark: str = raw_remark.split(',')[-1].split(' ')[-1]
            else:
                raw_order_number: str = dilovod_order['header']['id']['pr']
                raw_remark: str = raw_order_number.split(' ')[-1]
            remark: str = remark + '|' + raw_remark
            tableParts: dict = dilovod_order.get(
                'tableParts', {})
            order_tp_goods: dict = tableParts.get('tpGoods', {})
            request_body_goods: dict = raw_dilovod_request_body.get(
                'params', {}).get('tableParts', {}).get('tpGoods', {})
            for good_id, good_data in order_tp_goods.items():
                good_id: str = good_data.get('good')
                is_exist: bool = await self.good_exists_in_body(
                        body_goods=request_body_goods,
                        good_id=good_id)
                if is_exist:
                    qty: str = good_data.get('qty')
                    await self.process_goods_if_exist(
                        tp_goods=request_body_goods,
                        good_id=good_id,
                        increase_qty=float(qty))
                else:
                    request_body_goods[good_id] = good_data
        return remark
