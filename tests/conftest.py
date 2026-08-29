"""Set required environment variables before any app module is imported."""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_placeholder.db")
os.environ.setdefault("FUNGUS_AUTH_DISABLED", "true")
