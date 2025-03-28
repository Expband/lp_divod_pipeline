from asyncio import Lock

from app.middlewares.logger.loguru_logger import LoguruLogger
from app.middlewares.dilovod_client.dilovod_client import DilovodClient
from app.middlewares.dilovod_client.dilovod_statistics_middleware import DilovodStatisticsMiddleware


class CrmPostbackService:
    def __init__(
        self, loger: LoguruLogger,
        dilovod_client: DilovodClient,
        dilovod_statistics_handler: DilovodStatisticsMiddleware):
        self.__loger = loger.logger
        self.__dilovod_client = dilovod_client
        self.__dilovod_statistics = dilovod_statistics_handler
        self.__lock = Lock()

    async def process_postback_request(self, postback: list[dict], action: str):
        self.__dilovod_statistics.capture_time(point='start')
        i: int = 0
        for order in postback:
            order_id: str | None = order.get('order_id')
            order_number: str | None = order.get('id')
            if not order_id or not order_number:
                self.__loger.error(
                    f'''Unable to get "order_id" of "status_id" field \n
                    from postback request: \n
                    "order_id": {order_id}''')
                self.__dilovod_statistics.update_statistics(
                    status='unsuccess',
                    description='error_other')
                continue
            async with self.__lock:
                dilovod_order_id_response: list[dict] = await self.__dilovod_client.get_object_id_by_crm_id(
                    crm_id=order_id,
                    order_id=order_number,
                    document="documents.saleOrder")
                if not dilovod_order_id_response:
                    self.__loger.error(f'''Unexpected error occured while getting Dilovod order id from CRM.\n
                                        CRM "order_id": {order_id}''')
                    continue
                try:
                    dilovod_order_id: str = dilovod_order_id_response[0]['id']
                except Exception:
                    self.__loger.error(f'''Unable to get dilovod order id\n
                                        CRM order_id: {order_id}\n
                                        Response: \n{dilovod_order_id_response}''')
                    self.__dilovod_statistics.update_statistics(
                        status='unsuccess',
                        description='error_not_found'
                    )
                    continue
                dilovod_order_object: dict = await self.__dilovod_client.get_dilovod_order(
                    dilovod_id=dilovod_order_id)
                if not dilovod_order_object:
                    self.__dilovod_statistics.update_statistics(
                        status='unsuccess',
                        description='error_other'
                    )
                    self.__loger.error(f'''Wrong "dilovod_order_object"\n
                                        Response: {dilovod_order_object}\n''')
                    continue
                if action == 'move':
                    await self.__dilovod_client.make_move(
                        dilovod_response=dilovod_order_object)
                if action == 'shipment':
                    shipment_id: str = await self.__dilovod_client.make_shipment(
                        dilovod_response=dilovod_order_object
                    )
                    if not shipment_id:
                        self.__loger.error(f'''Unable to get "shipment_id" for "dilovod_id": {dilovod_order_id}\n''')
                        continue
                    await self.__dilovod_client.make_cashIn(
                        dilovod_response=dilovod_order_object,
                        shipment_id=shipment_id
                    )
            i += 1
        print(i)
        self.__dilovod_statistics.capture_time(point='end')
        statistics: dict = self.__dilovod_statistics.get_statistics()
        self.__loger.info(statistics)
