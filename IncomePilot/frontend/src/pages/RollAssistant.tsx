import { useState } from "react";
import toast from "react-hot-toast";
import { rollApi } from "../api/client";
import type { RollRequest, RollDecision } from "../types";

const DEFAULT: RollRequest = {
  symbol: "TSLA",
  strike: 350,
  expiry: "",
  sold_price: 5.0,
  current_option_mid: 8.0,
  current_spot: 340,
  days_to_expiry: 5,
};

const ACTION_LABELS: Record<string, string> = {
  hold: "Hold",
  close: "Close Position",
  roll_out: "Roll Out",
  roll_up_and_out: "Roll Up & Out",
  accept_assignment: "Accept Assignment",
};

const ACTION_COLORS: Record<string, string> = {
  hold: "bg-blue-100 text-blue-800",
  close: "bg-red-100 text-red-800",
  roll_out: "bg-yellow-100 text-yellow-800",
  roll_up_and_out: "bg-green-100 text-green-800",
  accept_assignment: "bg-purple-100 text-purple-800",
};

export default function RollAssistant() {
  const [form, setForm] = useState<RollRequest>({
    ...DEFAULT,
    expiry: new Date(Date.now() + 5 * 86400000).toISOString().slice(0, 10),
  });
  const [result, setResult] = useState<RollDecision | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const data = await rollApi.evaluate(form);
      setResult(data);
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  const set = (key: keyof RollRequest, val: string | number) =>
    setForm({ ...form, [key]: val });

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Roll Assistant</h2>

      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-lg shadow p-4 grid grid-cols-2 sm:grid-cols-4 gap-3 items-end"
      >
        <Field label="Symbol">
          <input
            className="input"
            value={form.symbol}
            onChange={(e) => set("symbol", e.target.value.toUpperCase())}
            required
          />
        </Field>
        <Field label="Strike">
          <input
            type="number"
            step="0.01"
            className="input"
            value={form.strike}
            onChange={(e) => set("strike", +e.target.value)}
            required
          />
        </Field>
        <Field label="Expiry">
          <input
            type="date"
            className="input"
            value={form.expiry}
            onChange={(e) => set("expiry", e.target.value)}
            required
          />
        </Field>
        <Field label="DTE">
          <input
            type="number"
            className="input"
            value={form.days_to_expiry}
            onChange={(e) => set("days_to_expiry", +e.target.value)}
            required
          />
        </Field>
        <Field label="Sold Price">
          <input
            type="number"
            step="0.01"
            className="input"
            value={form.sold_price}
            onChange={(e) => set("sold_price", +e.target.value)}
            required
          />
        </Field>
        <Field label="Current Option Mid">
          <input
            type="number"
            step="0.01"
            className="input"
            value={form.current_option_mid}
            onChange={(e) => set("current_option_mid", +e.target.value)}
            required
          />
        </Field>
        <Field label="Current Spot">
          <input
            type="number"
            step="0.01"
            className="input"
            value={form.current_spot}
            onChange={(e) => set("current_spot", +e.target.value)}
            required
          />
        </Field>
        <div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-brand-600 text-white rounded px-3 py-1.5 text-sm font-medium hover:bg-brand-700 disabled:opacity-50"
          >
            {loading ? "Evaluating..." : "Evaluate"}
          </button>
        </div>
      </form>

      {result && (
        <div className="space-y-4">
          {/* Decision card */}
          <div className="bg-white rounded-lg shadow p-4 space-y-3">
            <div className="flex items-center gap-3">
              <span
                className={`text-sm font-bold px-3 py-1 rounded ${
                  ACTION_COLORS[result.action] || "bg-gray-100"
                }`}
              >
                {ACTION_LABELS[result.action] || result.action}
              </span>
            </div>
            <p className="text-sm text-gray-700">{result.explanation}</p>
            <div className="flex gap-6 text-sm">
              <span>
                Intrinsic:{" "}
                <strong>${result.current_intrinsic.toFixed(2)}</strong>
              </span>
              <span>
                Extrinsic:{" "}
                <strong>${result.current_extrinsic.toFixed(2)}</strong>
              </span>
            </div>
          </div>

          {/* Alternatives table */}
          {result.alternatives.length > 0 && (
            <div className="bg-white rounded-lg shadow overflow-x-auto">
              <h3 className="font-semibold px-4 pt-3">
                Roll Alternatives (What-If)
              </h3>
              <table className="w-full text-sm mt-2">
                <thead className="bg-gray-50 text-left text-xs text-gray-500 uppercase">
                  <tr>
                    <th className="px-4 py-2">Strike</th>
                    <th className="px-4 py-2">Expiry</th>
                    <th className="px-4 py-2">DTE</th>
                    <th className="px-4 py-2">Delta</th>
                    <th className="px-4 py-2">Mid</th>
                    <th className="px-4 py-2">Net Credit</th>
                    <th className="px-4 py-2">OTM %</th>
                    <th className="px-4 py-2">Note</th>
                  </tr>
                </thead>
                <tbody>
                  {result.alternatives.map((a, i) => (
                    <tr
                      key={i}
                      className="border-t hover:bg-gray-50"
                    >
                      <td className="px-4 py-2 font-medium">${a.strike}</td>
                      <td className="px-4 py-2">{a.expiry}</td>
                      <td className="px-4 py-2">{a.dte}</td>
                      <td className="px-4 py-2">{a.delta.toFixed(3)}</td>
                      <td className="px-4 py-2">${a.mid.toFixed(2)}</td>
                      <td
                        className={`px-4 py-2 font-medium ${
                          a.net_credit >= 0
                            ? "text-green-600"
                            : "text-red-600"
                        }`}
                      >
                        {a.net_credit >= 0 ? "+" : ""}
                        ${a.net_credit.toFixed(2)}
                      </td>
                      <td className="px-4 py-2">
                        {(a.new_moneyness_pct * 100).toFixed(1)}%
                      </td>
                      <td className="px-4 py-2 text-xs text-gray-500 max-w-xs truncate">
                        {a.explanation}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-600 mb-1">
        {label}
      </label>
      {children}
    </div>
  );
}
