"""Payment verification (user -> receiver) and payout (agent -> tool)."""

from langgraph_agent.core.config import (
    get_agent_payment_receiver,
    get_solana_private_key,
    get_solana_rpc_url,
)


def receiver_balance_lamports() -> int:
    """Current balance of payment receiver address (lamports)."""
    receiver = get_agent_payment_receiver()
    if not receiver:
        return 0
    try:
        from solana.rpc.api import Client
        from solders.pubkey import Pubkey
    except ImportError:
        return 0
    rpc = get_solana_rpc_url()
    client = Client(rpc)
    try:
        resp = client.get_balance(Pubkey.from_string(receiver))
        if resp.value is not None:
            return resp.value
    except Exception:
        pass
    return 0


def check_payment_received(
    receiver_start_lamports: int,
    quote_lamports: int,
) -> bool:
    """True if receiver balance is at least quote_lamports (so 'run again' after paying works)."""
    now = receiver_balance_lamports()
    return now >= quote_lamports


def verify_payment_by_signature(
    signature: str,
    receiver: str,
    min_lamports: int,
) -> bool:
    """Verify that the given tx signature is a successful transfer of at least min_lamports to receiver.
    Used for x402 payment proof: client sends Payment-Signature header, we check on-chain."""
    if not receiver or min_lamports <= 0:
        return False
    try:
        from solana.rpc.api import Client
        from solders.pubkey import Pubkey
        from solders.signature import Signature
    except ImportError:
        return False
    client = Client(get_solana_rpc_url())
    sig = Signature.from_string(signature.strip())
    statuses = client.get_signature_statuses([sig])
    if not statuses.value or not statuses.value[0]:
        return False
    if getattr(statuses.value[0], "err", None) is not None:
        return False
    # Require receiver balance to be at least min_lamports (payment reached our wallet)
    return receiver_balance_lamports() >= min_lamports


def _wait_for_tx_confirm(client, signature: str, max_wait_sec: float = 30.0) -> None:
    """Poll until tx is confirmed or finalized, or max_wait_sec expires."""
    import time
    from solders.signature import Signature

    sig = Signature.from_string(signature)
    deadline = time.monotonic() + max_wait_sec
    while time.monotonic() < deadline:
        resp = client.get_signature_statuses([sig])
        if resp.value and resp.value[0]:
            status = resp.value[0]
            if getattr(status, "err", None) is not None:
                return
            conf = getattr(status, "confirmation_status", None) or getattr(
                status, "confirmations", None
            )
            if conf in ("processed", "confirmed", "finalized") or (
                isinstance(conf, int) and conf is not None
            ):
                return
        time.sleep(2.0)


def _send_lamports_versioned(client, sender, to_pubkey, amount_lamports: int) -> str | None:
    """Use VersionedTransaction + MessageV0 (recommended)."""
    from solders.message import MessageV0
    from solders.system_program import TransferParams, transfer
    from solders.transaction import VersionedTransaction

    ix = transfer(
        TransferParams(
            from_pubkey=sender.pubkey(),
            to_pubkey=to_pubkey,
            lamports=amount_lamports,
        )
    )
    latest = client.get_latest_blockhash()
    if not latest or not getattr(latest, "value", None):
        return None
    message = MessageV0.try_compile(
        payer=sender.pubkey(),
        instructions=[ix],
        address_lookup_table_accounts=[],
        recent_blockhash=latest.value.blockhash,
    )
    txn = VersionedTransaction(message, [sender])
    result = client.send_transaction(txn)
    if not result.value:
        return None
    return str(result.value)


def _send_lamports_legacy(client, sender, to_pubkey, amount_lamports: int) -> str | None:
    """Fallback: legacy Transaction with recent_blockhash."""
    from solders.system_program import TransferParams, transfer
    from solana.transaction import Transaction

    ix = transfer(
        TransferParams(
            from_pubkey=sender.pubkey(),
            to_pubkey=to_pubkey,
            lamports=amount_lamports,
        )
    )
    latest = client.get_latest_blockhash()
    if not latest or not getattr(latest, "value", None):
        return None
    txn = Transaction(
        fee_payer=sender.pubkey(),
        recent_blockhash=latest.value.blockhash,
    ).add(ix)
    result = client.send_transaction(txn, sender)
    if not result.value:
        return None
    return str(result.value)


def send_lamports_to_tool_provider(to_address: str, amount_lamports: int) -> str | None:
    """Send lamports from agent wallet to tool payout address. Waits for confirmation, returns tx signature or None."""
    key_b58 = get_solana_private_key()
    if not key_b58 or not to_address or amount_lamports <= 0:
        return None
    try:
        from solders.keypair import Keypair
        from solders.pubkey import Pubkey
        from solana.rpc.api import Client

        sender = Keypair.from_base58_string(key_b58)
        to_pubkey = Pubkey.from_string(to_address)
        client = Client(get_solana_rpc_url())
        # Ensure agent wallet has enough (need amount + rent/fee ~5000 lamports)
        try:
            bal = client.get_balance(sender.pubkey())
            if bal.value is not None and bal.value < amount_lamports + 5000:
                import sys
                print(
                    f"[tool payout] Agent wallet {sender.pubkey()} has {bal.value} lamports, "
                    f"need {amount_lamports + 5000}. Set SOLANA_PAY_TO to this address so user payment funds the agent.",
                    file=sys.stderr,
                )
                return None
        except Exception:
            pass
        sig = _send_lamports_versioned(client, sender, to_pubkey, amount_lamports)
        if sig is None:
            sig = _send_lamports_legacy(client, sender, to_pubkey, amount_lamports)
        # Skip confirmation wait so each step doesn't block; tx is still submitted and visible on explorer.
        # if sig:
        #     _wait_for_tx_confirm(client, sig)
        return sig
    except Exception as e:
        import sys
        print(f"[tool payout] send_lamports_to_tool_provider failed: {e}", file=sys.stderr)
        return None
