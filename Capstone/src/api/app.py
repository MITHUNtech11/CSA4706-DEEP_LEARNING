"""
FastAPI Main Application.
Production-hardened with security headers, correlation IDs, and multi-page portal views.
"""

import uuid
import time
from pathlib import Path
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router
from src.config import CORS_ORIGINS, ENVIRONMENT, logger

BASE_DIR = Path(__file__).resolve().parent.parent.parent
WEB_DIR = BASE_DIR / "web"

app = FastAPI(
    title="Hospital RAG Role-Based Access Control System",
    description="Secure Role-Based Access Control Reference Architecture for Hospital RAG (Capstone CSA4706)",
    version="1.0.0",
    docs_url="/docs" if ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if ENVIRONMENT != "production" else None
)

# 1. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"]
)


# 2. Security Headers & Request Correlation ID Middleware
@app.middleware("http")
async def security_and_tracing_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    start_time = time.time()

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"

    if ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    latency_ms = round((time.time() - start_time) * 1000, 2)
    logger.info(f"[{request_id}] {request.method} {request.url.path} -> {response.status_code} ({latency_ms}ms)")

    return response


# Favicon Endpoint (Prevents browser 404s)
@app.get("/favicon.ico")
def favicon():
    svg_icon = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#0f766e" stroke-width="2.5"><path d="M12 2v20M2 12h20M4.93 4.93l14.14 14.14M19.07 4.93L4.93 19.07"/></svg>"""
    return Response(content=svg_icon, media_type="image/svg+xml")


# Standard Health Check (for backward compatibility)
@app.get("/health")
def health():
    return {"status": "HEALTHY", "system": "Secure Hospital RAG RBAC", "environment": ENVIRONMENT}


# Include API routes
app.include_router(router, prefix="/api")


# Dedicated Role-Specific Portal Route Endpoints
@app.get("/portal/cmo")
def portal_cmo():
    return FileResponse(WEB_DIR / "cmo.html")


@app.get("/portal/dept-head")
def portal_dept_head():
    return FileResponse(WEB_DIR / "dept_head.html")


@app.get("/portal/doctor")
def portal_doctor():
    return FileResponse(WEB_DIR / "doctor.html")


@app.get("/portal/nurse")
def portal_nurse():
    return FileResponse(WEB_DIR / "nurse.html")


@app.get("/portal/billing")
def portal_billing():
    return FileResponse(WEB_DIR / "billing.html")


@app.get("/portal/admin")
def portal_admin():
    return FileResponse(WEB_DIR / "admin.html")


@app.get("/portal/gateway")
def portal_gateway():
    return FileResponse(WEB_DIR / "index.html")


# Static Asset Fallback under /portal/ (fixes relative requests like /portal/style.css)
@app.get("/portal/{asset_name:path}")
def portal_static_fallback(asset_name: str):
    file_path = WEB_DIR / asset_name
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    # Check if html extension was omitted
    html_path = WEB_DIR / f"{asset_name}.html"
    if html_path.exists() and html_path.is_file():
        return FileResponse(html_path)
    return Response(content="File Not Found", status_code=404)


# Mount static directory for JS, CSS, and direct file access
if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
