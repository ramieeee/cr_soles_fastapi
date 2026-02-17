from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers.multimodal_extraction_route import (
    router as multimodal_extraction_router,
)
from app.routers.paper_review_route import router as paper_review_router
from app.core.logger import set_log

app = FastAPI(title=settings.app_name)
set_log("App started")

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # or ["*"] to allow all origins
    allow_credentials=True,  # Required if including cookies/authentication
    allow_methods=["*"],  # Including POST
    allow_headers=["*"],  # Including Content-Type
)

app.include_router(multimodal_extraction_router, prefix=settings.api_prefix)
app.include_router(paper_review_router, prefix=settings.api_prefix)
set_log("Routers loaded successfully")


@app.get("/")
async def root():
    return {"message": "Hello World"}
