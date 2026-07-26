"""Portfolio Research MCP server.

A FastMCP server exposing stock/portfolio research tools over Streamable HTTP.
Data comes from Yahoo Finance via ``portfolio.py`` (yfinance).

Run locally:
    python server.py
    # -> serves MCP at http://127.0.0.1:8000/mcp  and health at /health

On Render, the platform injects ``PORT``; the server binds to 0.0.0.0:$PORT.

Auth:
    If the ``MCP_AUTH_TOKEN`` environment variable is set, every request to the
    ``/mcp`` endpoint must send ``Authorization: Bearer <token>``. If it is
    unset, auth is disabled (convenient for local development). Always set it in
    production so your public URL is not open to the world.
"""

from __future__ import annotations

import os

from fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse

import portfolio

mcp: FastMCP = FastMCP(
    name="Stock Market Research Demo MCP By Muhammad Farjad Ali Raza",
    instructions=(
        "Tools for investment and stock-portfolio research using live Yahoo "
        "Finance data. Use get_quote/get_fundamentals for a single ticker, "
        "compare_tickers to rank several, get_price_history for trends, "
        "get_news for headlines, and analyze_portfolio to value a set of "
        "holdings and compute gain/loss and weights."
    ),
)


# --------------------------------------------------------------------------- #
# Tools — thin MCP wrappers around the portfolio data layer.
# --------------------------------------------------------------------------- #
@mcp.tool
def get_quote(ticker: str) -> dict:
    """Get the latest price snapshot for a stock ticker (e.g. "AAPL").

    Returns price, day change, volume, market cap and exchange.
    """
    return portfolio.get_quote(ticker)


@mcp.tool
def get_fundamentals(ticker: str) -> dict:
    """Get valuation fundamentals for a ticker.

    Includes P/E, EPS, dividend yield, beta, 52-week range, sector and the
    consensus analyst recommendation.
    """
    return portfolio.get_fundamentals(ticker)


@mcp.tool
def get_price_history(ticker: str, period: str = "1mo", interval: str = "1d") -> dict:
    """Get historical OHLC candles for a ticker.

    period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    interval: 1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo
    """
    return portfolio.get_price_history(ticker, period=period, interval=interval)


@mcp.tool
def get_news(ticker: str, limit: int = 5) -> dict:
    """Get recent news headlines (with links) for a ticker."""
    return portfolio.get_news(ticker, limit=limit)


@mcp.tool
def analyze_portfolio(holdings: list[dict]) -> dict:
    """Analyze a portfolio of holdings and compute value, gain/loss and weights.

    Each holding is an object: {"ticker": "AAPL", "shares": 10, "cost_basis": 150}
    where cost_basis is the per-share purchase price (optional). Returns a
    per-position breakdown plus portfolio-level totals.
    """
    return portfolio.analyze_portfolio(holdings)


@mcp.tool
def compare_tickers(tickers: list[str]) -> dict:
    """Compare several tickers side by side (price, P/E, yield, beta, rating)."""
    return portfolio.compare_tickers(tickers)


# --------------------------------------------------------------------------- #
# Bearer-token auth middleware (applied only to the /mcp path).
# --------------------------------------------------------------------------- #
class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Reject requests to /mcp that lack a valid bearer token.

    No-op when MCP_AUTH_TOKEN is unset (local dev).
    """

    async def dispatch(self, request: Request, call_next):
        token = os.environ.get("MCP_AUTH_TOKEN")
        if token and request.url.path.rstrip("/").endswith("/mcp"):
            header = request.headers.get("authorization", "")
            expected = f"Bearer {token}"
            if header != expected:
                return JSONResponse(
                    {"error": "Unauthorized: missing or invalid bearer token."},
                    status_code=401,
                )
        return await call_next(request)


def build_app():
    """Build the Starlette ASGI app: MCP over HTTP + a /health route + auth."""
    app = mcp.http_app()  # Streamable HTTP app, mounts MCP at /mcp

    async def health(_request: Request) -> PlainTextResponse:
        return PlainTextResponse("ok")

    app.add_route("/health", health, methods=["GET"])
    app.add_middleware(BearerAuthMiddleware)
    return app


# Exposed for ASGI servers (e.g. `uvicorn server:app`).
app = build_app()


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
