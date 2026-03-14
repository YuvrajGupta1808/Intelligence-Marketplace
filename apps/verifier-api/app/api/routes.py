from fastapi import APIRouter

from app.models.schemas import HealthResponse, VerificationResultPayload, VerifyRequest
from app.rules.engine import verify


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="verifier-api")


@router.post("/verify", response_model=VerificationResultPayload)
def verify_route(request: VerifyRequest) -> VerificationResultPayload:
    return verify(request)

