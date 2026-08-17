from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.financial_result import FinancialResult


class FinancialResultRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        symbol: str,
        company_name: str | None,
        period_ended: date,
        period_type: str | None,
        consolidated: bool,

        # -----------------------------------------------------
        # Revenue
        # -----------------------------------------------------

        revenue,
        revenue_yoy,
        revenue_qoq,
        revenue_estimate=None,
        revenue_surprise_pct=None,
        revenue_result: str | None = None,

        # -----------------------------------------------------
        # EBITDA
        # -----------------------------------------------------

        ebitda=None,
        ebitda_yoy=None,
        ebitda_qoq=None,
        ebitda_estimate=None,
        ebitda_surprise_pct=None,
        ebitda_result: str | None = None,

        # -----------------------------------------------------
        # PAT / Net Profit
        # -----------------------------------------------------

        pat=None,
        pat_yoy=None,
        pat_qoq=None,
        pat_estimate=None,
        pat_surprise_pct=None,
        pat_result: str | None = None,

        # -----------------------------------------------------
        # EPS
        # -----------------------------------------------------

        eps=None,
        eps_yoy=None,
        eps_estimate=None,
        eps_surprise_pct=None,
        eps_result: str | None = None,

        # -----------------------------------------------------
        # Overall result
        # -----------------------------------------------------

        overall_result: str | None = None,

        # -----------------------------------------------------
        # Other information
        # -----------------------------------------------------

        market_view: str | None = None,
        summary: str | None = None,
        source: str | None = None,
        source_url: str | None = None,
        broadcast_date=None,
    ) -> FinancialResult:

        result = FinancialResult(
            symbol=symbol.upper(),
            company_name=company_name,
            period_ended=period_ended,
            period_type=period_type,
            consolidated=consolidated,

            # -------------------------------------------------
            # Revenue
            # -------------------------------------------------

            revenue=revenue,
            revenue_yoy=revenue_yoy,
            revenue_qoq=revenue_qoq,
            revenue_estimate=revenue_estimate,
            revenue_surprise_pct=revenue_surprise_pct,
            revenue_result=revenue_result,

            # -------------------------------------------------
            # EBITDA
            # -------------------------------------------------

            ebitda=ebitda,
            ebitda_yoy=ebitda_yoy,
            ebitda_qoq=ebitda_qoq,
            ebitda_estimate=ebitda_estimate,
            ebitda_surprise_pct=ebitda_surprise_pct,
            ebitda_result=ebitda_result,

            # -------------------------------------------------
            # PAT
            # -------------------------------------------------

            pat=pat,
            pat_yoy=pat_yoy,
            pat_qoq=pat_qoq,
            pat_estimate=pat_estimate,
            pat_surprise_pct=pat_surprise_pct,
            pat_result=pat_result,

            # -------------------------------------------------
            # EPS
            # -------------------------------------------------

            eps=eps,
            eps_yoy=eps_yoy,
            eps_estimate=eps_estimate,
            eps_surprise_pct=eps_surprise_pct,
            eps_result=eps_result,

            # -------------------------------------------------
            # Overall
            # -------------------------------------------------

            overall_result=overall_result,

            # -------------------------------------------------
            # Other
            # -------------------------------------------------

            market_view=market_view,
            summary=summary,

            source=source,
            source_url=source_url,

            broadcast_date=broadcast_date,
        )

        self.db.add(result)
        self.db.flush()

        return result

    # =========================================================
    # Get by period
    # =========================================================

    def get_by_period(
        self,
        symbol: str,
        period: date,
    ) -> FinancialResult | None:

        statement = (
            select(FinancialResult)
            .where(
                FinancialResult.symbol
                == symbol.upper(),
                FinancialResult.period_ended
                == period,
            )
            .limit(1)
        )

        return self.db.scalars(
            statement
        ).first()

    # =========================================================
    # Get latest result
    # =========================================================

    def get_latest(
        self,
        symbol: str,
    ) -> FinancialResult | None:

        statement = (
            select(FinancialResult)
            .where(
                FinancialResult.symbol
                == symbol.upper()
            )
            .order_by(
                FinancialResult.period_ended.desc()
            )
            .limit(1)
        )

        return self.db.scalars(
            statement
        ).first()

    # =========================================================
    # Get recent results
    # =========================================================

    def get_recent(
        self,
        symbol: str | None = None,
        limit: int = 20,
    ) -> list[FinancialResult]:

        statement = select(
            FinancialResult
        )

        if symbol:
            statement = statement.where(
                FinancialResult.symbol
                == symbol.upper()
            )

        statement = (
            statement
            .order_by(
                FinancialResult.period_ended.desc()
            )
            .limit(limit)
        )

        return list(
            self.db.scalars(
                statement
            ).all()
        )

    # =========================================================
    # Get all results
    # =========================================================

    def get_all(
        self,
        symbol: str | None = None,
    ) -> list[FinancialResult]:

        statement = select(
            FinancialResult
        )

        if symbol:
            statement = statement.where(
                FinancialResult.symbol
                == symbol.upper()
            )

        statement = statement.order_by(
            FinancialResult.period_ended.desc()
        )

        return list(
            self.db.scalars(
                statement
            ).all()
        )
