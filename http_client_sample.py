from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.tasks.job_mail_tracking import mail_tracking_wrapper

# Створення планувальника
scheduler = BlockingScheduler()

# Додавання завдання до планувальника: виконання кожні 5 секунд
scheduler.add_job(mail_tracking_wrapper, IntervalTrigger(seconds=25))

# Запуск планувальника
scheduler.start()



# from app.services.crm_postback_service import CrmPostbackService
# from app.middlewares.logger.loguru_logger import LoguruLogger
# from app.middlewares.dilovod_client.dilovod_client import DilovodClient
# from app.middlewares.dilovod_client.dilovod_statistics_middleware import DilovodStatisticsMiddleware

# import asyncio
# ll = LoguruLogger()
# dsm = DilovodStatisticsMiddleware()
# dc = DilovodClient(dilovod_statistics=dsm)

# asyncio.run(dc.get_orders_in_status(status='utilization'))

# cps = CrmPostbackService(loger=ll, dilovod_client=dc, dilovod_statistics_handler=dsm)

# props_title: list = ['order_id', 'id']
# crm_order: dict = {
#     "id": "98299",
#     "order_id": "1743452854321696",
#     "phone": "3433",
#     "buyer_name": "Тестовий на час",
#     "additional_1": "",
#     "additional_2": "",
#     "additional_3": "",
#     "additional_4": "",
#     "cancel_description": "",
#     "comment": "",
#     "email": "",
#     "localization": "UA",
#     "office": "2",
#     "payment": "4",
#     "site": "",
#     "status": "83",
#     "total": "399.00",
#     "ttn": "",
#     "ttn_status": "",
#     "attached_user": "admin",
#     "utm_campaign": "",
#     "utm_content": "",
#     "utm_medium": "",
#     "utm_source": "",
#     "utm_term": "",
#     "user": "Illiasdmin",
#     "products": [
#         {
#             "order_id": "1743452854321696",
#             "id": "687",
#             "quantity": "1",
#             "price": "399.00",
#             "id_sub": "0",
#             "name_sub": "",
#             "name": "ОДЯГ Спінер-антистрес сірий"
#         }
#     ],
#     "products_resale": []
#     }
# res = asyncio.run(cps.get_ids(crm_order=crm_order))
# print(res)