from typing import Callable, Awaitable

from app.services.crm_postback_service import CrmPostbackService
from app.middlewares.dilovod_client.dilovod_client import DilovodClient
from app.middlewares.logger.loguru_logger import LoguruLogger
from app.middlewares.dilovod_client.dilovod_statistics_middleware import DilovodStatisticsMiddleware

loger = LoguruLogger()
dilovod_statistics_handler = DilovodStatisticsMiddleware()
dilovod_client = DilovodClient(
    dilovod_statistics=dilovod_statistics_handler
)
crm_postback_service = CrmPostbackService(
    loger=loger,
    dilovod_client=dilovod_client,
    dilovod_statistics_handler=dilovod_statistics_handler
)

# Очікуємо data з ключами 'postback' і 'action'
request_handler: dict[tuple[str, str], Callable[[dict], Awaitable[None]]] = {
    ('POST', '/postback/dilovod-sync/post-transfer'): lambda data: crm_postback_service.process_postback_request(
        postback=data['postback'], action='move'
    ),
    ('POST', '/postback/dilovod-sync/finished'): lambda data: crm_postback_service.process_postback_request(
        postback=data['postback'], action='shipment_and_cashIn'
    ),
    ('POST', '/postback/dilovod-sync/refund'): lambda data: crm_postback_service.process_postback_request(
        postback=data['postback'], action='refund'
    )
}