from fastapi import FastAPI

from app.api.routes import router
from app.core.config import settings


settings.validate_runtime()
app = FastAPI(title="proof-of-browse-browser-worker")
app.include_router(router)
