import threading
from fastapi import FastAPI

from app.services.ingestion import run_ingestion_loop
from app.streaming.consumer import run_consumer
from app.api.routes import router

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

from app.db.base import Base
from app.db.session import engine

@app.on_event("startup")
def startup():

    print("🚀 Starting systems...")
    Base.metadata.create_all(bind=engine)

    # Kafka consumer → DB writer
    t1 = threading.Thread(target=run_consumer, daemon=True)
    t1.start()

    # Yahoo → Kafka producer
    t2 = threading.Thread(target=run_ingestion_loop, daemon=True)
    t2.start()