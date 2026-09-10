from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager
from typing import List
import json
from app.api.routes.ingestion import router as ingestion_router
from app.api.routes.cases import router as cases_router
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup code here (e.g. initialize db, connect to neo4j)
    yield
    # Teardown code here

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Air-Gapped DFIR Workbench API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.core.websocket_manager import manager

app.include_router(ingestion_router, prefix="/api/v1")
app.include_router(cases_router, prefix="/api/v1/cases")

@app.websocket("/api/v1/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/health")
def health_check():
    return {"status": "ok"}
