from fastapi import FastAPI

from app.api.routes import router


app = FastAPI(title="proof-of-browse-verifier")
app.include_router(router)

