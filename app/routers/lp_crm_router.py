from fastapi import APIRouter, Request


router = APIRouter(prefix='/postback')


@router.post('/dilovod-sync')
async def dilovod_sync(request: Request):
    postback_request = request.json()
