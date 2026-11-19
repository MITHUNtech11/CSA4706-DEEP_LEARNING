"""
FastAPI Main Application.
Serves REST API endpoints and static Interactive Control Panel UI.
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router

BASE_DIR = Path(__file__).resolve().parent.parent.parent
WEB_DIR = BASE_DIR / "web"

app = FastAPI(
    title="Hospital RAG Role-Based Access Control System",
    description="Secure Role-Based Access Control Reference Architecture for Hospital RAG (Capstone CSA4706)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "HEALTHY", "system": "Secure Hospital RAG RBAC"}


# Include API routes
app.include_router(router, prefix="/api")

# Mount web frontend static directory
if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
