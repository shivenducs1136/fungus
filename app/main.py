from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from app.api.v1.context import router

from app.core.exceptions import (
    ContextNotFoundException,
    StorageException
)

from app.core.handlers import (
    context_not_found_handler,
    storage_error_handler
)

from app.core.database import engine, Base
import app.models.domain_models # Ensure models are loaded

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create database tables
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown logic if any

app = FastAPI(
    title="Fungus Knowledge Server",
    description="API for managing architectural decisions and context indexed by JIRA IDs",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.add_exception_handler(
    ContextNotFoundException,
    context_not_found_handler
)

app.add_exception_handler(
    StorageException,
    storage_error_handler
)

app.include_router(router)