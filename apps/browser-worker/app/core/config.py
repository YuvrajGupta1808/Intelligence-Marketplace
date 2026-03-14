from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_ENV = Path(__file__).resolve().parents[4] / ".env"
LOCAL_ENV = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(str(ROOT_ENV), str(LOCAL_ENV)), extra="ignore")

    app_mode: str = "demo"
    payment_mode: str = "mock"
    artifacts_dir: str = "./artifacts"
    public_artifacts_base_url: str = "http://localhost:8002/artifacts"
    worker_id: str = "browser-1"
    x402_network: str = "solana-devnet"
    x402_asset: str = "USDC"
    x402_facilitator_url: str = "https://x402.org/facilitator"
    x402_pay_to: str = ""
    x402_payment_token: str = "solana-devnet-usdc-proof"
    quote_price_usdc: float = 0.06
    unbrowse_url: str = "http://127.0.0.1:6969"
    unbrowse_timeout_sec: float = 45.0

    def real_mode(self) -> bool:
        return self.app_mode.lower() == "real"

    def validate_runtime(self) -> None:
        if not self.real_mode():
            return
        missing: list[str] = []
        if self.payment_mode.lower() != "real":
            missing.append("PAYMENT_MODE=real")
        if not self.unbrowse_url:
            missing.append("UNBROWSE_URL")
        if missing:
            raise RuntimeError(f"Browser worker real mode is not configured: {', '.join(missing)}")

    def artifact_root(self) -> Path:
        return Path(self.artifacts_dir).resolve()


settings = Settings()
