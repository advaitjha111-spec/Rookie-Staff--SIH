from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.routes.ingestion import router as ingestion_router
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup code here (e.g. initialize db, connect to neo4j)
    yield
    # Teardown code here

app = FastAPI(
    title="Air-Gapped DFIR Workbench API",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(ingestion_router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {"status": "ok"}
