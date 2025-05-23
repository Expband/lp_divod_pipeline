from app.routers.crm_postback_router import router
from app.routers.queue_router import request_handler
from app.tasks.job_on_road_tracking import mail_tracking_on_road
from app.tasks.job_on_branch_tracking import mail_tracking_on_branch
from app.tasks.refund_wrapper import refund_wrapper
from app.tasks.scheduler import Scheduler
from app.middlewares.logger.loguru_logger import LoguruLogger

from typing import Callable, Awaitable
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
import uuid


logger = LoguruLogger().logger
task_queue = asyncio.Queue()

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(worker())
    logger.info('Request worker created')
    sc = Scheduler()
    sc.start()
    logger.info(f'Scheduler started')
    sc.add_job(refund_wrapper, hours=0, minutes=6, seconds=0)
    yield
    sc.shutdown()
    logger.info(f'Scheduler stopped')


app = FastAPI(lifespan=lifespan)
app.include_router(router)


async def worker():
    while True:
        task: asyncio.Task = await task_queue.get()
        handler: Callable[[dict], Awaitable[None]] = task['handler']
        payload: dict = task['payload']
        try:
            await handler(payload)
        except Exception as ex:
            logger.error(f'Error occured while task execution: {ex}')
        task_queue.task_done()


@app.middleware('http')
async def handle_http_enqueue(request: Request, call_next):
    if request.url.path.startswith('/docs') or request.url.path.startswith('/openapi'):
        return await call_next(request)

    key = (request.method, request.url.path)
    handler = request_handler.get(key)

    if not handler:
        return JSONResponse(status_code=404, content={'message': 'Not found'})

    try:
        body = await request.json()
    except Exception:
        body = {}

    task_data = {
        'handler': handler,
        'payload': {'postback': body},
    }

    await task_queue.put(task_data)
    print(f'Task added: {key}')
    return JSONResponse(status_code=202, content={'message': 'task added to queue'})
