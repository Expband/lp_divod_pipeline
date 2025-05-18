exmpl_resp: dict = {
    "error": "multithreadApiSession multithread api request blocked"
}

exmpl_resp_2: dict = [
   {
      "id":"1109100000110120",
      "id__pr":"22.04.2025 Замовлення НР00109092",
      "remark":"Заказ из CRM: 17453159493, vibegroup 380954",
      "state":"1111500000001004",
      "state__pr":"[access restricted]"
   },
   {
      "id":"1109100000117754",
      "id__pr":"28.04.2025 Замовлення НР00116726",
      "remark":"Заказ из CRM: 17458449616, vibegroup 393461",
      "state":"1111500000001004",
      "state__pr":"[access restricted]"
   },
   {
      "id":"1109100000118317",
      "id__pr":"29.04.2025 Замовлення НР00117289",
      "remark":"Заказ из CRM: 17459063015, vibegroup 395106",
      "state":"1111500000001004",
      "state__pr":"[access restricted]"
   }]

# for r in exmpl_resp:
#     rr = r['id']


# for rrr in exmpl_resp_2:
#     rrrr = rrr['id']



if not isinstance(exmpl_resp_2, list):
    print('not list')