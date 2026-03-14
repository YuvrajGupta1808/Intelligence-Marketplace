from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_ENV = Path(__file__).resolve().parents[4] / ".env"
LOCAL_ENV = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(str(ROOT_ENV), str(LOCAL_ENV)), extra="ignore")

    app_mode: str = "demo"
    postgres_url: str = "sqlite:///./proof-of-browse.db"
    browser_worker_url: str = "http://localhost:8002"
    sponsor_runtime_url: str = "http://127.0.0.1:8010"
    verifier_api_url: str = "http://localhost:8003"
    planner_provider: str = "auto"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4.1-mini"
    openai_timeout_sec: float = 30.0
    openai_reasoning_effort: str = "low"
    payment_mode: str = "mock"
    x402_network: str = "solana-devnet"
    x402_asset: str = "USDC"
    x402_facilitator_url: str = "https://x402.org/facilitator"
    x402_payment_token: str = "solana-devnet-usdc-proof"
    settlement_mode: str = "app"
    alkahest_chain_name: str = "Base Sepolia"
    alkahest_chain_id: int = 84532
    alkahest_erc20_escrow_address: str = "0xfa76421cee6aee41adc7f6a475b9ef3776d500f0"
    alkahest_trusted_oracle_arbiter_address: str = "0x361e0950534f4a54a39f8c4f1f642c323f6e66b9"
    alkahest_oracle_address: str = ""
    sponsor_runtime_dir: str = "../sponsor-runtime"
    service_timeout_sec: float = 30.0
    temporal_target: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "proof-of-browse"
    temporal_ui_url: str = "http://localhost:8088"

    def real_mode(self) -> bool:
        return self.app_mode.lower() == "real"

    def validate_runtime(self) -> None:
        if not self.real_mode():
            return
        missing: list[str] = []
        if self.planner_provider.lower() != "openai":
            missing.append("PLANNER_PROVIDER=openai")
        if not self.openai_api_key:
            missing.append("OPENAI_API_KEY")
        if self.payment_mode.lower() != "real":
            missing.append("PAYMENT_MODE=real")
        if self.settlement_mode.lower() != "alkahest":
            missing.append("SETTLEMENT_MODE=alkahest")
        if self.postgres_url.startswith("sqlite"):
            missing.append("POSTGRES_URL must point to Postgres in real mode")
        if not self.temporal_target:
            missing.append("TEMPORAL_TARGET")
        if missing:
            raise RuntimeError(f"Planner real mode is not configured: {', '.join(missing)}")


settings = Settings()
