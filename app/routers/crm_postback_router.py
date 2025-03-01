from fastapi import APIRouter, Request


from app.services.crm_postback_service import CrmPostbackService


crm_postback_service = CrmPostbackService()

router = APIRouter(prefix='/postback')


@router.post('/dilovod-sync')
async def dilovod_sync(request: Request):
    postback_request = await request.json()
    await crm_postback_service.process_postback_request(postback=postback_request[0])