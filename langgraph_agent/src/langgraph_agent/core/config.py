"""Agent configuration (model, defaults, Solana)."""

import os

DEFAULT_RPC = "https://api.devnet.solana.com"


def get_model() -> str:
    """OpenAI model name from env or default."""
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def get_temperature() -> float:
    """LLM temperature from env or default."""
    try:
        return float(os.getenv("LANGGRAPH_AGENT_TEMPERATURE", "0"))
    except ValueError:
        return 0.0


def get_solana_rpc_url() -> str:
    """Solana RPC URL (devnet default)."""
    return os.getenv("SOLANA_RPC_URL", DEFAULT_RPC)


def get_solana_private_key() -> str | None:
    """Agent wallet private key (base58). Used for tool payouts."""
    return os.getenv("X402_SOLANA_PRIVATE_KEY") or os.getenv("SOLANA_PRIVATE_KEY")


def get_agent_payment_receiver() -> str | None:
    """Address where user sends quote payment (base58)."""
    return (
        os.getenv("SOLANA_PAY_TO")
        or os.getenv("X402_PAY_TO")
        or os.getenv("AGENT_PAYMENT_RECEIVER")
    )


def get_tool_payout_address() -> str | None:
    """Address that receives per-tool payouts (base58). Set TOOL_PAYOUT_ADDRESS in .env."""
    return os.getenv("TOOL_PAYOUT_ADDRESS")


def get_payment_poll_interval_sec() -> float:
    """Seconds between balance checks while waiting for payment."""
    try:
        return float(os.getenv("PAYMENT_POLL_INTERVAL_SEC", "5"))
    except ValueError:
        return 5.0


def get_payment_poll_max_wait_sec() -> float:
    """Max seconds to wait for payment before giving up."""
    try:
        return float(os.getenv("PAYMENT_POLL_MAX_WAIT_SEC", "300"))
    except ValueError:
        return 300.0
