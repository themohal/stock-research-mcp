"""Portfolio research data layer.

Thin wrappers around `yfinance` that return plain, JSON-serializable dicts.

Design notes:
- Every public function catches exceptions and returns a dict with an ``error``
  key instead of raising. yfinance scrapes Yahoo Finance and can rate-limit or
  return partial data, so callers (the MCP tools) should always get structured
  output they can hand back to an LLM.
- Nothing here imports FastMCP; this module is pure data access and can be unit
  tested on its own.
"""

from __future__ import annotations

from typing import Any

import yfinance as yf


def _round(value: Any, digits: int = 2) -> Any:
    """Round floats for clean output; pass through anything non-numeric/None."""
    if isinstance(value, (int, float)):
        return round(value, digits)
    return value


def _first(info: dict, *keys: str) -> Any:
    """Return the first present, non-None value among ``keys`` in ``info``."""
    for key in keys:
        value = info.get(key)
        if value is not None:
            return value
    return None


def get_quote(ticker: str) -> dict:
    """Latest price snapshot for a single ticker."""
    try:
        symbol = ticker.strip().upper()
        info = yf.Ticker(symbol).info

        price = _first(info, "currentPrice", "regularMarketPrice")
        prev_close = _first(info, "regularMarketPreviousClose", "previousClose")

        change = change_pct = None
        if isinstance(price, (int, float)) and isinstance(prev_close, (int, float)) and prev_close:
            change = price - prev_close
            change_pct = (change / prev_close) * 100

        if price is None:
            return {"error": f"No price data found for '{symbol}'. Is the ticker valid?"}

        return {
            "ticker": symbol,
            "name": info.get("shortName") or info.get("longName"),
            "price": _round(price),
            "currency": info.get("currency", "USD"),
            "previous_close": _round(prev_close),
            "change": _round(change),
            "change_percent": _round(change_pct),
            "day_high": _round(_first(info, "dayHigh", "regularMarketDayHigh")),
            "day_low": _round(_first(info, "dayLow", "regularMarketDayLow")),
            "volume": _first(info, "volume", "regularMarketVolume"),
            "market_cap": info.get("marketCap"),
            "exchange": info.get("fullExchangeName") or info.get("exchange"),
        }
    except Exception as exc:  # noqa: BLE001 - deliberately broad; return structured error
        return {"error": f"Failed to fetch quote for '{ticker}': {exc}"}


def get_fundamentals(ticker: str) -> dict:
    """Valuation and company fundamentals for a single ticker."""
    try:
        symbol = ticker.strip().upper()
        info = yf.Ticker(symbol).info

        if not info or _first(info, "currentPrice", "regularMarketPrice") is None:
            return {"error": f"No fundamentals found for '{symbol}'. Is the ticker valid?"}

        dividend_yield = info.get("dividendYield")
        # yfinance returns dividend yield as a fraction (0.005) — express as %.
        if isinstance(dividend_yield, (int, float)):
            dividend_yield = _round(dividend_yield * 100, 2)

        return {
            "ticker": symbol,
            "name": info.get("shortName") or info.get("longName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "market_cap": info.get("marketCap"),
            "trailing_pe": _round(info.get("trailingPE")),
            "forward_pe": _round(info.get("forwardPE")),
            "eps_trailing": _round(info.get("trailingEps")),
            "price_to_book": _round(info.get("priceToBook")),
            "dividend_yield_percent": dividend_yield,
            "beta": _round(info.get("beta")),
            "fifty_two_week_high": _round(info.get("fiftyTwoWeekHigh")),
            "fifty_two_week_low": _round(info.get("fiftyTwoWeekLow")),
            "analyst_target_price": _round(info.get("targetMeanPrice")),
            "recommendation": info.get("recommendationKey"),
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": f"Failed to fetch fundamentals for '{ticker}': {exc}"}


def get_price_history(ticker: str, period: str = "1mo", interval: str = "1d") -> dict:
    """Historical OHLC series for charting / trend analysis.

    ``period``: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    ``interval``: 1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo
    """
    try:
        symbol = ticker.strip().upper()
        frame = yf.Ticker(symbol).history(period=period, interval=interval)

        if frame.empty:
            return {"error": f"No history for '{symbol}' (period={period}, interval={interval})."}

        candles = [
            {
                "date": index.isoformat(),
                "open": _round(row["Open"]),
                "high": _round(row["High"]),
                "low": _round(row["Low"]),
                "close": _round(row["Close"]),
                "volume": int(row["Volume"]) if row["Volume"] == row["Volume"] else None,
            }
            for index, row in frame.iterrows()
        ]

        first_close = candles[0]["close"]
        last_close = candles[-1]["close"]
        period_return = None
        if isinstance(first_close, (int, float)) and first_close:
            period_return = _round(((last_close - first_close) / first_close) * 100)

        return {
            "ticker": symbol,
            "period": period,
            "interval": interval,
            "points": len(candles),
            "start_close": first_close,
            "end_close": last_close,
            "period_return_percent": period_return,
            "candles": candles,
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": f"Failed to fetch history for '{ticker}': {exc}"}


def get_news(ticker: str, limit: int = 5) -> dict:
    """Recent news headlines for a ticker."""
    try:
        symbol = ticker.strip().upper()
        raw = yf.Ticker(symbol).news or []

        articles = []
        for item in raw[: max(1, limit)]:
            # yfinance has shipped two shapes over time: flat, and nested under
            # a "content" key. Handle both.
            content = item.get("content", item)
            title = content.get("title")
            if not title:
                continue
            link = (
                content.get("canonicalUrl", {}).get("url")
                if isinstance(content.get("canonicalUrl"), dict)
                else content.get("link") or content.get("clickThroughUrl", {}).get("url")
                if isinstance(content.get("clickThroughUrl"), dict)
                else content.get("link")
            )
            provider = content.get("provider", {})
            articles.append(
                {
                    "title": title,
                    "publisher": provider.get("displayName") if isinstance(provider, dict) else content.get("publisher"),
                    "link": link,
                    "published": content.get("pubDate") or content.get("providerPublishTime"),
                }
            )

        if not articles:
            return {"ticker": symbol, "count": 0, "articles": [], "note": "No recent news returned."}

        return {"ticker": symbol, "count": len(articles), "articles": articles}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"Failed to fetch news for '{ticker}': {exc}"}


def analyze_portfolio(holdings: list[dict]) -> dict:
    """Analyze a portfolio of holdings.

    Each holding: ``{"ticker": str, "shares": float, "cost_basis": float}``
    where ``cost_basis`` is the per-share purchase price (optional).
    Returns per-holding valuation plus portfolio totals and weights.
    """
    try:
        if not holdings:
            return {"error": "No holdings provided. Expected a list of {ticker, shares, cost_basis}."}

        positions = []
        total_value = 0.0
        total_cost = 0.0

        for holding in holdings:
            symbol = str(holding.get("ticker", "")).strip().upper()
            shares = holding.get("shares")
            cost_basis = holding.get("cost_basis")

            if not symbol or not isinstance(shares, (int, float)):
                positions.append({"ticker": symbol or None, "error": "Missing ticker or numeric shares."})
                continue

            quote = get_quote(symbol)
            if "error" in quote:
                positions.append({"ticker": symbol, "error": quote["error"]})
                continue

            price = quote["price"]
            market_value = price * shares
            total_value += market_value

            position = {
                "ticker": symbol,
                "name": quote.get("name"),
                "shares": shares,
                "price": price,
                "market_value": _round(market_value),
                "day_change_percent": quote.get("change_percent"),
            }

            if isinstance(cost_basis, (int, float)):
                invested = cost_basis * shares
                gain = market_value - invested
                total_cost += invested
                position.update(
                    {
                        "cost_basis": cost_basis,
                        "invested": _round(invested),
                        "gain_loss": _round(gain),
                        "gain_loss_percent": _round((gain / invested) * 100) if invested else None,
                    }
                )

            positions.append(position)

        # Second pass: portfolio weights now that we know total_value.
        for position in positions:
            if "market_value" in position and total_value:
                position["weight_percent"] = _round((position["market_value"] / total_value) * 100)

        summary = {
            "total_market_value": _round(total_value),
            "holdings_count": len(holdings),
            "priced_positions": sum(1 for p in positions if "market_value" in p),
        }
        if total_cost:
            total_gain = total_value - total_cost
            summary.update(
                {
                    "total_invested": _round(total_cost),
                    "total_gain_loss": _round(total_gain),
                    "total_return_percent": _round((total_gain / total_cost) * 100),
                }
            )

        return {"summary": summary, "positions": positions}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"Failed to analyze portfolio: {exc}"}


def compare_tickers(tickers: list[str]) -> dict:
    """Side-by-side valuation snapshot for several tickers."""
    try:
        if not tickers:
            return {"error": "No tickers provided."}

        rows = []
        for ticker in tickers:
            fundamentals = get_fundamentals(ticker)
            quote = get_quote(ticker)
            if "error" in fundamentals and "error" in quote:
                rows.append({"ticker": str(ticker).upper(), "error": fundamentals["error"]})
                continue
            rows.append(
                {
                    "ticker": str(ticker).strip().upper(),
                    "name": fundamentals.get("name") or quote.get("name"),
                    "price": quote.get("price"),
                    "market_cap": fundamentals.get("market_cap"),
                    "trailing_pe": fundamentals.get("trailing_pe"),
                    "forward_pe": fundamentals.get("forward_pe"),
                    "dividend_yield_percent": fundamentals.get("dividend_yield_percent"),
                    "beta": fundamentals.get("beta"),
                    "recommendation": fundamentals.get("recommendation"),
                }
            )

        return {"count": len(rows), "comparison": rows}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"Failed to compare tickers: {exc}"}
