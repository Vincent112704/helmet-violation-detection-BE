from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from app.api.dashboard import router as dashboard_router
from app.api.table import router as table_router
from app.api.upload import router as upload_router
from app.repository.db import supabase
from app.dependencies.auth import get_user
from ultralytics import YOLO
from fastapi.middleware.cors import CORSMiddleware
from paddleocr import PaddleOCR


import logging

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model = YOLO("model/best.pt")
    app.state.ocr_model = PaddleOCR(
        use_angle_cls=True,
        lang="en",
        show_log=False,
        use_gpu=False,
    )
    logging.info("Model loaded successfully.")
    yield


app = FastAPI(title="FastAPI Boilerplate", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(dashboard_router, prefix='/api/dashboard', dependencies=[Depends(get_user)])
app.include_router(table_router, prefix='/api/table', dependencies=[Depends(get_user)])
app.include_router(upload_router, prefix='/api/upload')



