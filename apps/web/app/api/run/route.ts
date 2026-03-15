import { NextRequest, NextResponse } from "next/server";

const X402_API_URL = process.env.X402_API_URL || "http://127.0.0.1:8000";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const query = typeof body?.query === "string" ? body.query.trim() : "";
    if (!query) {
      return NextResponse.json(
        { detail: "query is required" },
        { status: 400 }
      );
    }

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "application/json",
    };
    const paymentSignature = request.headers.get("payment-signature");
    const quoteLamports = request.headers.get("x-quote-lamports");
    if (paymentSignature) headers["Payment-Signature"] = paymentSignature;
    if (quoteLamports) headers["X-Quote-Lamports"] = quoteLamports;

    const res = await fetch(`${X402_API_URL}/run`, {
      method: "POST",
      headers,
      body: JSON.stringify({ query }),
    });

    const data = await res.json().catch(() => ({}));
    return NextResponse.json(data, { status: res.status });
  } catch (e) {
    const message = e instanceof Error ? e.message : "Request failed";
    return NextResponse.json(
      { detail: message },
      { status: 502 }
    );
  }
}
