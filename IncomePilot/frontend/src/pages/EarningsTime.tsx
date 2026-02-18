import { useState } from "react";
import { earningsApi } from "../api/client";
import type { EarningsAnalysisResponse, KeyMetric } from "../types";

function fmtLarge(val: number | null): string {
  if (val == null) return "N/A";
  const abs = Math.abs(val);
  if (abs >= 1e12) return `$${(val / 1e12).toFixed(2)}T`;
  if (abs >= 1e9) return `$${(val / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `$${(val / 1e6).toFixed(1)}M`;
  return `$${val.toLocaleString()}`;
}

const sentimentColor: Record<string, string> = {
  bullish: "bg-green-100 text-green-800 border-green-300",
  bearish: "bg-red-100 text-red-800 border-red-300",
  neutral: "bg-gray-100 text-gray-700 border-gray-300",
};

function MetricCard({ metric }: { metric: KeyMetric }) {
  return (
    <div className={`rounded-lg border p-3 ${sentimentColor[metric.sentiment] || sentimentColor.neutral}`}>
      <div className="text-xs font-medium opacity-70">{metric.name}</div>
      <div className="text-lg font-bold mt-1">{metric.value}</div>
    </div>
  );
}

function ConfidenceMeter({ confidence }: { confidence: number }) {
  const color =
    confidence >= 70 ? "bg-green-500" : confidence >= 40 ? "bg-yellow-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-3 bg-gray-200 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${confidence}%` }} />
      </div>
      <span className="text-sm font-bold w-10 text-right">{confidence}%</span>
    </div>
  );
}

export default function EarningsTime() {
  const [ticker, setTicker] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EarningsAnalysisResponse | null>(null);

  const handleAnalyze = async () => {
    const sym = ticker.trim().toUpperCase();
    if (!sym) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await earningsApi.analyze(sym);
      setResult(data);
    } catch (e: any) {
      setError(e.message || "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Earnings Time</h2>
      <p className="text-gray-500">
        Enter a ticker to get an AI-powered deep analysis before earnings.
      </p>

      {/* ── Search ── */}
      <div className="flex gap-2">
        <input
          type="text"
          value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          onKeyDown={(e) => e.key === "Enter" && handleAnalyze()}
          placeholder="AAPL, TSLA, MSFT…"
          className="border rounded-lg px-4 py-2 w-48 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
        <button
          onClick={handleAnalyze}
          disabled={loading || !ticker.trim()}
          className="bg-brand-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-brand-700 disabled:opacity-50"
        >
          {loading ? "Analyzing…" : "Analyze"}
        </button>
      </div>

      {/* ── Loading ── */}
      {loading && (
        <div className="flex items-center gap-3 text-gray-500 py-12 justify-center">
          <svg className="animate-spin h-6 w-6" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
          </svg>
          <span>Fetching data &amp; running AI analysis… this may take 10-15 seconds</span>
        </div>
      )}

      {/* ── Error ── */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4">
          {error}
        </div>
      )}

      {/* ── Results ── */}
      {result && (
        <div className="space-y-6">
          {/* Header */}
          <div className="bg-white rounded-lg border p-5 flex items-center justify-between">
            <div>
              <h3 className="text-xl font-bold">{result.company_name}</h3>
              <span className="text-gray-500 text-sm">{result.ticker}</span>
              {result.financials.sector && (
                <span className="text-gray-400 text-sm ml-2">
                  {result.financials.sector} / {result.financials.industry}
                </span>
              )}
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold">${result.current_price.toFixed(2)}</div>
              {result.earnings_date && (
                <div className="text-sm text-gray-500">
                  Earnings: {result.earnings_date}
                </div>
              )}
            </div>
          </div>

          {/* Prediction */}
          <div
            className={`rounded-lg border-2 p-5 ${
              result.prediction.direction === "UP"
                ? "border-green-400 bg-green-50"
                : "border-red-400 bg-red-50"
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-lg font-bold">AI Prediction</h4>
              <span
                className={`text-3xl font-black ${
                  result.prediction.direction === "UP" ? "text-green-600" : "text-red-600"
                }`}
              >
                {result.prediction.direction === "UP" ? "▲" : "▼"}{" "}
                {result.prediction.direction} {result.prediction.magnitude_pct.toFixed(1)}%
              </span>
            </div>
            <div className="grid grid-cols-3 gap-4 mb-3">
              <div>
                <div className="text-xs text-gray-500">Direction</div>
                <div className="font-bold">{result.prediction.direction}</div>
              </div>
              <div>
                <div className="text-xs text-gray-500">Expected Move</div>
                <div className="font-bold">
                  ${result.prediction.magnitude_price.toFixed(2)} ({result.prediction.magnitude_pct.toFixed(1)}%)
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-500">Confidence</div>
                <div className="font-bold">{result.prediction.confidence}/100</div>
              </div>
            </div>
            <ConfidenceMeter confidence={result.prediction.confidence} />
          </div>

          {/* Key Metrics Grid */}
          {result.key_metrics.length > 0 && (
            <div>
              <h4 className="text-lg font-bold mb-3">Key Metrics</h4>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                {result.key_metrics.map((m, i) => (
                  <MetricCard key={i} metric={m} />
                ))}
              </div>
            </div>
          )}

          {/* Options Recommendation */}
          <div className="bg-white rounded-lg border p-5">
            <h4 className="text-lg font-bold mb-3">Options Recommendation</h4>
            {result.options_recommendation.viable ? (
              <div className="space-y-2">
                <div className="flex gap-6">
                  <div>
                    <span className="text-xs text-gray-500">Strategy</span>
                    <div className="font-bold text-lg">
                      {result.options_recommendation.strategy === "CALL" ? "📈 Buy CALL" : "📉 Buy PUT"}
                    </div>
                  </div>
                  {result.options_recommendation.suggested_strike && (
                    <div>
                      <span className="text-xs text-gray-500">Strike</span>
                      <div className="font-bold text-lg">
                        ${result.options_recommendation.suggested_strike}
                      </div>
                    </div>
                  )}
                  {result.options_recommendation.suggested_expiry && (
                    <div>
                      <span className="text-xs text-gray-500">Expiry</span>
                      <div className="font-bold text-lg">
                        {result.options_recommendation.suggested_expiry}
                      </div>
                    </div>
                  )}
                </div>
                {result.options_recommendation.rationale && (
                  <p className="text-sm text-gray-600 mt-2">
                    {result.options_recommendation.rationale}
                  </p>
                )}
              </div>
            ) : (
              <p className="text-gray-500">
                No clear options trade recommended for this setup.
              </p>
            )}
          </div>

          {/* Detailed Analysis */}
          {result.analysis_summary && (
            <div className="bg-white rounded-lg border p-5">
              <h4 className="text-lg font-bold mb-3">Detailed Analysis</h4>
              <div
                className="prose prose-sm max-w-none text-gray-700"
                dangerouslySetInnerHTML={{ __html: markdownToHtml(result.analysis_summary) }}
              />
            </div>
          )}

          {/* Risk Factors */}
          {result.risk_factors.length > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-5">
              <h4 className="text-lg font-bold mb-3 text-yellow-800">Risk Factors</h4>
              <ul className="list-disc list-inside space-y-1">
                {result.risk_factors.map((r, i) => (
                  <li key={i} className="text-sm text-yellow-700">{r}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Financials snapshot */}
          <div className="bg-white rounded-lg border p-5">
            <h4 className="text-lg font-bold mb-3">Financial Snapshot</h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Market Cap</span>
                <div className="font-bold">{fmtLarge(result.financials.market_cap)}</div>
              </div>
              <div>
                <span className="text-gray-500">P/E Ratio</span>
                <div className="font-bold">{result.financials.pe_ratio?.toFixed(1) ?? "N/A"}</div>
              </div>
              <div>
                <span className="text-gray-500">Forward P/E</span>
                <div className="font-bold">{result.financials.forward_pe?.toFixed(1) ?? "N/A"}</div>
              </div>
              <div>
                <span className="text-gray-500">EBITDA</span>
                <div className="font-bold">{fmtLarge(result.financials.ebitda)}</div>
              </div>
              <div>
                <span className="text-gray-500">Profit Margin</span>
                <div className="font-bold">
                  {result.financials.profit_margin != null
                    ? `${(result.financials.profit_margin * 100).toFixed(1)}%`
                    : "N/A"}
                </div>
              </div>
              <div>
                <span className="text-gray-500">Debt/Equity</span>
                <div className="font-bold">{result.financials.debt_to_equity?.toFixed(1) ?? "N/A"}</div>
              </div>
              <div>
                <span className="text-gray-500">30d Price Change</span>
                <div className={`font-bold ${(result.financials.price_change_30d_pct ?? 0) >= 0 ? "text-green-600" : "text-red-600"}`}>
                  {result.financials.price_change_30d_pct != null
                    ? `${result.financials.price_change_30d_pct > 0 ? "+" : ""}${result.financials.price_change_30d_pct.toFixed(1)}%`
                    : "N/A"}
                </div>
              </div>
              <div>
                <span className="text-gray-500">Implied Volatility</span>
                <div className="font-bold">
                  {result.financials.implied_volatility != null
                    ? `${result.financials.implied_volatility.toFixed(1)}%`
                    : "N/A"}
                </div>
              </div>
            </div>

            {/* EPS History */}
            {result.financials.eps_history.length > 0 && (
              <div className="mt-4">
                <h5 className="font-semibold text-sm mb-2">EPS History</h5>
                <div className="overflow-x-auto">
                  <table className="text-xs w-full">
                    <thead>
                      <tr className="text-gray-500 border-b">
                        <th className="text-left py-1 pr-3">Quarter</th>
                        <th className="text-right py-1 pr-3">Actual</th>
                        <th className="text-right py-1 pr-3">Estimate</th>
                        <th className="text-right py-1 pr-3">Surprise</th>
                        <th className="text-center py-1">Result</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.financials.eps_history.map((q, i) => (
                        <tr key={i} className="border-b border-gray-100">
                          <td className="py-1 pr-3">{q.quarter}</td>
                          <td className="text-right py-1 pr-3">{q.actual ?? "N/A"}</td>
                          <td className="text-right py-1 pr-3">{q.estimate ?? "N/A"}</td>
                          <td className="text-right py-1 pr-3">
                            {q.surprise_pct != null ? `${q.surprise_pct.toFixed(1)}%` : "N/A"}
                          </td>
                          <td className="text-center py-1">
                            {q.beat === true && <span className="text-green-600 font-bold">BEAT</span>}
                            {q.beat === false && <span className="text-red-600 font-bold">MISS</span>}
                            {q.beat == null && <span className="text-gray-400">—</span>}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/** Minimal markdown→HTML for the analysis summary (bold, italic, headings, lists). */
function markdownToHtml(md: string): string {
  return md
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/^### (.+)$/gm, "<h5 class='font-bold mt-3 mb-1'>$1</h5>")
    .replace(/^## (.+)$/gm, "<h4 class='font-bold text-lg mt-4 mb-1'>$1</h4>")
    .replace(/^# (.+)$/gm, "<h3 class='font-bold text-xl mt-4 mb-2'>$1</h3>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/^- (.+)$/gm, "<li class='ml-4'>$1</li>")
    .replace(/\n\n/g, "<br/><br/>");
}
