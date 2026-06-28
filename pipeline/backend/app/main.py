from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .api.upload import router as upload_router
from .api.admin import router as admin_router
from .api.search import router as search_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Nursing Textbook Ingestion Pipeline", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(admin_router)
app.include_router(search_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
