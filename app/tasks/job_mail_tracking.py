import pytz
import asyncio
from datetime import datetime


from app.middlewares.logger.loguru_logger import LoguruLogger
from app.middlewares.dilovod_client.dilovod_client import DilovodClient
from app.middlewares.dilovod_client.dilovod_statistics_middleware import DilovodStatisticsMiddleware

kyiv_tz = pytz.timezone("Europe/Kiev")
logger = LoguruLogger().logger
dilovod_statistics: DilovodStatisticsMiddleware = DilovodStatisticsMiddleware()
dilovod_client: DilovodClient = DilovodClient(
    dilovod_statistics=dilovod_statistics)


async def mail_tracking():
    date: str = datetime.now(tz=kyiv_tz).strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f'''Mail tracking job started at {date}''')
    refund_on_the_road: dict = await dilovod_client.get_orders_in_status(
        status='refund_on_the_road')
    returned_to_branch: dict = await dilovod_client.get_orders_in_status(
        status='returned_to_branch'
    )
    print('refund on the road', refund_on_the_road)
    print('refund on branch', returned_to_branch)


def mail_tracking_wrapper():
    loop = asyncio.new_event_loop()  # Створюємо новий цикл подій
    asyncio.set_event_loop(loop)     # Встановлюємо його як поточний цикл подій
    loop.create_task(mail_tracking())  # Додаємо корутину до циклу подій
    loop.run_forever()
