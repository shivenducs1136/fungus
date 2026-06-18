from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.context import router

from app.core.exceptions import (
    ContextNotFoundException,
    StorageException
)

from app.core.handlers import (
    context_not_found_handler,
    storage_error_handler
)

app = FastAPI(
    title="Fungus Knowledge Server",
    description="API for managing architectural decisions and context indexed by JIRA IDs",
    version="1.0.0"
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