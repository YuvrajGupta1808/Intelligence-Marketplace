import { baseSepolia } from "viem/chains";
import { SOLANA_DEVNET_CAIP2 } from "@x402/svm";

export const sponsorConfig = {
  appMode: process.env.APP_MODE ?? "demo",
  port: Number.parseInt(process.env.SPONSOR_RUNTIME_PORT ?? "8010", 10),
  browserWorkerUrl: process.env.BROWSER_WORKER_URL ?? "http://127.0.0.1:8002",
  x402FacilitatorUrl: process.env.X402_FACILITATOR_URL ?? "https://facilitator.x402.org",
  x402Network: process.env.X402_NETWORK_CAIP2 ?? SOLANA_DEVNET_CAIP2,
  x402PriceUsd: process.env.X402_PRICE_USD ?? "$0.06",
  x402PayTo: process.env.X402_PAY_TO ?? "",
  x402SolanaPrivateKey: process.env.X402_SOLANA_PRIVATE_KEY ?? "",
  alkahestRpcUrl: process.env.ALKAHEST_RPC_URL ?? "",
  alkahestUsdcAddress: process.env.ALKAHEST_USDC_ADDRESS ?? "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
  alkahestBuyerPrivateKey: process.env.ALKAHEST_BUYER_PRIVATE_KEY ?? "",
  alkahestWorkerPrivateKey: process.env.ALKAHEST_WORKER_PRIVATE_KEY ?? "",
  alkahestOraclePrivateKey: process.env.ALKAHEST_ORACLE_PRIVATE_KEY ?? "",
  alkahestExpirationSeconds: Number.parseInt(process.env.ALKAHEST_EXPIRATION_SECONDS ?? "30", 10),
  alkahestChain: baseSepolia,
};

export function validateSponsorRuntimeConfig() {
  if (sponsorConfig.appMode !== "real") return;
  const missing = [];
  if (!sponsorConfig.x402PayTo) missing.push("X402_PAY_TO");
  if (!sponsorConfig.x402SolanaPrivateKey) missing.push("X402_SOLANA_PRIVATE_KEY");
  if (!sponsorConfig.alkahestRpcUrl) missing.push("ALKAHEST_RPC_URL");
  if (!sponsorConfig.alkahestBuyerPrivateKey) missing.push("ALKAHEST_BUYER_PRIVATE_KEY");
  if (!sponsorConfig.alkahestWorkerPrivateKey) missing.push("ALKAHEST_WORKER_PRIVATE_KEY");
  if (!sponsorConfig.alkahestOraclePrivateKey) missing.push("ALKAHEST_ORACLE_PRIVATE_KEY");
  if (missing.length) {
    throw new Error(`Sponsor runtime real mode is not configured: ${missing.join(", ")}`);
  }
}
