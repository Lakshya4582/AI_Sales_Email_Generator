import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import inspect, text

from backend.db import Base, engine
from backend import models  # noqa: F401  (register ORM models with Base)
from backend.limits import limiter
from backend.routes import router

app = FastAPI(title="AI Sales Email Generator")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# FRONTEND_ORIGIN — set this to your Vercel URL in production (e.g.
# https://myapp.vercel.app). Comma-separated for multiple origins.
# When unset (local dev), allows any origin.
_origins_env = os.getenv("FRONTEND_ORIGIN", "").strip()
if _origins_env:
    allow_origins = [o.strip() for o in _origins_env.split(",") if o.strip()]
else:
    allow_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=False,
    allow_methods=["POST", "GET", "OPTIONS", "DELETE", "PATCH"],
    allow_headers=["Content-Type", "Authorization"],
)


def _apply_lightweight_migrations():
    """Add columns that were introduced after the table already existed.
    Dev-only pattern. For production use Alembic."""
    inspector = inspect(engine)
    if "email_history" not in inspector.get_table_names():
        return
    cols = {c["name"] for c in inspector.get_columns("email_history")}
    with engine.begin() as conn:
        if "parent_id" not in cols:
            conn.execute(text("ALTER TABLE email_history ADD COLUMN parent_id INTEGER"))


Base.metadata.create_all(bind=engine)
_apply_lightweight_migrations()

app.include_router(router)


@app.get("/")
def home():
    return {"message": "AI Email Generator Running"}
