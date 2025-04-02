from asyncio import Lock
from typing import Literal

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
        dilovod_order_id_response: list[dict] = await self.__dilovod_client.get_order_id_by_crm_id(
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
            self.__loger.error(f'''Unable to get dilovod object id\n
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
            self.__loger.error(f'''Wrong "dilovod_object"\n
                                Response: {dilovod_order_object}\n''')
            return None
        return dilovod_order_object

    async def get_dict_props(
            self,
            prop_title: list[str],
            crm_order: dict) -> str | ValueError:
        prop_values: dict = {}
        for title in prop_title:
            prop: str | None = crm_order.get(title)
            if not prop:
                raise ValueError(f'''Some of order properties None\n
                                Property: "{title}"''')
            prop_values[title] = prop
        return prop_values

    async def get_ids(self, crm_order: dict[str]) -> dict[str]:
        order_fields: list[str] = ['id', 'order_id']
        try:
            order_fields_values: dict = await self.get_dict_props(
                crm_order=crm_order,
                prop_title=order_fields
            )
        except ValueError as e:
            self.__loger.error(
                f'''{e}\n
                "crm_webhook": {crm_order}''')
            return None
        return order_fields_values

    async def get_object_by_crm(self, order: dict):
        order_fields_values: dict = await self.get_ids(crm_order=order)
        if not order_fields_values:
            return None
        _id: str = order_fields_values['id']
        order_id: str = order_fields_values['order_id']
        async with self.__lock:
            dilovod_order_object: dict = await self.get_dilovod_object_by_crm_id(
                    crm_id=order_id,
                    crm_order_number=_id,
                    dilovod_document="documents.saleOrder"
                )
            return dilovod_order_object

    async def make_move(
            self,
            crm_postback: list[dict],
            move_from: Literal['from_sale', 'from_movement'],
            save_mode: Literal[
                'save_anyway',
                'try_register',
                'dont_register']):
        for order in crm_postback:
            dilovod_order_object: dict = await self.get_object_by_crm(order=order)
            if not dilovod_order_object:
                continue
            if save_mode == 'save_anyway':
                response: str | bool = await self.__dilovod_client.make_move(
                        dilovod_response=dilovod_order_object,
                        move_type=move_from,
                        save_type='registred')
                if response is False:
                    response: str | bool = await self.__dilovod_client.make_move(
                        dilovod_response=dilovod_order_object,
                        move_type=move_from,
                        save_type='unregistred')
                    await self.__dilovod_client.change_status(
                        dilovod_order_id=dilovod_order_object['header']['id']['id'],
                        status='error'
                    )
                else:
                    await self.__dilovod_client.change_status(
                        dilovod_order_id=dilovod_order_object['header']['id']['id'],
                        status='sent_to_post_office'
                    )
                    continue
            if save_mode == 'try_register':
                await self.__dilovod_client.make_move(
                    dilovod_response=dilovod_order_object,
                    move_type=move_from,
                    save_type='registred')
            if save_mode == 'dont_register':
                await self.__dilovod_client.make_move(
                    move_type=move_from,
                    save_type='unregistred'
                )

    async def make_shipment_and_cashin(self, crm_postback: list[dict]):
        for order in crm_postback:
            dilovod_order_object: dict = await self.get_object_by_crm(order=order)
            if not dilovod_order_object:
                continue
            shipment_id: str = await self.__dilovod_client.make_shipment(
                        dilovod_response=dilovod_order_object
                    )
            if not shipment_id:
                continue
            await self.__dilovod_client.change_status(
                dilovod_order_id=dilovod_order_object['header']['id']['id'],
                status='completed')
            await self.__dilovod_client.make_cashIn(
                    dilovod_response=dilovod_order_object,
                    shipment_id=shipment_id
                )

    async def make_refund(self, crm_postback: list[dict]):
        for order in crm_postback:
            order_fields_values: dict = await self.get_ids(crm_order=order)
            if not order_fields_values:
                continue
            _id: str = order_fields_values['id']
            order_id: str = order_fields_values['order_id']
            dilovod_movement_object: dict = await self.get_dilovod_object_by_crm_id(
                        crm_id=order_id,
                        crm_order_number=_id,
                        dilovod_document='documents.goodMoving'
                    )
            if not dilovod_movement_object:
                continue
            dilovod_order_object: dict = await self.get_object_by_crm(order=order)
            if not dilovod_order_object:
                continue
            response: str | bool = await self.__dilovod_client.make_move(
                        dilovod_response=dilovod_movement_object,
                        move_type='from_movement',
                        save_type='registred')
            if response:
                await self.__dilovod_client.change_status(
                    dilovod_order_id=dilovod_order_object['header']['id']['id'],
                    status='refund_on_the_road')
            else:
                await self.__dilovod_client.change_status(
                    dilovod_order_id=dilovod_order_object['header']['id']['id'],
                    status='error'
                )

    async def process_postback_request(
            self,
            postback: list[dict],
            action: str):
        self.__dilovod_statistics.capture_time(point='start')
        if action == 'move':
            await self.make_move(
                crm_postback=postback,
                move_from='from_sale',
                save_mode='save_anyway')
        if action == 'shipment_and_cashIn':
            await self.make_shipment_and_cashin(crm_postback=postback)
        if action == 'refund':
            await self.make_refund(crm_postback=postback)
