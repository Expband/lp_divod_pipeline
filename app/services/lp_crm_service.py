from app.middlewares.logger.loguru_logger import LoguruLogger
from app.middlewares.lp_crm_client.lp_crm_client import LpCrmClient


class LpCrmService:
    def __init__(self):
        self.__loger = LoguruLogger().logger
        self.__crm_client = LpCrmClient()

    async def process_postback_request(self, postback: dict):
        order_id = postback.get('order_id')
        status_id = postback.get('status_id')
        if order_id is None or status_id is None:
            self.__loger.error(
                f'''Unable to get "order_id" of "status_id" field \n
                from postback request: \n
                "order_id": {order_id} \n
                "status_id: {status_id}"''')
            return
