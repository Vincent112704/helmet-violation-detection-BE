from fastapi import FastAPI
from app.api.dashboard import router as dashboard_router
from app.api.table import router as table_router
from app.api.upload import router as upload_router
from app.repository.db import supabase

app = FastAPI(title="FastAPI Boilerplate", version="0.1.0")


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI"}


@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/db_health")
def db_check():
    response = (
        supabase.table("personnel")
        .select("*")
        .execute()
    )

    return response.data

app.include_router(dashboard_router, prefix='/api/dashboard')
app.include_router(table_router, prefix='/api/table')
app.include_router(upload_router, prefix='/api/upload')
