from app.routers.lp_crm_router import router

from fastapi import FastAPI


app = FastAPI()
app.include_router(router)
