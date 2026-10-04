from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import delete, func, select
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

        # Process the underlying Stock rows in fixed-size batches. The cursor
        # must advance by rows scanned, not by candidates returned, otherwise
        # a batch with few matches causes the same stocks to be processed again.
        batch_size = 100
        all_results_by_symbol: dict[str, ScreenerResult] = {}
        offset = 0

        while offset < universe_limit:
            batch_limit = min(batch_size, universe_limit - offset)
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

            total_universe, results = StockScreenerService(self.db).screen(
                filters,
                offset=offset,
            )

            for result in results:
                symbol = result.symbol.upper()
                previous = all_results_by_symbol.get(symbol)
                if (
                    previous is None
                    or (result.score, result.data_completeness)
                    > (previous.score, previous.data_completeness)
                ):
                    all_results_by_symbol[symbol] = result

            offset += batch_limit
            if offset >= total_universe:
                break

        all_results = sorted(
            all_results_by_symbol.values(),
            key=lambda item: (
                item.verdict not in {"BUY", "STRONG BUY"},
                -item.score,
                -item.data_completeness,
                item.symbol,
            ),
        )

        if not all_results:
            return 0

        self.db.execute(delete(ScreenerSnapshot))
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
    ) -> tuple[int, list[ScreenerResult], datetime | None]:
        # Report the actual active NSE universe, not merely the number of
        # symbols that happened to have usable snapshot data.
        total_universe = self.db.scalar(
            select(func.count())
            .select_from(Stock)
            .where(Stock.exchange == "NSE")
        ) or 0

        query = select(ScreenerSnapshot).order_by(
            ScreenerSnapshot.score.desc(),
            ScreenerSnapshot.data_completeness.desc(),
            ScreenerSnapshot.symbol.asc(),
        )
        rows = self.db.execute(query).scalars().all()

        results: list[ScreenerResult] = []
        seen_symbols: set[str] = set()

        for row in rows:
            symbol = row.symbol.upper()
            if symbol in seen_symbols:
                continue
            seen_symbols.add(symbol)

            if row.score < filters.min_score:
                continue
            if row.roe is not None and row.roe < filters.min_roe:
                continue
            if row.pe is not None and row.pe > filters.max_pe:
                continue
            if (
                row.debt_to_equity is not None
                and row.debt_to_equity > filters.max_debt_to_equity
            ):
                continue
            if (
                row.revenue_growth is not None
                and row.revenue_growth < filters.min_revenue_growth
            ):
                continue
            if (
                row.profit_growth is not None
                and row.profit_growth < filters.min_profit_growth
            ):
                continue
            if (
                row.market_cap is not None
                and row.market_cap < filters.min_market_cap * 10_000_000
            ):
                continue

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
                    peg=row.peg,
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
            if len(results) >= filters.limit:
                break

        snapshot_at = rows[0].snapshot_at if rows else None
        return int(total_universe), results, snapshot_at
