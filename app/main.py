import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

load_dotenv()

from app.api.v1.context import router as context_router
from app.api.v1.demo_booking import router as demo_booking_router

from app.core.exceptions import (
    ContextNotFoundException,
    StorageException
)

from app.core.handlers import (
    context_not_found_handler,
    storage_error_handler
)

from app.core.database import engine, Base
from app.core.logging_config import get_logger
import app.models.domain_models # Ensure models are loaded

log = get_logger("fungus.knowledge_server.main")

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create database tables
    log.info("Knowledge server startup - ensuring database tables exist")
    Base.metadata.create_all(bind=engine)
    log.info("Database tables ready")
    yield
    # Shutdown logic if any
    log.info("Knowledge server shutdown")

app = FastAPI(
    title="Fungus Knowledge Server",
    description="API for managing architectural decisions and context indexed by JIRA IDs",
    version="1.0.0",
    lifespan=lifespan
)
log.info("FastAPI application initialized")

_allowed_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_exception_handler(
    ContextNotFoundException,
    context_not_found_handler
)

app.add_exception_handler(
    StorageException,
    storage_error_handler
)

app.include_router(context_router)
app.include_router(demo_booking_router)