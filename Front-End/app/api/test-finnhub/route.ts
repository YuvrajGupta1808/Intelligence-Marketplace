import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function GET() {
  const token =
    process.env.FINNHUB_API_KEY ?? process.env.NEXT_PUBLIC_FINNHUB_API_KEY ?? '';

  if (!token) {
    return NextResponse.json(
      { ok: false, error: 'FINNHUB_API_KEY is not set in .env' },
      { status: 500 }
    );
  }

  try {
    const url = `https://finnhub.io/api/v1/quote?symbol=AAPL&token=${token}`;
    const res = await fetch(url, { cache: 'no-store' });

    if (!res.ok) {
      const text = await res.text();
      return NextResponse.json(
        { ok: false, error: `Finnhub returned ${res.status}: ${text.slice(0, 200)}` },
        { status: 502 }
      );
    }

    const data = await res.json();
    // Free tier may return zeros; we only care that the API responded
    return NextResponse.json({
      ok: true,
      message: 'Finnhub API is working',
      sample: { symbol: 'AAPL', currentPrice: data.c ?? 0 },
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json(
      { ok: false, error: message },
      { status: 500 }
    );
  }
}
