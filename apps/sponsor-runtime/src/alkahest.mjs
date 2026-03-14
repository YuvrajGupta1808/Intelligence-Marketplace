import { encodeAbiParameters, http, parseAbiParameters, parseUnits, createWalletClient } from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { makeClient } from "alkahest-ts";

import { sponsorConfig } from "./config.mjs";

function makeAlkahestClient(privateKey) {
  if (!privateKey) {
    throw new Error("Missing Alkahest private key");
  }
  if (!sponsorConfig.alkahestRpcUrl) {
    throw new Error("Missing ALKAHEST_RPC_URL");
  }
  return makeClient(
    createWalletClient({
      account: privateKeyToAccount(privateKey),
      chain: sponsorConfig.alkahestChain,
      transport: http(sponsorConfig.alkahestRpcUrl),
    }),
  );
}

function makeDemand(client, task) {
  const innerDemand = encodeAbiParameters(
    parseAbiParameters("(string taskId,string allowedDomain,string targetUrl)"),
    [{ taskId: task.id, allowedDomain: task.allowed_domain, targetUrl: task.target_url }],
  );
  const oracleAddress = privateKeyToAccount(sponsorConfig.alkahestOraclePrivateKey).address;
  return {
    oracleAddress,
    demand: client.arbiters.general.trustedOracle.encodeDemand({
      oracle: oracleAddress,
      data: innerDemand,
    }),
  };
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function fundEscrow(task, quote) {
  const buyerClient = makeAlkahestClient(sponsorConfig.alkahestBuyerPrivateKey);
  const { oracleAddress, demand } = makeDemand(buyerClient, task);
  const expiration = BigInt(Math.floor(Date.now() / 1000) + sponsorConfig.alkahestExpirationSeconds);
  const escrow = await buyerClient.erc20.escrow.nonTierable.approveAndCreate(
    { address: sponsorConfig.alkahestUsdcAddress, value: parseUnits(String(quote.price_usdc), 6) },
    {
      arbiter: buyerClient.contractAddresses.trustedOracleArbiter,
      demand,
    },
    expiration,
  );

  return {
    settlement_mode: "alkahest",
    chain_name: sponsorConfig.alkahestChain.name,
    chain_id: String(sponsorConfig.alkahestChain.id),
    escrow_contract: buyerClient.contractAddresses.erc20EscrowObligation,
    arbiter_contract: buyerClient.contractAddresses.trustedOracleArbiter,
    oracle_address: oracleAddress,
    escrow_uid: escrow.attested.uid,
    fund_tx_hash: escrow.hash,
    demand,
    expiration_unix: expiration.toString(),
  };
}

export async function releaseEscrow(task, quote, verification, execution, fundedMetadata) {
  const workerClient = makeAlkahestClient(sponsorConfig.alkahestWorkerPrivateKey);
  const oracleClient = makeAlkahestClient(sponsorConfig.alkahestOraclePrivateKey);
  const fulfillment = await workerClient.stringObligation.doObligationJson(
    {
      task_id: task.id,
      final_url: execution.final_url,
      plan_name: execution.plan_name,
      price_found: execution.price_found,
      html_hash: execution.evidence.html_hash,
      verification_passed: verification.passed,
    },
    undefined,
    fundedMetadata.escrow_uid,
  );
  const arbitrationDecisionTx = await oracleClient.arbiters.general.trustedOracle.arbitrate(
    fulfillment.attested.uid,
    fundedMetadata.demand,
    true,
  );
  const collectTx = await workerClient.erc20.escrow.nonTierable.collect(
    fundedMetadata.escrow_uid,
    fulfillment.attested.uid,
  );
  return {
    ...fundedMetadata,
    oracle_decision: "approve",
    fulfillment_uid: fulfillment.attested.uid,
    fulfillment_tx_hash: fulfillment.hash,
    arbitration_decision_tx_hash: arbitrationDecisionTx,
    collect_tx_hash: collectTx,
  };
}

export async function refundEscrow(task, quote, verification, execution, fundedMetadata) {
  const buyerClient = makeAlkahestClient(sponsorConfig.alkahestBuyerPrivateKey);
  const workerClient = makeAlkahestClient(sponsorConfig.alkahestWorkerPrivateKey);
  const oracleClient = makeAlkahestClient(sponsorConfig.alkahestOraclePrivateKey);
  const fulfillment = await workerClient.stringObligation.doObligationJson(
    {
      task_id: task.id,
      final_url: execution.final_url,
      plan_name: execution.plan_name,
      price_found: execution.price_found,
      html_hash: execution.evidence.html_hash,
      verification_passed: verification.passed,
    },
    undefined,
    fundedMetadata.escrow_uid,
  );
  const arbitrationDecisionTx = await oracleClient.arbiters.general.trustedOracle.arbitrate(
    fulfillment.attested.uid,
    fundedMetadata.demand,
    false,
  );
  const expirationUnix = Number.parseInt(fundedMetadata.expiration_unix, 10) * 1000;
  const waitMs = Math.max(0, expirationUnix - Date.now() + 1000);
  if (waitMs > 0) {
    await sleep(waitMs);
  }
  const reclaimTx = await buyerClient.erc20.escrow.nonTierable.reclaimExpired(fundedMetadata.escrow_uid);
  return {
    ...fundedMetadata,
    oracle_decision: "reject",
    fulfillment_uid: fulfillment.attested.uid,
    fulfillment_tx_hash: fulfillment.hash,
    arbitration_decision_tx_hash: arbitrationDecisionTx,
    reclaim_tx_hash: reclaimTx,
  };
}
