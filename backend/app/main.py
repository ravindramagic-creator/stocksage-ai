from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auto_sales import router as auto_sales_router
from app.api.financial_results import router as financial_results_router
from app.api.fundamental_analysis import router as fundamental_analysis_router
from app.api.health import router as health_router
from app.api.indices import router as indices_router
from app.api.market_data import router as market_data_router
from app.api.screener import router as screener_router
from app.api.stock_search import router as stock_search_router
from app.api.stocks import router as stocks_router
from app.api.subscriptions import router as subscriptions_router
from app.api.update_stats import router as update_stats_router
from app.api.updates import router as updates_router
from app.api.watchlist import router as watchlist_router
from app.core.config import settings
from app.db.init_db import initialize_database
from app.services.auto_sales_worker import auto_sales_worker
from app.services.market_snapshot_worker import market_snapshot_worker
from app.services.screener_worker import screener_worker
from app.services.universe_worker import universe_worker
from app.services.update_worker import update_worker


async def delayed_auto_sales_worker():
    # Vehicle sales data is daily and can involve a slow external request.
    # Never let it compete with the first dashboard requests.
    await asyncio.sleep(60)
    await auto_sales_worker()


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()

    worker_task = asyncio.create_task(update_worker())
    auto_sales_task = asyncio.create_task(delayed_auto_sales_worker())
    universe_task = asyncio.create_task(universe_worker())
    market_snapshot_task = asyncio.create_task(market_snapshot_worker())
    screener_task = asyncio.create_task(screener_worker())

    try:
        yield
    finally:
        for task in (
            worker_task,
            auto_sales_task,
            universe_task,
            market_snapshot_task,
            screener_task,
        ):
            task.cancel()

        for task in (
            worker_task,
            auto_sales_task,
            universe_task,
            market_snapshot_task,
            screener_task,
        ):
            try:
                await task
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
app.include_router(stock_search_router)
app.include_router(subscriptions_router)
app.include_router(updates_router)
app.include_router(update_stats_router)
app.include_router(financial_results_router)
app.include_router(fundamental_analysis_router)
app.include_router(auto_sales_router)
app.include_router(screener_router)
