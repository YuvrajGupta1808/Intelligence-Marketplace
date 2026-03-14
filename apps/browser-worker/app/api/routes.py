from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.payment import MockPaymentGate, PaymentGate, RealPaymentGate
from app.models.schemas import BrowseRequest, BrowseResponse, HealthResponse, QuoteRequest, QuoteResponse
from app.services import build_quote, execute_browse


router = APIRouter()


def get_payment_gate() -> PaymentGate:
    return RealPaymentGate() if settings.payment_mode == "real" else MockPaymentGate()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="browser-worker")


@router.post("/quote", response_model=QuoteResponse)
def quote(request: QuoteRequest) -> QuoteResponse:
    return build_quote(request)


@router.post("/browse", response_model=BrowseResponse)
async def browse(
    request: BrowseRequest,
    raw_request: Request,
    payment_gate: PaymentGate = Depends(get_payment_gate),
) -> BrowseResponse:
    await payment_gate.challenge_or_continue(raw_request)
    return await execute_browse(request)


@router.post("/internal/browse", response_model=BrowseResponse)
async def internal_browse(request: BrowseRequest) -> BrowseResponse:
    return await execute_browse(request)


@router.get("/artifacts/{name}")
def artifact(name: str) -> FileResponse:
    path = settings.artifact_root() / name
    return FileResponse(Path(path))
