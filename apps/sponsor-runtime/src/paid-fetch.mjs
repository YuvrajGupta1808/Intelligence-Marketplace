import process from "node:process";

import { base58 } from "@scure/base";
import { createKeyPairSignerFromBytes } from "@solana/kit";
import { decodePaymentResponseHeader, wrapFetchWithPaymentFromConfig } from "@x402/fetch";
import { ExactSvmScheme, SOLANA_DEVNET_CAIP2, toClientSvmSigner } from "@x402/svm";

const input = await new Promise((resolve, reject) => {
  let data = "";
  process.stdin.setEncoding("utf8");
  process.stdin.on("data", (chunk) => {
    data += chunk;
  });
  process.stdin.on("end", () => resolve(data));
  process.stdin.on("error", reject);
});

const payload = JSON.parse(input);
const signerBytes = base58.decode(process.env.X402_SOLANA_PRIVATE_KEY ?? "");
const keypair = await createKeyPairSignerFromBytes(signerBytes);
const signer = toClientSvmSigner(keypair);
const paidFetch = wrapFetchWithPaymentFromConfig(fetch, {
  schemes: [
    {
      network: process.env.X402_NETWORK_CAIP2 ?? SOLANA_DEVNET_CAIP2,
      client: new ExactSvmScheme(signer),
    },
  ],
});

const response = await paidFetch(payload.url, {
  method: payload.method,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(payload.json_body),
});
const paymentHeader = response.headers.get("PAYMENT-RESPONSE");
const body = await response.json();

process.stdout.write(
  JSON.stringify({
    body,
    payment_metadata: {
      payment_mode: "real",
      network: process.env.X402_NETWORK ?? "solana-devnet",
      payment_response_header: paymentHeader,
      payment_response: paymentHeader ? decodePaymentResponseHeader(paymentHeader) : null,
    },
  }),
);
