import { useState } from "react";
import toast from "react-hot-toast";
import { recommendationsApi, journalApi } from "../api/client";
import type { RecommendationResponse, CandidateMetrics } from "../types";

export default function Recommendations() {
  const [symbol, setSymbol] = useState("");
  const [strategyType, setStrategyType] = useState<"CC" | "CSP">("CC");
  const [result, setResult] = useState<RecommendationResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const handleFetch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!symbol.trim()) return;
    setLoading(true);
    try {
      const data = await recommendationsApi.get(symbol.trim().toUpperCase(), strategyType);
      setResult(data);
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  const saveToJournal = async (c: CandidateMetrics) => {
    try {
      await journalApi.create({
        symbol: c.symbol,
        decision_type: "sell",
        strike: c.strike,
        expiry: c.expiry,
        premium: c.mid,
        delta_at_entry: c.delta,
        contracts: 1,
        rationale: c.why,
      });
      toast.success("Saved to journal");
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const strategyLabel = strategyType === "CC" ? "Covered Call" : "Cash Secured Put";

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Option Recommendations</h2>

      <form onSubmit={handleFetch} className="flex gap-3 items-end">
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Symbol
          </label>
          <input
            className="border rounded px-3 py-1.5 text-sm w-32"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            placeholder="AAPL"
            required
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Strategy
          </label>
          <select
            className="border rounded px-3 py-1.5 text-sm w-48"
            value={strategyType}
            onChange={(e) => setStrategyType(e.target.value as "CC" | "CSP")}
          >
            <option value="CC">Covered Call (CC)</option>
            <option value="CSP">Cash Secured Put (CSP)</option>
          </select>
        </div>
        <button
          type="submit"
          disabled={loading}
          className="bg-brand-600 text-white rounded px-4 py-1.5 text-sm font-medium hover:bg-brand-700 disabled:opacity-50"
        >
          {loading ? "Loading..." : "Get Recommendations"}
        </button>
      </form>

      {result && (
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <p className="text-sm text-gray-600">
              <span className="font-semibold">{result.symbol}</span> spot: $
              {result.spot.toFixed(2)}
              <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded">
                {result.strategy_type === "CC" ? "Covered Call" : "Cash Secured Put"}
              </span>
            </p>
            {result.earnings_warning && (
              <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">
                {result.earnings_warning}
              </span>
            )}
          </div>

          {result.candidates.length === 0 ? (
            <p className="text-gray-400">
              No candidates matched the strategy filters.
            </p>
          ) : (
            <div className="grid gap-4">
              {result.candidates.map((c, i) => (
                <div
                  key={`${c.strike}-${c.expiry}`}
                  className="bg-white rounded-lg shadow p-4 space-y-3"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="text-xs text-gray-400">Rank #{i + 1}</span>
                      <h3 className="text-lg font-semibold">
                        ${c.strike} &middot; {c.expiry} ({c.dte} DTE)
                      </h3>
                    </div>
                    <span className="bg-green-100 text-green-800 text-sm font-bold px-2 py-0.5 rounded">
                      Score {c.score}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-sm">
                    <Stat label="Mid" value={`$${c.mid.toFixed(2)}`} />
                    <Stat label="Delta" value={c.delta.toFixed(3)} />
                    <Stat
                      label="Annualised"
                      value={`${c.annualized_yield_pct.toFixed(1)}%`}
                    />
                    <Stat
                      label="OTM"
                      value={`${(c.moneyness_pct * 100).toFixed(1)}%`}
                    />
                    <Stat label="IV" value={`${(c.iv * 100).toFixed(1)}%`} />
                    <Stat label="OI" value={String(c.open_interest)} />
                    <Stat label="Volume" value={String(c.volume)} />
                    <Stat
                      label="P(ITM)"
                      value={`${(c.prob_itm_proxy * 100).toFixed(0)}%`}
                    />
                  </div>

                  <div className="text-sm space-y-1 text-gray-700">
                    <p>
                      <strong>Why:</strong> {c.why}
                    </p>
                    <p>
                      <strong>Risk:</strong> {c.risk_note}
                    </p>
                    <p>
                      <strong>Income:</strong> {c.income_note}
                    </p>
                  </div>

                  <button
                    onClick={() => saveToJournal(c)}
                    className="text-sm bg-gray-100 hover:bg-gray-200 rounded px-3 py-1"
                  >
                    Save to Journal
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-gray-400">{label}</p>
      <p className="font-medium">{value}</p>
    </div>
  );
}
