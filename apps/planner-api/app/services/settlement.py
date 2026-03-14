from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from app.core.config import settings
from app.core.time import utc_now_iso
from app.models.schemas import QuotePayload, SettlementEventPayload, TaskPayload, VerificationResultPayload


@dataclass
class SettlementDecision:
    event_type: str
    metadata: dict[str, str]


class AppSettlementAdapter:
    def funded_event(self, task: TaskPayload, quote: QuotePayload) -> SettlementEventPayload:
        return SettlementEventPayload(
            task_id=task.id,
            event_type="funded",
            amount_usdc=quote.price_usdc,
            timestamp=utc_now_iso(),
            metadata={
                "settlement_mode": "app",
                "worker_id": quote.worker_id,
            },
        )

    def decide(self, task: TaskPayload, quote: QuotePayload, verification: VerificationResultPayload) -> SettlementDecision:
        event_type = "released" if verification.passed else "refunded"
        return SettlementDecision(
            event_type=event_type,
            metadata={
                "settlement_mode": "app",
                "worker_id": quote.worker_id,
                "passed": str(verification.passed).lower(),
            },
        )


class AlkahestSettlementAdapter:
    def _escrow_id(self, task: TaskPayload, quote: QuotePayload) -> str:
        payload = f"{task.id}:{task.target_url}:{quote.price_usdc}:{settings.alkahest_chain_id}"
        return hashlib.sha256(payload.encode()).hexdigest()

    def _demand_payload(self, task: TaskPayload) -> str:
        return json.dumps(
            {
                "allowed_domain": task.allowed_domain,
                "required_fields": task.required_fields,
                "deadline_seconds": task.deadline_seconds,
                "verification": "deterministic",
            },
            sort_keys=True,
        )

    def funded_event(self, task: TaskPayload, quote: QuotePayload) -> SettlementEventPayload:
        escrow_id = self._escrow_id(task, quote)
        return SettlementEventPayload(
            task_id=task.id,
            event_type="funded",
            amount_usdc=quote.price_usdc,
            timestamp=utc_now_iso(),
            metadata={
                "settlement_mode": "alkahest",
                "worker_id": quote.worker_id,
                "escrow_id": escrow_id,
                "chain_name": settings.alkahest_chain_name,
                "chain_id": str(settings.alkahest_chain_id),
                "escrow_contract": settings.alkahest_erc20_escrow_address,
                "arbiter_contract": settings.alkahest_trusted_oracle_arbiter_address,
                "oracle_address": settings.alkahest_oracle_address or "unconfigured",
                "demand_data": self._demand_payload(task),
            },
        )

    def decide(self, task: TaskPayload, quote: QuotePayload, verification: VerificationResultPayload) -> SettlementDecision:
        event_type = "released" if verification.passed else "refunded"
        return SettlementDecision(
            event_type=event_type,
            metadata={
                "settlement_mode": "alkahest",
                "worker_id": quote.worker_id,
                "passed": str(verification.passed).lower(),
                "escrow_id": self._escrow_id(task, quote),
                "arbiter_contract": settings.alkahest_trusted_oracle_arbiter_address,
                "oracle_address": settings.alkahest_oracle_address or "unconfigured",
                "oracle_decision": "approve" if verification.passed else "reject",
            },
        )


def build_settlement_adapter() -> AppSettlementAdapter | AlkahestSettlementAdapter:
    if settings.settlement_mode.lower() == "alkahest":
        return AlkahestSettlementAdapter()
    return AppSettlementAdapter()
