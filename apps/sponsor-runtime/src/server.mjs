import express from "express";

import { HTTPFacilitatorClient } from "@x402/core/server";
import { paymentMiddleware, x402ResourceServer } from "@x402/express";
import { registerExactSvmScheme } from "@x402/svm/exact/server";

import { sponsorConfig, validateSponsorRuntimeConfig } from "./config.mjs";
import { fundEscrow, refundEscrow, releaseEscrow } from "./alkahest.mjs";

validateSponsorRuntimeConfig();

const app = express();
app.use(express.json());

app.get("/health", async (_req, res) => {
  let browserWorkerHealthy = false;
  try {
    const response = await fetch(`${sponsorConfig.browserWorkerUrl}/health`);
    browserWorkerHealthy = response.ok;
  } catch {
    browserWorkerHealthy = false;
  }
  res.json({
    status: "ok",
    service: "sponsor-runtime",
    browser_worker_healthy: browserWorkerHealthy,
    x402_network: sponsorConfig.x402Network,
  });
});

app.post("/quote", async (req, res) => {
  const response = await fetch(`${sponsorConfig.browserWorkerUrl}/quote`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req.body),
  });
  const body = await response.json();
  res.status(response.status).json({
    ...body,
    worker_id: "unbrowse-browser-agent",
    capabilities: [...new Set([...(body.capabilities ?? []), "unbrowse", "x402", "alkahest"])],
  });
});

const facilitatorClient = new HTTPFacilitatorClient({ url: sponsorConfig.x402FacilitatorUrl });
const resourceServer = registerExactSvmScheme(new x402ResourceServer(facilitatorClient));

app.use(
  paymentMiddleware(
    {
      "POST /browse": {
        accepts: {
          scheme: "exact",
          price: sponsorConfig.x402PriceUsd,
          network: sponsorConfig.x402Network,
          payTo: sponsorConfig.x402PayTo,
        },
        description: "Paid browser execution via Unbrowse-backed worker",
      },
    },
    resourceServer,
    undefined,
    undefined,
    false,
  ),
);

app.post("/browse", async (req, res) => {
  const response = await fetch(`${sponsorConfig.browserWorkerUrl}/internal/browse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req.body),
  });
  const body = await response.json();
  res.status(response.status).json(body);
});

app.post("/settlement/fund", async (req, res) => {
  const result = await fundEscrow(req.body.task, req.body.quote);
  res.json(result);
});

app.post("/settlement/release", async (req, res) => {
  const result = await releaseEscrow(
    req.body.task,
    req.body.quote,
    req.body.verification,
    req.body.execution_result,
    req.body.funded_metadata,
  );
  res.json(result);
});

app.post("/settlement/refund", async (req, res) => {
  const result = await refundEscrow(
    req.body.task,
    req.body.quote,
    req.body.verification,
    req.body.execution_result,
    req.body.funded_metadata,
  );
  res.json(result);
});

app.listen(sponsorConfig.port, "127.0.0.1", () => {
  console.log(`sponsor-runtime listening on http://127.0.0.1:${sponsorConfig.port}`);
});
