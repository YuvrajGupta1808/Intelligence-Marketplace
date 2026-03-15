"""
Yahoo Finance researcher and think tool for the deep research agent.
"""
from dotenv import load_dotenv
load_dotenv()

import subprocess
import sys

from langchain_core.tools import tool

from deep_research.config import PROJECT_ROOT


@tool
def live_finance_researcher(query: str):
    """
    Research live stock data using Yahoo Finance MCP.

    Use this tool to get:
    - Current stock prices and real-time market data
    - Latest financial news
    - Stock recommendations and analyst ratings
    - Option chains and expiration dates
    - Recent stock actions (splits, dividends)

    Args:
        query: The financial research question about current market data

    Returns:
        Research results from Yahoo Finance
    """
    escaped = (query or "").replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
    code = f"""
import asyncio
from deep_research.tools.yahoo_mcp import finance_research
asyncio.run(finance_research("{escaped}"))
"""
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    return result.stdout


@tool
def think_tool(reflection: str) -> str:
    """Tool for strategic reflection on research progress and decision-making.

    Use after each search to analyze results and plan next steps. When to use:
    - After receiving search results: What key information did I find?
    - Before deciding next steps: Do I have enough to answer comprehensively?
    - When assessing research gaps: What specific information am I still missing?

    Args:
        reflection: Your detailed reflection on research progress, findings, gaps, and next steps

    Returns:
        Confirmation that reflection was recorded.
    """
    return f"Reflection recorded: {reflection}"
