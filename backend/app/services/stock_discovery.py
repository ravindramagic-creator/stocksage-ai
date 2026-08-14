from dataclasses import dataclass

import yfinance as yf


@dataclass
class DiscoveredStock:
    symbol: str
    company_name: str
    exchange: str
    sector: str | None = None
    yahoo_symbol: str | None = None


class StockDiscoveryService:

    @staticmethod
    def search(
        query: str,
    ) -> list[DiscoveredStock]:

        query = query.strip()

        if not query:
            return []

        search = yf.Search(query)

        quotes = search.quotes

        results: list[DiscoveredStock] = []

        for quote in quotes:

            exchange = str(
                quote.get("exchange", "")
            ).upper()

            quote_type = str(
                quote.get("quoteType", "")
            ).upper()

            symbol = str(
                quote.get("symbol", "")
            ).upper()

            if not symbol:
                continue

            # We primarily want Indian NSE stocks.
            if (
                exchange not in {
                    "NSI",
                    "NSE",
                }
                and not symbol.endswith(".NS")
            ):
                continue

            if quote_type not in {
                "EQUITY",
            }:
                continue

            clean_symbol = symbol

            if clean_symbol.endswith(".NS"):
                clean_symbol = clean_symbol[:-3]

            company_name = (
                quote.get("longname")
                or quote.get("shortname")
                or clean_symbol
            )

            results.append(
                DiscoveredStock(
                    symbol=clean_symbol,
                    company_name=str(
                        company_name
                    ),
                    exchange="NSE",
                    yahoo_symbol=symbol,
                )
            )

        return results[:20]
