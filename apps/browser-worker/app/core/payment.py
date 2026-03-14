from __future__ import annotations

from typing import Protocol

from fastapi import HTTPException, Request

from app.core.config import settings


class PaymentGate(Protocol):
    async def challenge_or_continue(self, request: Request) -> None: ...


class MockPaymentGate:
    async def challenge_or_continue(self, request: Request) -> None:
        if request.headers.get("x-mock-payment") == "paid":
            return
        raise HTTPException(
            status_code=402,
            detail={
                "error": "payment_required",
                "payment_mode": "mock",
                "challenge": "mock-usdc-challenge",
                "network": "solana-devnet",
                "asset": "USDC",
            },
        )


class RealPaymentGate:
    async def challenge_or_continue(self, request: Request) -> None:
        payment_header = request.headers.get("x-x402-payment")
        if payment_header and payment_header == settings.x402_payment_token:
            return
        raise HTTPException(
            status_code=402,
            detail={
                "error": "payment_required",
                "payment_mode": "real",
                "challenge": "x402-solana-devnet-usdc",
                "network": settings.x402_network,
                "asset": settings.x402_asset,
                "facilitator_url": settings.x402_facilitator_url,
                "pay_to": settings.x402_pay_to or settings.worker_id,
            },
        )
