export function explorerUrl(address: string, cluster: string): string {
  return `https://explorer.solana.com/address/${address}?cluster=${cluster}`;
}

export function explorerTxUrl(signature: string, cluster: string): string {
  return `https://explorer.solana.com/tx/${signature}?cluster=${cluster}`;
}

export type PaymentRequiredResponse = {
  error: string;
  message: string;
  quote_lamports: number;
  quote_sol: number;
  receiver: string;
  network: string;
  how_to_pay: string;
  plan?: string[];
};

export type RunSuccessResponse = {
  final_answer: string;
  plan: string[];
  tool_call_log: Array<{ tool?: string; amount_lamports?: number; tx?: string }>;
};

export type RunResult =
  | { kind: "payment_required"; data: PaymentRequiredResponse }
  | { kind: "success"; data: RunSuccessResponse }
  | { kind: "error"; status: number; message: string };

export async function runAgent(
  query: string,
  options?: { paymentSignature?: string; quoteLamports?: number }
): Promise<RunResult> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
  };
  if (options?.paymentSignature) {
    headers["Payment-Signature"] = options.paymentSignature;
    if (options.quoteLamports != null) {
      headers["X-Quote-Lamports"] = String(options.quoteLamports);
    }
  }

  const res = await fetch("/api/run", {
    method: "POST",
    headers,
    body: JSON.stringify({ query }),
  });
  const data = await res.json().catch(() => ({}));

  if (res.status === 402) {
    return { kind: "payment_required", data: data as PaymentRequiredResponse };
  }
  if (res.ok) {
    return { kind: "success", data: data as RunSuccessResponse };
  }
  return {
    kind: "error",
    status: res.status,
    message: (data.detail ?? data.message ?? res.statusText) as string,
  };
}
