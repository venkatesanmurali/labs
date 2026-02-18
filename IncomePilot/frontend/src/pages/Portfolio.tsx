import { useEffect, useState, useRef } from "react";
import toast from "react-hot-toast";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { holdingsApi } from "../api/client";
import type { Holding, HoldingCreate, NetWorthSummary } from "../types";

const COLORS = [
  "#22c55e", "#3b82f6", "#f59e0b", "#ef4444",
  "#8b5cf6", "#ec4899", "#14b8a6", "#6366f1",
];

const EMPTY: HoldingCreate = {
  symbol: "",
  shares: 100,
  avg_cost: 0,
  owner: "Venky",
  holding_type: "stock",
  strike: null,
  expiry: null,
  option_type: null,
  tags: "",
};

export default function Portfolio() {
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [form, setForm] = useState<HoldingCreate>({ ...EMPTY });
  const [editId, setEditId] = useState<number | null>(null);
  const [ownerFilter, setOwnerFilter] = useState<string>("");
  const [netWorth, setNetWorth] = useState<NetWorthSummary | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const load = () => {
    holdingsApi.list(ownerFilter || undefined).then(setHoldings).catch(() => {});
    holdingsApi.netWorth().then(setNetWorth).catch(() => {});
  };

  useEffect(() => {
    load();
  }, [ownerFilter]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = { ...form };
    if (payload.holding_type === "stock") {
      payload.strike = null;
      payload.expiry = null;
      payload.option_type = null;
    }
    try {
      if (editId) {
        await holdingsApi.update(editId, payload);
        toast.success("Holding updated");
      } else {
        await holdingsApi.create(payload);
        toast.success("Holding added");
      }
      setForm({ ...EMPTY });
      setEditId(null);
      load();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const startEdit = (h: Holding) => {
    setEditId(h.id);
    setForm({
      symbol: h.symbol,
      shares: h.shares,
      avg_cost: h.avg_cost,
      owner: h.owner,
      holding_type: h.holding_type,
      strike: h.strike,
      expiry: h.expiry,
      option_type: h.option_type,
      tags: h.tags || "",
    });
  };

  const handleDelete = async (id: number) => {
    await holdingsApi.remove(id);
    toast.success("Deleted");
    load();
  };

  const handleCSV = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const result = await holdingsApi.importCSV(file);
      toast.success(`Imported ${result.imported}, skipped ${result.skipped}`);
      if (result.errors.length) {
        result.errors.forEach((err) => toast.error(err));
      }
      load();
    } catch (err: any) {
      toast.error(err.message);
    }
    e.target.value = "";
  };

  const handleDemo = async () => {
    try {
      await holdingsApi.loadDemo();
      toast.success("Demo portfolio loaded");
      load();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const pieData = netWorth?.holdings
    .filter((h) => h.market_value > 0)
    .map((h) => ({ name: `${h.symbol} (${h.owner})`, value: h.market_value })) || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Portfolio</h2>
        <div className="flex gap-2">
          <select
            className="border rounded px-2 py-1.5 text-sm"
            value={ownerFilter}
            onChange={(e) => setOwnerFilter(e.target.value)}
          >
            <option value="">All Owners</option>
            <option value="Venky">Venky</option>
            <option value="Bharg">Bharg</option>
          </select>
          <button
            onClick={() => fileRef.current?.click()}
            className="px-3 py-1.5 bg-gray-200 rounded text-sm hover:bg-gray-300"
          >
            Import CSV
          </button>
          <input
            ref={fileRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={handleCSV}
          />
          <button
            onClick={handleDemo}
            className="px-3 py-1.5 bg-brand-600 text-white rounded text-sm hover:bg-brand-700"
          >
            Load Demo
          </button>
        </div>
      </div>

      {/* ── Net Worth Summary ─────────────────────────────────────────── */}
      {netWorth && netWorth.total_net_worth > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg shadow p-4 lg:col-span-1">
            <p className="text-sm text-gray-500">Family Net Worth</p>
            <p className="text-2xl font-bold text-green-600">
              ${netWorth.total_net_worth.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
            <div className="mt-3 space-y-1">
              {Object.entries(netWorth.by_owner).map(([owner, val]) => (
                <div key={owner} className="flex justify-between text-sm">
                  <span className="text-gray-600">{owner}</span>
                  <span className="font-medium">
                    ${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                </div>
              ))}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 lg:col-span-2">
            <h3 className="font-semibold mb-2 text-sm">Allocation</h3>
            {pieData.length > 0 && (
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={pieData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label={(e) => e.name}
                  >
                    {pieData.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v: number) => `$${v.toLocaleString(undefined, { maximumFractionDigits: 2 })}`} />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      )}

      {/* ── Add / Edit form ──────────────────────────────────────────── */}
      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-lg shadow p-4 grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3 items-end"
      >
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Symbol</label>
          <input
            className="w-full border rounded px-2 py-1.5 text-sm"
            value={form.symbol}
            onChange={(e) => setForm({ ...form, symbol: e.target.value.toUpperCase() })}
            required
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Shares</label>
          <input
            type="number"
            className="w-full border rounded px-2 py-1.5 text-sm"
            value={form.shares}
            onChange={(e) => setForm({ ...form, shares: +e.target.value })}
            min={1}
            required
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Avg Cost</label>
          <input
            type="number"
            step="0.01"
            className="w-full border rounded px-2 py-1.5 text-sm"
            value={form.avg_cost || ""}
            onChange={(e) => setForm({ ...form, avg_cost: +e.target.value })}
            required
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Owner</label>
          <select
            className="w-full border rounded px-2 py-1.5 text-sm"
            value={form.owner}
            onChange={(e) => setForm({ ...form, owner: e.target.value })}
          >
            <option value="Venky">Venky</option>
            <option value="Bharg">Bharg</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Type</label>
          <select
            className="w-full border rounded px-2 py-1.5 text-sm"
            value={form.holding_type}
            onChange={(e) => setForm({ ...form, holding_type: e.target.value })}
          >
            <option value="stock">Stock</option>
            <option value="leaps">LEAPS</option>
          </select>
        </div>
        {form.holding_type === "leaps" && (
          <>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Strike</label>
              <input
                type="number"
                step="0.01"
                className="w-full border rounded px-2 py-1.5 text-sm"
                value={form.strike || ""}
                onChange={(e) => setForm({ ...form, strike: +e.target.value })}
                required
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Expiry</label>
              <input
                type="date"
                className="w-full border rounded px-2 py-1.5 text-sm"
                value={form.expiry || ""}
                onChange={(e) => setForm({ ...form, expiry: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Call/Put</label>
              <select
                className="w-full border rounded px-2 py-1.5 text-sm"
                value={form.option_type || "call"}
                onChange={(e) => setForm({ ...form, option_type: e.target.value })}
              >
                <option value="call">Call</option>
                <option value="put">Put</option>
              </select>
            </div>
          </>
        )}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Tags</label>
          <input
            className="w-full border rounded px-2 py-1.5 text-sm"
            value={form.tags || ""}
            onChange={(e) => setForm({ ...form, tags: e.target.value })}
          />
        </div>
        <div>
          <button
            type="submit"
            className="w-full bg-brand-600 text-white rounded px-3 py-1.5 text-sm font-medium hover:bg-brand-700"
          >
            {editId ? "Update" : "Add"}
          </button>
        </div>
      </form>

      {/* ── Table ────────────────────────────────────────────────────── */}
      <div className="bg-white rounded-lg shadow overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs text-gray-500 uppercase">
            <tr>
              <th className="px-4 py-2">Symbol</th>
              <th className="px-4 py-2">Shares</th>
              <th className="px-4 py-2">Avg Cost</th>
              <th className="px-4 py-2">Owner</th>
              <th className="px-4 py-2">Type</th>
              <th className="px-4 py-2">Details</th>
              <th className="px-4 py-2">Tags</th>
              <th className="px-4 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {holdings.map((h) => (
              <tr key={h.id} className="border-t hover:bg-gray-50">
                <td className="px-4 py-2 font-medium">{h.symbol}</td>
                <td className="px-4 py-2">{h.shares}</td>
                <td className="px-4 py-2">${h.avg_cost.toFixed(2)}</td>
                <td className="px-4 py-2">{h.owner}</td>
                <td className="px-4 py-2 capitalize">{h.holding_type}</td>
                <td className="px-4 py-2 text-gray-500">
                  {h.holding_type === "leaps"
                    ? `${h.option_type?.toUpperCase()} $${h.strike} exp ${h.expiry}`
                    : "—"}
                </td>
                <td className="px-4 py-2 text-gray-500">{h.tags || "—"}</td>
                <td className="px-4 py-2 flex gap-2">
                  <button
                    onClick={() => startEdit(h)}
                    className="text-blue-600 hover:underline"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(h.id)}
                    className="text-red-600 hover:underline"
                  >
                    Del
                  </button>
                </td>
              </tr>
            ))}
            {holdings.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-6 text-center text-gray-400">
                  No holdings yet. Add one above or load the demo portfolio.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
