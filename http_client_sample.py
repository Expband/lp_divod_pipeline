import asyncio
from app.middlewares.dilovod_client.dilovod_query_builder import DilovodQueryBuilder

dqb = DilovodQueryBuilder()

fields: dict = {
    "id": "id",
    "remark": "remark"
}
filters_list: list[dict] = [
    {
        "alias": "remark",
        "operator": "%",
        "value": "1741982178771930"
    }
]

req = asyncio.run(dqb.configure_payload(action="request",
                                        document="documents.saleOrder",
                                        fields=fields,
                                        filters_list=filters_list))

srt_req = str(req)
print(srt_req.replace("'", '"'))