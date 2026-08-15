from contextlib import asynccontextmanager
import asyncio

from app.api.updates import router as updates_router
from app.services.update_worker import update_worker
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.stocks import router as stocks_router
from app.api.watchlist import router as watchlist_router
from app.core.config import settings
from app.db.init_db import initialize_database
from app.api.market_data import (
    router as market_data_router,
)
from app.api.indices import (
    router as indices_router,
)
from app.api.stock_search import (
    router as stock_search_router,
)

from app.api.subscriptions import (
    router as subscriptions_router,
)
from app.api.updates import (
    router as updates_router,
)
from app.api.update_stats import (
    router as update_stats_router,
)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database first
    initialize_database()

    # Start StockSage background update worker
    worker_task = asyncio.create_task(
        update_worker()
    )

    try:
        yield
    finally:
        # Stop worker when FastAPI shuts down
        worker_task.cancel()

        try:
            await worker_task
        except asyncio.CancelledError:
            pass

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(stocks_router)
app.include_router(watchlist_router)
app.include_router(market_data_router)
app.include_router(indices_router)
app.include_router(
    stock_search_router
)

app.include_router(
    subscriptions_router
)

app.include_router(
    updates_router
)
app.include_router(
    update_stats_router
)
