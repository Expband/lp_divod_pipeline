from app.middlewares.logger.loguru_logger import LoguruLogger
from app.middlewares.lp_crm_client.lp_crm_client import LpCrmClient
from app.middlewares.dilovod_client.dilovod_client import DilovodClient


class CrmPostbackService:
    def __init__(self):
        self.__loger = LoguruLogger().logger
        self.__crm_client = LpCrmClient()
        self.__dilovod_client = DilovodClient()

    async def process_postback_request(self, postback: dict):
        order_id = postback.get('order_id')
        status_id = postback.get('status')
        if order_id is None or status_id is None:
            self.__loger.error(
                f'''Unable to get "order_id" of "status_id" field \n
                from postback request: \n
                "order_id": {order_id} \n
                "status_id: {status_id}"''')
            return None
        dilovod_order_id = await self.__dilovod_client.get_oreder_by_crm_id(order_id)
        if dilovod_order_id is None:
            return None
        if status_id == '3':
            print(dilovod_order_id)
