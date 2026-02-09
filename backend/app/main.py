from fastapi import FastAPI

from app.api.routes import router
from app.db.base import Base
from app.db.session import engine
from app import models  # noqa: F401
from app.workers.queue import start_worker, stop_worker

app = FastAPI(title="AI Call Optimizer / De-LLM-ifier", version="1.0.0")
app.include_router(router)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    start_worker()


@app.on_event("shutdown")
def on_shutdown() -> None:
    stop_worker()
