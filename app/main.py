from fastapi import FastAPI

from app.core.config import settings
from app.routers.document_process import router as document_router

app = FastAPI(title=settings.app_name)
app.include_router(document_router, prefix=settings.api_prefix)


@app.get("/")
async def root():
    return {"message": "Hello World"}
