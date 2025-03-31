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

    async def get_dilovod_object_by_crm_id(
            self,
            crm_id: str,
            crm_order_number: str,
            dilovod_document: str) -> dict:
        dilovod_order_id_response: list[dict] = await self.__dilovod_client.get_object_id_by_crm_id(
                    crm_id=crm_id,
                    order_id=crm_order_number,
                    document=dilovod_document)
        if not dilovod_order_id_response:
            self.__loger.error(f'''Unexpected error occured while getting
                                Dilovod object id from CRM.\n
                                CRM "order_id": {crm_id}''')
            return None
        try:
            dilovod_order_id: str = dilovod_order_id_response[0]['id']
        except Exception:
            self.__loger.error(f'''Unable to get dilovod order id\n
                                CRM order_id: {crm_id}\n
                                Response: \n{dilovod_order_id_response}''')
            self.__dilovod_statistics.update_statistics(
                status='unsuccess',
                description='error_not_found'
            )
            return None
        dilovod_order_object: dict = await self.__dilovod_client.get_dilovod_object_by_id(
            dilovod_id=dilovod_order_id)
        if not dilovod_order_object:
            self.__dilovod_statistics.update_statistics(
                status='unsuccess',
                description='error_other'
            )
            self.__loger.error(f'''Wrong "dilovod_order_object"\n
                                Response: {dilovod_order_object}\n''')
            return None
        return dilovod_order_object

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
                if action == 'move':
                    dilovod_order_object: dict = await self.get_dilovod_object_by_crm_id(
                        crm_id=order_id,
                        crm_order_number=order_number,
                        dilovod_document="documents.saleOrder"
                    )
                    if not dilovod_order_object:
                        continue
                    await self.__dilovod_client.make_move(
                        dilovod_response=dilovod_order_object,
                        move_type='from_sale')
                if action == 'shipment':
                    dilovod_order_object: dict = await self.get_dilovod_object_by_crm_id(
                        crm_id=order_id,
                        crm_order_number=order_number,
                        dilovod_document="documents.saleOrder"
                    )
                    if not dilovod_order_object:
                        continue
                    shipment_id: str = await self.__dilovod_client.make_shipment(
                        dilovod_response=dilovod_order_object
                    )
                    if not shipment_id:
                        dilovod_order_id: str = dilovod_order_object['header']['id']['id']
                        self.__loger.error(f'''Unable to get "shipment_id" for 
                                            "dilovod_id": {dilovod_order_id}\n''')
                        continue
                    await self.__dilovod_client.make_cashIn(
                        dilovod_response=dilovod_order_object,
                        shipment_id=shipment_id
                    )
                if action == 'refund':
                    dilovod_movement_object: dict = await self.get_dilovod_object_by_crm_id(
                        crm_id=order_id,
                        crm_order_number=order_number,
                        dilovod_document='documents.goodMoving'
                    )
                    print(dilovod_movement_object)
                    await self.__dilovod_client.make_move(
                        dilovod_response=dilovod_movement_object,
                        move_type='from_movement')
            i += 1
        self.__dilovod_statistics.capture_time(point='end')
        statistics: dict = self.__dilovod_statistics.get_statistics()
        self.__loger.info(statistics)
