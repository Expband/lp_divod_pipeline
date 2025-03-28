from app.middlewares.novapost_client.novapost_query_builder import NovaPostQueryBuilder
import asyncio
npqb = NovaPostQueryBuilder()
dilovod_sample: list[dict] = []
for i in range(1000):
    b_srt: str = '11111111111111'
    b_srt += str(i)
    dilovod_sample.append({'deliveryRemark_forDel': b_srt},)
res = asyncio.run(npqb.prepare_request(dilovod_orders=dilovod_sample))
print(str(res).replace("'", '"'))