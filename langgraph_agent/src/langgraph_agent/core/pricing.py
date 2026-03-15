"""Per-tool and quote pricing (lamports)."""

import os

# Lamports per executor step (~0.005 SOL); override via env.
LAMPORTS_PER_STEP = int(os.getenv("TOOL_PRICE_LAMPORTS_WEB_SEARCH", "5000000"))
# Est. lamports per transfer (network fee) for tool payout.
LAMPORTS_TRANSFER_FEE = int(os.getenv("LAMPORTS_TRANSFER_FEE", "5000"))
# Platform fee (~0.01 SOL)
PLATFORM_FEE_LAMPORTS = int(os.getenv("PLATFORM_FEE_LAMPORTS", "10000000"))


def compute_quote_lamports(num_steps: int) -> int:
    """Total lamports user must pay: steps * (per_step + transfer_fee) + platform_fee."""
    per_step_total = LAMPORTS_PER_STEP + LAMPORTS_TRANSFER_FEE
    return num_steps * per_step_total + PLATFORM_FEE_LAMPORTS


def lamports_to_sol(lamports: int) -> float:
    """Convert lamports to SOL for display."""
    return lamports / 1_000_000_000
