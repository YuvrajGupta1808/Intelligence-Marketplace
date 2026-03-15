"""Solana Agent Kit (sendaifun/solana-agent-kit-py) init and LangChain tools."""

import os

from langgraph_agent.core.config import (
    get_solana_private_key,
    get_solana_rpc_url,
)

_solana_kit = None


def get_solana_kit():
    """Lazy-init SolanaAgentKit; requires X402_SOLANA_PRIVATE_KEY and RPC."""
    global _solana_kit
    if _solana_kit is not None:
        return _solana_kit
    try:
        from solana_agent_kit import SolanaAgentKit
    except ImportError:
        raise ImportError("pip install solana-agent-kit-py")
    key = get_solana_private_key()
    if not key:
        raise ValueError("X402_SOLANA_PRIVATE_KEY or SOLANA_PRIVATE_KEY required")
    rpc = get_solana_rpc_url()
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    _solana_kit = SolanaAgentKit(key, rpc, openai_key)
    return _solana_kit


def get_solana_tools():
    """Create LangChain tools from Solana Agent Kit (when enabled)."""
    try:
        from solana_agent_kit import create_solana_tools
    except ImportError:
        return []
    kit = get_solana_kit()
    return create_solana_tools(kit)
