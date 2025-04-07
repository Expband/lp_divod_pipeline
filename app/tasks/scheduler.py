from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from typing import Callable

from app.middlewares.logger.loguru_logger import LoguruLogger


class Scheduler:
    def __init__(self):
        self.__scheduler = AsyncIOScheduler()
        self.__logger = LoguruLogger().logger

    def start(self):
        self.__logger.info('Job scheduler started')
        self.__scheduler.start()

    def shutdown(self):
        self.__logger.info('Job scheduler stopped')
        self.__scheduler.shutdown()

    def add_job(
            self,
            func: Callable,
            hours: int = 0,
            minutes: int = 0,
            seconds: int = 0):
        if hours == 0 and minutes == 0 and seconds == 0:
            raise ValueError('Jobs delay cant be 0')
        trigger = IntervalTrigger(
            hours=hours,
            minutes=minutes,
            seconds=seconds
            )
        job = self.__scheduler.add_job(func=func, trigger=trigger)
        self.__logger.info(f'''Scheduled job added: {job.name}.
                            Next run at: {job.next_run_time}''')
