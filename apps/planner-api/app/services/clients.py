from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Protocol

import httpx

from app.core.config import settings
from app.models.schemas import ExecutionResultPayload, QuotePayload, TaskPayload, VerificationResultPayload


class WorkerClient(Protocol):
    async def quote(self, task: TaskPayload) -> QuotePayload: ...
    async def browse(self, task: TaskPayload) -> PaidExecution: ...


class VerifierClient(Protocol):
    async def verify(self, task: TaskPayload, result: ExecutionResultPayload) -> VerificationResultPayload: ...


class PaymentClient(Protocol):
    async def pay_and_request(self, method: str, url: str, json_body: dict) -> tuple[dict, dict]: ...


@dataclass
class PaidExecution:
    execution: ExecutionResultPayload
    payment_metadata: dict[str, object]


class MockPaymentClient:
    async def pay_and_request(self, method: str, url: str, json_body: dict) -> tuple[dict, dict]:
        async with httpx.AsyncClient(timeout=settings.service_timeout_sec) as client:
            response = await client.request(method, url, json=json_body)
            challenge_detail = {}
            if response.status_code == 402:
                challenge_detail = response.json().get("detail", {})
                response = await client.request(method, url, json=json_body, headers={"x-mock-payment": "paid"})
            response.raise_for_status()
            return response.json(), {
                "payment_mode": "mock",
                "challenge": str(challenge_detail.get("challenge", "mock-usdc-challenge")),
                "network": str(challenge_detail.get("network", settings.x402_network)),
                "asset": str(challenge_detail.get("asset", settings.x402_asset)),
            }


class RealPaymentClient:
    async def pay_and_request(self, method: str, url: str, json_body: dict) -> tuple[dict, dict]:
        helper = Path(settings.sponsor_runtime_dir).resolve() / "src" / "paid-fetch.mjs"
        env = os.environ.copy()
        env.setdefault("X402_NETWORK", settings.x402_network)
        env.setdefault("X402_NETWORK_CAIP2", "solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1")
        env.setdefault("X402_FACILITATOR_URL", settings.x402_facilitator_url)
        process = await asyncio.create_subprocess_exec(
            "node",
            str(helper),
            cwd=str(Path(settings.sponsor_runtime_dir).resolve()),
            env=env,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate(
            json.dumps({"method": method, "url": url, "json_body": json_body}).encode("utf-8")
        )
        if process.returncode != 0:
            raise RuntimeError(stderr.decode("utf-8") or "x402 paid fetch failed")
        payload = json.loads(stdout.decode("utf-8"))
        payment_metadata = payload.get("payment_metadata", {})
        payment_metadata.setdefault("facilitator_url", settings.x402_facilitator_url)
        payment_metadata.setdefault("asset", settings.x402_asset)
        return payload["body"], payment_metadata


class HttpSettlementClient:
    async def fund(self, task: TaskPayload, quote: QuotePayload) -> dict:
        async with httpx.AsyncClient(base_url=settings.sponsor_runtime_url, timeout=settings.service_timeout_sec) as client:
            response = await client.post("/settlement/fund", json={"task": task.model_dump(), "quote": quote.model_dump()})
            response.raise_for_status()
            return response.json()

    async def settle(
        self,
        task: TaskPayload,
        quote: QuotePayload,
        verification: VerificationResultPayload,
        execution: ExecutionResultPayload,
        funded_metadata: dict,
    ) -> dict:
        path = "/settlement/release" if verification.passed else "/settlement/refund"
        async with httpx.AsyncClient(base_url=settings.sponsor_runtime_url, timeout=settings.service_timeout_sec) as client:
            response = await client.post(
                path,
                json={
                    "task": task.model_dump(),
                    "quote": quote.model_dump(),
                    "verification": verification.model_dump(),
                    "execution_result": execution.model_dump(),
                    "funded_metadata": funded_metadata,
                },
            )
            response.raise_for_status()
            return response.json()


class HttpWorkerClient:
    def __init__(self, payment_client: PaymentClient) -> None:
        self.payment_client = payment_client

    async def quote(self, task: TaskPayload) -> QuotePayload:
        base_url = settings.sponsor_runtime_url if settings.payment_mode == "real" else settings.browser_worker_url
        async with httpx.AsyncClient(base_url=base_url, timeout=settings.service_timeout_sec) as client:
            response = await client.post(
                "/quote",
                json={
                    "task_id": task.id,
                    "task_type": task.task_type,
                    "target_url": task.target_url,
                    "allowed_domain": task.allowed_domain,
                    "required_fields": task.required_fields,
                },
            )
            response.raise_for_status()
            return QuotePayload.model_validate(response.json())

    async def browse(self, task: TaskPayload) -> PaidExecution:
        payload = {
            "task_id": task.id,
            "task_type": task.task_type,
            "target_url": task.target_url,
            "allowed_domain": task.allowed_domain,
            "required_fields": task.required_fields,
        }
        json_response, payment_metadata = await self.payment_client.pay_and_request(
            "POST", f"{settings.sponsor_runtime_url if settings.payment_mode == 'real' else settings.browser_worker_url}/browse", payload
        )
        return PaidExecution(
            execution=ExecutionResultPayload.model_validate(json_response),
            payment_metadata=payment_metadata,
        )


class HttpVerifierClient:
    async def verify(self, task: TaskPayload, result: ExecutionResultPayload) -> VerificationResultPayload:
        async with httpx.AsyncClient(base_url=settings.verifier_api_url, timeout=settings.service_timeout_sec) as client:
            response = await client.post(
                "/verify",
                json={"task": task.model_dump(), "execution_result": result.model_dump()},
            )
            response.raise_for_status()
            return VerificationResultPayload.model_validate(response.json())
