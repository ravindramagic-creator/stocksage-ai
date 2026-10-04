from __future__ import annotations

from datetime import datetime, timezone
import math

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.market_snapshot import MarketSnapshot
from app.models.stock import Stock
from app.services.market_data.yahoo_fundamentals_provider import YahooFundamentalsProvider
from app.services.market_service import get_market_service


class MarketSnapshotService:
    """Incrementally build the complete scoring dataset in the background."""

    def __init__(self, db: Session, stale_minutes: int = 30):
        self.db = db
        self.stale_seconds = stale_minutes * 60
        self.market = get_market_service()
        self.yahoo_fundamentals = YahooFundamentalsProvider()

    @staticmethod
    def _number(value) -> float | None:
        try:
            value = float(value)
            return value if math.isfinite(value) else None
        except (TypeError, ValueError):
            return None

    @classmethod
    def _percent(cls, value) -> float | None:
        value = cls._number(value)
        if value is None:
            return None
        return value * 100 if abs(value) <= 1.5 else value

    @classmethod
    def _debt(cls, value) -> float | None:
        value = cls._number(value)
        if value is None:
            return None
        return value / 100 if abs(value) > 10 else value

    @classmethod
    def _rsi(cls, closes: list[float], period: int = 14) -> float | None:
        if len(closes) <= period:
            return None
        changes = [b - a for a, b in zip(closes[-period - 1:], closes[-period:])]
        gains = [max(change, 0.0) for change in changes]
        losses = [max(-change, 0.0) for change in changes]
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            return 100.0 if avg_gain else 50.0
        return 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)

    @staticmethod
    def _statement_value(statement, labels: tuple[str, ...]) -> float | None:
        if statement is None:
            return None

        for label in labels:
            try:
                if label not in statement.index:
                    continue
                row = statement.loc[label]
                if hasattr(row, "dropna"):
                    row = row.dropna()
                    if len(row) == 0:
                        continue
                    return float(row.iloc[0])
                return float(row)
            except (TypeError, ValueError, IndexError, KeyError):
                continue

        return None

    @classmethod
    def _calculate_roe(
        cls,
        info: dict,
        balance_sheet,
        financials,
    ) -> float | None:
        roe = cls._percent(info.get("returnOnEquity"))
        if roe is not None:
            return roe

        net_income = cls._statement_value(
            financials,
            ("Net Income", "Net Income Common Stockholders"),
        )
        equity = cls._statement_value(
            balance_sheet,
            (
                "Stockholders Equity",
                "Common Stock Equity",
                "Total Equity Gross Minority Interest",
            ),
        )

        if net_income is None or equity is None or equity <= 0:
            return None

        return (net_income / equity) * 100

    @classmethod
    def _calculate_roce(
        cls,
        info: dict,
        balance_sheet,
        financials,
    ) -> float | None:
        # Some Yahoo payloads expose ROCE directly. Prefer that when present.
        roce = cls._percent(
            info.get("returnOnCapitalEmployed")
        )
        if roce is not None:
            return roce

        ebit = cls._statement_value(
            financials,
            (
                "EBIT",
                "Operating Income",
                "Operating Income as Reported",
            ),
        )
        if ebit is None:
            ebitda = cls._statement_value(
                financials,
                ("EBITDA", "Normalized EBITDA"),
            )
            depreciation = cls._statement_value(
                financials,
                (
                    "Reconciled Depreciation",
                    "Depreciation And Amortization In Income Statement",
                    "Depreciation",
                ),
            )
            if ebitda is not None:
                ebit = ebitda - abs(depreciation or 0)

        total_assets = cls._statement_value(
            balance_sheet,
            ("Total Assets",),
        )
        current_liabilities = cls._statement_value(
            balance_sheet,
            (
                "Current Liabilities",
                "Total Current Liabilities",
            ),
        )

        if (
            ebit is None
            or total_assets is None
            or current_liabilities is None
        ):
            return None

        capital_employed = total_assets - current_liabilities
        if capital_employed <= 0:
            return None

        return (ebit / capital_employed) * 100

    @classmethod
    def _calculate_debt_to_equity(
        cls,
        info: dict,
        balance_sheet,
    ) -> float | None:
        debt = cls._debt(info.get("debtToEquity"))
        if debt is not None:
            return debt

        total_debt = cls._statement_value(
            balance_sheet,
            (
                "Total Debt",
                "Total Debt And Equity",
            ),
        )
        equity = cls._statement_value(
            balance_sheet,
            (
                "Stockholders Equity",
                "Common Stock Equity",
                "Total Equity Gross Minority Interest",
            ),
        )

        if total_debt is None or equity is None or equity <= 0:
            return None

        return total_debt / equity

    def _is_stale(self, row: MarketSnapshot | None, now: datetime) -> bool:
        if row is None or row.updated_at is None:
            return True
        updated = row.updated_at
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)

        age = (now - updated).total_seconds()

        # Revisit incomplete fundamental snapshots sooner so old missing ROE/ROCE
        # values do not stay in the screener for hours after a provider repair.
        fundamental_incomplete = row.roe is None or row.roce is None
        retry_window = min(self.stale_seconds, 60 * 60) if fundamental_incomplete else self.stale_seconds

        return age >= retry_window

    def _refresh_symbol(
        self,
        stock: Stock,
        row: MarketSnapshot,
        now: datetime,
    ) -> None:
        symbol = stock.symbol.upper()
        quote = self.market.get_quote(symbol)
        if quote is None:
            row.status = "unavailable"
            row.error = "No quote available from configured providers"
            row.updated_at = now
            return

        row.price = self._number(quote.price)
        row.status = "ok"
        row.error = None

        try:
            data = self.yahoo_fundamentals.get_snapshot_data(symbol)
            info = data.get("info", {})
            financials = data.get("financials")
            balance_sheet = data.get("balance_sheet")

            row.market_cap = self._number(info.get("marketCap"))
            row.pe = self._number(info.get("trailingPE"))
            row.pb = self._number(info.get("priceToBook"))
            row.roe = self._calculate_roe(
                info,
                balance_sheet,
                financials,
            )
            row.roce = self._calculate_roce(
                info,
                balance_sheet,
                financials,
            )
            row.debt_to_equity = self._calculate_debt_to_equity(
                info,
                balance_sheet,
            )
            row.revenue_growth = self._percent(info.get("revenueGrowth"))
            row.profit_growth = self._percent(info.get("earningsGrowth"))

            target = self._number(info.get("targetMeanPrice"))
            row.target_upside = (
                ((target / row.price) - 1) * 100
                if target and row.price
                else None
            )

            history = self.yahoo_fundamentals.get_history(symbol)
            closes = [
                self._number(value)
                for value in history.get("Close", []).tolist()
            ]
            closes = [value for value in closes if value is not None]

            if len(closes) >= 50:
                row.sma50 = sum(closes[-50:]) / 50
            if len(closes) >= 200:
                row.sma200 = sum(closes[-200:]) / 200

            row.rsi14 = self._rsi(closes)

            if len(closes) >= 2:
                lookback = min(126, len(closes) - 1)
                row.momentum_6m = (
                    closes[-1] / closes[-1 - lookback] - 1
                ) * 100

            if row.roe is None or row.roce is None:
                row.status = "partial"
                row.error = (
                    "ROE/ROCE unavailable after statement-based calculation"
                )
        except Exception as exc:
            # Preserve any good values already in the snapshot. A provider
            # outage must not erase usable historical scoring data.
            row.error = f"partial snapshot: {str(exc)[:900]}"
            if "cooling down" in str(exc).lower():
                row.status = "partial"

        row.updated_at = now

    def refresh_stale(self, limit: int = 50) -> int:
        now = datetime.now(timezone.utc)
        stocks = self.db.execute(
            select(Stock)
            .where(Stock.exchange == "NSE")
            .order_by(Stock.symbol)
        ).scalars().all()

        existing = {
            row.symbol.upper(): row
            for row in self.db.execute(select(MarketSnapshot)).scalars().all()
        }

        refreshed = 0
        for stock in stocks:
            if refreshed >= limit:
                break

            row = existing.get(stock.symbol.upper())
            if not self._is_stale(row, now):
                continue

            if row is None:
                row = MarketSnapshot(
                    symbol=stock.symbol.upper(),
                    status="pending",
                )
                self.db.add(row)

            try:
                self._refresh_symbol(stock, row, now)
            except Exception as exc:
                row.status = "error"
                row.error = str(exc)[:1000]
                row.updated_at = now

            refreshed += 1

        self.db.commit()
        return refreshed
