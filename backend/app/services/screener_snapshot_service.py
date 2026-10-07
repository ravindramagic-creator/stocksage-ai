from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from app.models.market_snapshot import MarketSnapshot
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
                    rsi_weekly=result.rsi_weekly,
                    rsi_monthly=result.rsi_monthly,
                    momentum_3m=result.momentum_3m,
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
        mode: str = "combined",
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

        # Technical indicators can be refreshed more frequently than the
        # persisted ranking snapshot. Prefer the latest MarketSnapshot values
        # for the configurable technical gate, falling back to the persisted
        # screener snapshot when necessary.
        technical = MarketSnapshot

        live_price = func.coalesce(technical.price, ScreenerSnapshot.price)
        live_sma50 = func.coalesce(technical.sma50, ScreenerSnapshot.sma50)
        live_sma200 = func.coalesce(technical.sma200, ScreenerSnapshot.sma200)
        live_daily_rsi = func.coalesce(technical.rsi14, ScreenerSnapshot.rsi14)
        live_weekly_rsi = func.coalesce(
            technical.rsi_weekly,
            ScreenerSnapshot.rsi_weekly,
        )
        live_monthly_rsi = func.coalesce(
            technical.rsi_monthly,
            ScreenerSnapshot.rsi_monthly,
        )
        live_momentum_3m = func.coalesce(
            technical.momentum_3m,
            ScreenerSnapshot.momentum_3m,
        )
        live_momentum_6m = func.coalesce(
            technical.momentum_6m,
            ScreenerSnapshot.momentum_6m,
        )

        market_cap_floor = filters.min_market_cap * 10_000_000
        mode = mode.lower()
        if mode not in {"combined", "fundamental", "technical"}:
            raise ValueError("mode must be combined, fundamental, or technical")

        technical = MarketSnapshot

        live_price = func.coalesce(technical.price, ScreenerSnapshot.price)
        live_sma50 = func.coalesce(technical.sma50, ScreenerSnapshot.sma50)
        live_sma200 = func.coalesce(technical.sma200, ScreenerSnapshot.sma200)
        live_daily_rsi = func.coalesce(technical.rsi14, ScreenerSnapshot.rsi14)
        live_weekly_rsi = func.coalesce(
            technical.rsi_weekly,
            ScreenerSnapshot.rsi_weekly,
        )
        live_monthly_rsi = func.coalesce(
            technical.rsi_monthly,
            ScreenerSnapshot.rsi_monthly,
        )
        live_momentum_3m = func.coalesce(
            technical.momentum_3m,
            ScreenerSnapshot.momentum_3m,
        )
        live_momentum_6m = func.coalesce(
            technical.momentum_6m,
            ScreenerSnapshot.momentum_6m,
        )

        conditions = []

        if mode in {"combined", "fundamental"}:
            conditions.extend(
                [
                    ScreenerSnapshot.roe.is_not(None),
                    ScreenerSnapshot.roce.is_not(None),
                    ScreenerSnapshot.pe.is_not(None),
                    ScreenerSnapshot.pe > 0,
                    ScreenerSnapshot.roe >= filters.min_roe,
                    ScreenerSnapshot.pe <= filters.max_pe,
                    ScreenerSnapshot.revenue_growth.is_not(None),
                    ScreenerSnapshot.revenue_growth >= filters.min_revenue_growth,
                    ScreenerSnapshot.profit_growth.is_not(None),
                    ScreenerSnapshot.profit_growth >= filters.min_profit_growth,
                    or_(
                        ScreenerSnapshot.debt_to_equity.is_(None),
                        ScreenerSnapshot.debt_to_equity <= filters.max_debt_to_equity,
                    ),
                    or_(
                        ScreenerSnapshot.market_cap.is_(None),
                        ScreenerSnapshot.market_cap >= market_cap_floor,
                    ),
                ]
            )

        if mode in {"combined", "technical"}:
            conditions.extend(
                [
                    live_price.is_not(None),
                    live_sma50.is_not(None),
                    live_sma200.is_not(None),
                    live_daily_rsi.is_not(None),
                    live_weekly_rsi.is_not(None),
                    live_monthly_rsi.is_not(None),
                    live_momentum_3m.is_not(None),
                    live_momentum_6m.is_not(None),
                    live_daily_rsi > filters.min_daily_rsi,
                    live_weekly_rsi > filters.min_weekly_rsi,
                    live_monthly_rsi > filters.min_monthly_rsi,
                    live_price > live_sma50,
                    live_sma50 > live_sma200,
                    live_momentum_3m > filters.min_momentum_3m,
                    live_momentum_6m > filters.min_momentum_6m,
                ]
            )

        score_column = (
            ScreenerSnapshot.technical_score
            if mode == "technical"
            else ScreenerSnapshot.fundamental_score
            if mode == "fundamental"
            else ScreenerSnapshot.score
        )

        conditions.insert(0, score_column.is_not(None))
        conditions.insert(0, score_column >= filters.min_score)

        query = (
            select(ScreenerSnapshot, technical)
            .outerjoin(
                technical,
                technical.symbol == ScreenerSnapshot.symbol,
            )
            .where(*conditions)
            .order_by(
                score_column.desc(),
                ScreenerSnapshot.data_completeness.desc(),
                ScreenerSnapshot.symbol.asc(),
            )
            .limit(filters.limit)
        )

        rows = self.db.execute(query).all()

        # Do not mix the two analyses. Fundamental mode uses only fundamental
        # quality/valuation/earnings filters; technical mode uses only price,
        # trend, RSI and momentum filters.
        if not rows and mode == "combined":
            fallback_conditions = [
                ScreenerSnapshot.score >= filters.min_score,
                ScreenerSnapshot.roe.is_not(None),
                ScreenerSnapshot.roce.is_not(None),
                ScreenerSnapshot.pe.is_not(None),
                ScreenerSnapshot.pe > 0,
                live_price.is_not(None),
                live_sma50.is_not(None),
                live_sma200.is_not(None),
                live_daily_rsi.is_not(None),
                live_weekly_rsi.is_not(None),
                live_monthly_rsi.is_not(None),
                live_momentum_3m.is_not(None),
                live_momentum_6m.is_not(None),
                ScreenerSnapshot.roe >= filters.min_roe,
                ScreenerSnapshot.pe <= filters.max_pe,
                ScreenerSnapshot.revenue_growth.is_not(None),
                ScreenerSnapshot.revenue_growth >= filters.min_revenue_growth,
                ScreenerSnapshot.profit_growth.is_not(None),
                ScreenerSnapshot.profit_growth >= filters.min_profit_growth,
                or_(
                    ScreenerSnapshot.debt_to_equity.is_(None),
                    ScreenerSnapshot.debt_to_equity <= filters.max_debt_to_equity,
                ),
                or_(
                    ScreenerSnapshot.market_cap.is_(None),
                    ScreenerSnapshot.market_cap >= market_cap_floor,
                ),
            ]
            fallback_query = (
                select(ScreenerSnapshot, technical)
                .outerjoin(
                    technical,
                    technical.symbol == ScreenerSnapshot.symbol,
                )
                .where(*fallback_conditions)
                .order_by(
                    ScreenerSnapshot.score.desc(),
                    ScreenerSnapshot.data_completeness.desc(),
                    ScreenerSnapshot.symbol.asc(),
                )
                .limit(filters.limit)
            )
            rows = self.db.execute(fallback_query).all()

        results: list[ScreenerResult] = []

        for row, technical_row in rows:
            if mode == "technical":
                display_score = row.technical_score or 0
                display_verdict = (
                    "STRONG TECHNICAL"
                    if display_score >= 85
                    else "TECHNICAL BUY"
                    if display_score >= 70
                    else "TECHNICAL WATCH"
                )
            elif mode == "fundamental":
                display_score = row.fundamental_score or 0
                display_verdict = (
                    "STRONG FUNDAMENTAL"
                    if display_score >= 85
                    else "FUNDAMENTAL BUY"
                    if display_score >= 70
                    else "FUNDAMENTAL WATCH"
                )
            else:
                display_score = row.score
                display_verdict = row.verdict

            results.append(
                ScreenerResult(
                    rank=len(results) + 1,
                    symbol=row.symbol,
                    company_name=row.company_name,
                    sector=row.sector,
                    score=display_score,
                    verdict=display_verdict,
                    data_completeness=row.data_completeness,
                    price=(
                        technical_row.price
                        if technical_row and technical_row.price is not None
                        else row.price
                    ),
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
                    sma50=(
                        technical_row.sma50
                        if technical_row and technical_row.sma50 is not None
                        else row.sma50
                    ),
                    sma200=(
                        technical_row.sma200
                        if technical_row and technical_row.sma200 is not None
                        else row.sma200
                    ),
                    rsi14=(
                        technical_row.rsi14
                        if technical_row and technical_row.rsi14 is not None
                        else row.rsi14
                    ),
                    rsi_weekly=(
                        technical_row.rsi_weekly
                        if technical_row and technical_row.rsi_weekly is not None
                        else row.rsi_weekly
                    ),
                    rsi_monthly=(
                        technical_row.rsi_monthly
                        if technical_row and technical_row.rsi_monthly is not None
                        else row.rsi_monthly
                    ),
                    momentum_3m=(
                        technical_row.momentum_3m
                        if technical_row and technical_row.momentum_3m is not None
                        else row.momentum_3m
                    ),
                    momentum_6m=(
                        technical_row.momentum_6m
                        if technical_row and technical_row.momentum_6m is not None
                        else row.momentum_6m
                    ),
                    target_upside=row.target_upside,
                    analyst_beat_rate=row.analyst_beat_rate,
                    fundamental_score=row.fundamental_score,
                    valuation_score=row.valuation_score,
                    technical_score=row.technical_score,
                    analyst_score=row.analyst_score,
                )
            )

        technical_rows = [
            technical_row
            for _, technical_row in rows
            if technical_row is not None and technical_row.updated_at is not None
        ]

        snapshot_at = (
            technical_rows[0].updated_at
            if technical_rows
            else rows[0][0].snapshot_at
            if rows
            else None
        )

        return (
            int(total_universe),
            results,
            snapshot_at,
        )
