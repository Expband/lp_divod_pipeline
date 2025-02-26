import asyncio

from middlewares.lp_crm_client.lp_crm_client import LpCrmClient

lpc = LpCrmClient()

status_id = asyncio.run(lpc.get_status_id(status='НЕ АКТУАЛЬНО'))
print(status_id)
