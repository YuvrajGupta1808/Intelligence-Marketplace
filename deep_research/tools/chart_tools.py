"""
Chart tools for company research — price and performance charts like Morningstar/Value Line.

Returns Plotly figure as JSON so the UI (e.g. Streamlit) can render with st.plotly_chart.
"""

import json
from langchain_core.tools import tool

try:
    import plotly.graph_objects as go
    import plotly.io as pio
    import yfinance as yf
except ImportError:
    yf = None
    go = None
    pio = None


@tool
def generate_price_chart(ticker: str, period: str = "1y", title: str = ""):
    """
    Generate a stock price chart (OHLC close) for a ticker. Use this for company research reports.

    Call this when the user asks for a company/ticker report, stock chart, or price history.
    The chart is returned as data for the UI to render (e.g. in Streamlit). After calling,
    summarize the trend in your text response (e.g. "AAPL is up 15% over the past year...").

    Args:
        ticker: Stock ticker symbol (e.g. AAPL, MSFT, GOOGL).
        period: Yahoo Finance period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y. Default 1y.
        title: Optional chart title. If empty, uses "{ticker} Price ({period})".

    Returns:
        JSON string of a Plotly figure for the UI to render, or an error message if data failed.
    """
    if yf is None or go is None or pio is None:
        return json.dumps({"error": "Chart libraries not installed (plotly, yfinance)."})

    ticker = (ticker or "").strip().upper()
    if not ticker:
        return json.dumps({"error": "Ticker is required."})

    period = (period or "1y").strip().lower()
    valid_periods = ("1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y")
    if period not in valid_periods:
        period = "1y"

    try:
        obj = yf.Ticker(ticker)
        hist = obj.history(period=period, auto_adjust=True)
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch data for {ticker}: {e!s}"})

    if hist is None or hist.empty:
        return json.dumps({"error": f"No price data for {ticker} (period={period})."})

    chart_title = (title or f"{ticker} Price ({period})").strip()
    fig = go.Figure(
        data=[
            go.Scatter(
                x=hist.index.tolist(),
                y=hist["Close"].tolist(),
                mode="lines",
                name="Close",
                line=dict(color="#1f77b4", width=2),
            )
        ],
        layout=go.Layout(
            title=chart_title,
            xaxis=dict(title="Date", type="date"),
            yaxis=dict(title="Price ($)"),
            template="plotly_white",
            height=400,
            margin=dict(l=60, r=40, t=50, b=50),
        ),
    )
    return pio.to_json(fig)


def get_chart_tools():
    """Return list of chart tools for the agent."""
    return [generate_price_chart]
