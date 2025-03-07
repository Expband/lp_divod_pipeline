from app.middlewares.logger.loguru_logger import LoguruLogger
from app.middlewares.dilovod_client.dilovod_client import DilovodClient


class CrmPostbackService:
    def __init__(self, loger: LoguruLogger, dilovod_client: DilovodClient):
        self.__loger = loger.logger
        self.__dilovod_client = dilovod_client

    async def process_postback_request(self, postback: dict, action: str):
        order_id: str | None = postback.get('order_id')
        if not order_id:
            self.__loger.error(
                f'''Unable to get "order_id" of "status_id" field \n
                from postback request: \n
                "order_id": {order_id}''')
            return None
        dilovod_order_id_response = await self.__dilovod_client.get_oreder_id_by_crm_id(order_id)
        if not dilovod_order_id_response:
            self.__loger.error(f'''Unexpected error occured while getting Dilovod order id from CRM.\n
                                CRM "order_id": {order_id}''')
            return None
        try:
            dilovod_order_id = dilovod_order_id_response[0]['id']
        except Exception:
            self.__loger.error(f'''Unable to get dilovod order id\n
                                CRM order_id: {order_id}\n
                                Response: \n{dilovod_order_id_response}''')
            return None
        dilovod_order_object: dict = await self.__dilovod_client.get_dilovod_order(
            dilovod_id=dilovod_order_id)
        if action == 'move':
            await self.__dilovod_client.make_move(
                dilovod_response=dilovod_order_object)
        if action == 'shipment':
            shipment_id: str = await self.__dilovod_client.make_shipment(
                dilovod_response=dilovod_order_object
            )
            await self.__dilovod_client.make_cashIn(
                dilovod_response=dilovod_order_object,
                shipment_id=shipment_id
            )
