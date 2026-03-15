"""
Research graph: create_deep_agent with sub-agents and tools.
"""
import warnings
warnings.filterwarnings("ignore")

from dotenv import load_dotenv
load_dotenv()

import os
from datetime import datetime

from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent

from deep_research.tools import (
    live_finance_researcher,
    think_tool,
    get_chart_tools,
    get_unbrowse_tools,
    get_exa_tools,
    list_skills,
    load_skill,
    generate_research_pdf,
)
from deep_research.prompts import (
    DEEP_ORCHESTRATOR_INSTRUCTIONS,
    COMPANY_DATA_AGENT_INSTRUCTIONS,
    INDUSTRY_COMPETITORS_AGENT_INSTRUCTIONS,
    VALUATION_RISKS_AGENT_INSTRUCTIONS,
)

current_date = datetime.now().strftime("%Y-%m-%d")

base_tools = (
    [live_finance_researcher, think_tool]
    + get_chart_tools()
    + get_unbrowse_tools()
    + get_exa_tools()
    + [list_skills, load_skill, generate_research_pdf]
)

company_data_agent = {
    "name": "company-data-agent",
    "description": "Company and financial data: header, business description, historical financials, financial exhibits. Use for Yahoo, SEC/Unbrowse, and company-level data.",
    "system_prompt": COMPANY_DATA_AGENT_INSTRUCTIONS.format(date=current_date),
    "tools": base_tools,
}
industry_competitors_agent = {
    "name": "industry-competitors-agent",
    "description": "Industry and competitive positioning: market size, competitors, moat, peer set. Use for EXA and Unbrowse industry research.",
    "system_prompt": INDUSTRY_COMPETITORS_AGENT_INSTRUCTIONS.format(date=current_date),
    "tools": base_tools,
}
valuation_risks_agent = {
    "name": "valuation-risks-agent",
    "description": "Valuation, recommendation, risks, catalysts, management/ESG, disclosures. Use for Yahoo, EXA, and Unbrowse for valuation and risk data.",
    "system_prompt": VALUATION_RISKS_AGENT_INSTRUCTIONS.format(date=current_date),
    "tools": base_tools,
}

research_sub_agents = [company_data_agent, industry_competitors_agent, valuation_risks_agent]

model = ChatOpenAI(
    model=os.getenv("FIREWORKS_LLM_MODEL", "accounts/fireworks/models/llama-v3p1-70b-instruct"),
    base_url="https://api.fireworks.ai/inference/v1",
    api_key=os.getenv("FIREWORKS_API_KEY"),
)

tools = base_tools

agent = create_deep_agent(
    model=model,
    tools=tools,
    system_prompt=DEEP_ORCHESTRATOR_INSTRUCTIONS,
    subagents=research_sub_agents,
)
