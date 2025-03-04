from app.middlewares.logger.loguru_logger import LoguruLogger
from app.middlewares.lp_crm_client.lp_crm_client import LpCrmClient
from app.middlewares.dilovod_client.dilovod_client import DilovodClient


class CrmPostbackService:
    def __init__(self):
        self.__loger = LoguruLogger().logger
        self.__crm_client = LpCrmClient()
        self.__dilovod_client = DilovodClient()

    async def process_postback_request(self, postback: dict):
        order_id: str | None = postback.get('order_id')
        status_id: str | None = postback.get('status')
        if order_id is None or status_id is None:
            self.__loger.error(
                f'''Unable to get "order_id" of "status_id" field \n
                from postback request: \n
                "order_id": {order_id} \n
                "status_id: {status_id}"''')
            return None
        dilovod_order_id_response = await self.__dilovod_client.get_oreder_id_by_crm_id(order_id)
        if dilovod_order_id_response is None:
            self.__loger.error(f'''Unexpected error occured while getting Dilovod order id from CRM.\n
                                CRM "order_id": {order_id}''')
            return None
        try:
            dilovod_order_id = dilovod_order_id_response[0]['id']
        except Exception:
            self.__loger.error(f'''Unable to get dilovod order id\n
                                CRM order_id: {order_id}\n
                                Response: \n{dilovod_order_id_response}''')
        dilovod_order_object: dict = await self.__dilovod_client.get_dilovod_order(
            dilovod_id=dilovod_order_id)
        order_status_new = await self.__crm_client.get_status_id('Новий')
        if status_id == order_status_new:
            await self.__dilovod_client.make_move(
                dilovod_response=dilovod_order_object)
        order_status_ukr_post = await self.__crm_client.get_status_id('Укр пошта')
        if status_id == order_status_ukr_post:
            await self.__dilovod_client.make_move(
                dilovod_response=dilovod_order_object)
