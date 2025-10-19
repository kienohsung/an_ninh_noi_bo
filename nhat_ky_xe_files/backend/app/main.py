from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import ALLOW_ORIGINS
from .routers.vehicle_log import router as vehicle_log_router

app = FastAPI(title="Nhat Ky Xe API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS if ALLOW_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vehicle_log_router)

@app.get("/healthz")
def healthz():
    return {"status": "ok"}
