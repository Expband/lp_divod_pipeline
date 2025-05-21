from app.routers.crm_postback_router import router
from app.tasks.job_on_road_tracking import mail_tracking_on_road
from app.tasks.job_on_branch_tracking import mail_tracking_on_branch
from app.tasks.refund_wrapper import refund_wrapper
from app.tasks.scheduler import Scheduler
from app.middlewares.logger.loguru_logger import LoguruLogger

from fastapi import FastAPI
from contextlib import asynccontextmanager

logger = LoguruLogger().logger


#TODO:
# 1) clean mail_tracking_on_road and mail_tracking_on_branch
# methods (code duplicates)
# 2) add descriptions for methods
# 3) change np and up trigger status codes
# 4) add ttn to remark
# 5) add queue for incoming requests


@asynccontextmanager
async def lifespan(app: FastAPI):
    sc = Scheduler()
    sc.start()
    logger.info(f'Scheduler started')
    sc.add_job(refund_wrapper, hours=0, minutes=5, seconds=0)
    sc.add_job(mail_tracking_on_road, hours=0, minutes=1, seconds=0)
    logger.info(f'Task "mail_tracking_on_road" added')
    sc.add_job(mail_tracking_on_branch, hours=0, minutes=1, seconds=0)
    logger.info(f'Task "mail_tracking_on_branch" added')
    yield
    sc.shutdown()
    logger.info(f'Scheduler stopped')


app = FastAPI(lifespan=lifespan)
app.include_router(router)
