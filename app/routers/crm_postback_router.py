from fastapi import APIRouter, Request


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

router = APIRouter(prefix='/postback')


@router.post('/dilovod-sync/post-transfer')
async def dilovod_sync_post_transfer(request: Request):
    print('request')
    postback_request: dict = await request.json()
    await crm_postback_service.process_postback_request(
        postback=postback_request,
        action='move')


@router.post('/dilovod-sync/finished')
async def dilovod_sync_finished(request: Request):
    postback_request: dict = await request.json()
    await crm_postback_service.process_postback_request(
        postback=postback_request,
        action='shipment'
    )
