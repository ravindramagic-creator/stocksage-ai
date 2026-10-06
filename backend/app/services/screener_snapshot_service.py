from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from app.models.screener_snapshot import ScreenerSnapshot
from app.models.stock import Stock
from app.schemas.screener import ScreenerFilters, ScreenerResult
from app.services.screener_service import StockScreenerService


class ScreenerSnapshotService:
    """Persist the expensive screener calculation and serve cached rankings."""

    def __init__(self, db: Session):
        self.db = db

    def refresh(self, universe_limit: int = 5000) -> int:
        version = (
            datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            + "-"
            + uuid4().hex[:8]
        )

        batch_size = 100
        all_results_by_symbol: dict[str, ScreenerResult] = {}
        offset = 0

        while offset < universe_limit:
            batch_limit = min(
                batch_size,
                universe_limit - offset,
            )
            filters = ScreenerFilters(
                min_score=0,
                min_roe=-100,
                max_pe=500,
                max_debt_to_equity=20,
                min_revenue_growth=-100,
                min_profit_growth=-100,
                min_market_cap=0,
                limit=batch_limit,
                universe_limit=batch_limit,
            )

            total_universe, results = (
                StockScreenerService(self.db).screen(
                    filters,
                    offset=offset,
                )
            )

            for result in results:
                symbol = result.symbol.upper()
                previous = all_results_by_symbol.get(symbol)

                if (
                    previous is None
                    or (
                        result.score,
                        result.data_completeness,
                    )
                    > (
                        previous.score,
                        previous.data_completeness,
                    )
                ):
                    all_results_by_symbol[symbol] = result

            offset += batch_limit
            if offset >= total_universe:
                break

        all_results = sorted(
            all_results_by_symbol.values(),
            key=lambda item: (
                item.verdict not in {
                    "BUY",
                    "STRONG BUY",
                },
                -item.score,
                -item.data_completeness,
                item.symbol,
            ),
        )

        if not all_results:
            return 0

        self.db.execute(
            delete(ScreenerSnapshot)
        )
        now = datetime.now(timezone.utc)

        for result in all_results:
            self.db.add(
                ScreenerSnapshot(
                    symbol=result.symbol,
                    company_name=result.company_name,
                    sector=result.sector,
                    score=result.score,
                    verdict=result.verdict,
                    data_completeness=result.data_completeness,
                    price=result.price,
                    market_cap=result.market_cap,
                    pe=result.pe,
                    peg=result.peg,
                    pb=result.pb,
                    roe=result.roe,
                    roce=result.roce,
                    debt_to_equity=result.debt_to_equity,
                    revenue_growth=result.revenue_growth,
                    profit_growth=result.profit_growth,
                    eps_growth=result.eps_growth,
                    sma50=result.sma50,
                    sma200=result.sma200,
                    rsi14=result.rsi14,
                    momentum_6m=result.momentum_6m,
                    target_upside=result.target_upside,
                    analyst_beat_rate=result.analyst_beat_rate,
                    fundamental_score=result.fundamental_score,
                    valuation_score=result.valuation_score,
                    technical_score=result.technical_score,
                    analyst_score=result.analyst_score,
                    snapshot_at=now,
                    snapshot_version=version,
                )
            )

        self.db.commit()
        return len(all_results)

    def get_results(
        self,
        filters: ScreenerFilters,
    ) -> tuple[
        int,
        list[ScreenerResult],
        datetime | None,
    ]:
        total_universe = (
            self.db.scalar(
                select(func.count())
                .select_from(Stock)
                .where(Stock.exchange == "NSE")
            )
            or 0
        )

        # Push the screener filters into SQL instead of loading the entire
        # snapshot table and filtering thousands of rows in Python on every
        # page request.
        market_cap_floor = (
            filters.min_market_cap * 10_000_000
        )

        query = (
            select(ScreenerSnapshot)
            .where(
                ScreenerSnapshot.score >= filters.min_score,
                ScreenerSnapshot.data_completeness >= 75,
                ScreenerSnapshot.roe.is_not(None),
                ScreenerSnapshot.roce.is_not(None),
                ScreenerSnapshot.pe.is_not(None),
                ScreenerSnapshot.pe > 0,
                ScreenerSnapshot.price.is_not(None),
                ScreenerSnapshot.sma50.is_not(None),
                ScreenerSnapshot.sma200.is_not(None),
                ScreenerSnapshot.rsi14.is_not(None),
                ScreenerSnapshot.momentum_6m.is_not(None),
                ScreenerSnapshot.roe >= filters.min_roe,
                ScreenerSnapshot.pe <= filters.max_pe,
                ScreenerSnapshot.revenue_growth.is_not(None),
                ScreenerSnapshot.revenue_growth
                >= filters.min_revenue_growth,
                ScreenerSnapshot.profit_growth.is_not(None),
                ScreenerSnapshot.profit_growth
                >= filters.min_profit_growth,
                or_(
                    ScreenerSnapshot.debt_to_equity.is_(None),
                    ScreenerSnapshot.debt_to_equity
                    <= filters.max_debt_to_equity,
                ),
                or_(
                    ScreenerSnapshot.market_cap.is_(None),
                    ScreenerSnapshot.market_cap
                    >= market_cap_floor,
                ),
            )
            .order_by(
                ScreenerSnapshot.score.desc(),
                ScreenerSnapshot.data_completeness.desc(),
                ScreenerSnapshot.symbol.asc(),
            )
            .limit(filters.limit)
        )

        rows = self.db.execute(
            query
        ).scalars().all()

        results: list[ScreenerResult] = []

        for row in rows:
            peg = row.peg

            results.append(
                ScreenerResult(
                    rank=len(results) + 1,
                    symbol=row.symbol,
                    company_name=row.company_name,
                    sector=row.sector,
                    score=row.score,
                    verdict=row.verdict,
                    data_completeness=row.data_completeness,
                    price=row.price,
                    market_cap=row.market_cap,
                    pe=row.pe,
                    peg=peg,
                    pb=row.pb,
                    roe=row.roe,
                    roce=row.roce,
                    debt_to_equity=row.debt_to_equity,
                    revenue_growth=row.revenue_growth,
                    profit_growth=row.profit_growth,
                    eps_growth=row.eps_growth,
                    sma50=row.sma50,
                    sma200=row.sma200,
                    rsi14=row.rsi14,
                    momentum_6m=row.momentum_6m,
                    target_upside=row.target_upside,
                    analyst_beat_rate=row.analyst_beat_rate,
                    fundamental_score=row.fundamental_score,
                    valuation_score=row.valuation_score,
                    technical_score=row.technical_score,
                    analyst_score=row.analyst_score,
                )
            )

        snapshot_at = (
            rows[0].snapshot_at
            if rows
            else None
        )

        return (
            int(total_universe),
            results,
            snapshot_at,
        )
