import asyncio
from app.middlewares.dilovod_client.dilovod_client import DilovodClient

dd = DilovodClient()
resp = asyncio.run(
    dd.configure_payload(
        action='request',
        document='documents.saleOrder',
        fields={'id': 'id', 'remark': 'remark'},
        filters_list=[
            {'alias': 'remark', 'operator': '%', 'value': '17392727069'}]
    )
)

response = asyncio.run(
    dd.get_oreder_by_crm_id('17393133386')
)

print(resp)
print(response)
# from app.middlewares.lp_crm_client.lp_crm_client import LpCrmClient

# lpc = LpCrmClient()

# status_id = asyncio.run(lpc.get_status_id(status='НЕ АКТУАЛЬНО'))
# print(status_id)
