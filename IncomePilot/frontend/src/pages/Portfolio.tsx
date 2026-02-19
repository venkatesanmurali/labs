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

  // Build a lookup of market values from netWorth data
  // For stocks: keyed by "SYMBOL|OWNER", summing market_value across lots
  // For LEAPS: keyed by holding id from netWorth (matched by symbol+owner+type)
  const nwByKey = new Map<string, { market_value: number; current_price: number }>();
  if (netWorth) {
    for (const nwh of netWorth.holdings) {
      const key = `${nwh.symbol}|${nwh.owner}|${nwh.holding_type}`;
      const existing = nwByKey.get(key);
      if (existing) {
        existing.market_value += nwh.market_value;
      } else {
        nwByKey.set(key, { market_value: nwh.market_value, current_price: nwh.current_price });
      }
    }
  }

  // Group stock holdings by (symbol, owner) — LEAPS stay separate
  type GroupedHolding = {
    key: string;
    symbol: string;
    owner: string;
    holding_type: string;
    total_shares: number;
    weighted_avg_cost: number;
    market_value: number;
    tags: string[];
    ids: number[];
    // For LEAPS
    strike: number | null;
    expiry: string | null;
    option_type: string | null;
  };

  const grouped: GroupedHolding[] = [];
  const stockMap = new Map<string, GroupedHolding>();

  for (const h of holdings) {
    if (h.holding_type === "leaps") {
      const nwKey = `${h.symbol}|${h.owner}|leaps`;
      const nw = nwByKey.get(nwKey);
      grouped.push({
        key: `leaps-${h.id}`,
        symbol: h.symbol,
        owner: h.owner,
        holding_type: h.holding_type,
        total_shares: h.shares,
        weighted_avg_cost: h.avg_cost,
        market_value: nw?.market_value ?? 0,
        tags: h.tags ? [h.tags] : [],
        ids: [h.id],
        strike: h.strike,
        expiry: h.expiry,
        option_type: h.option_type,
      });
    } else {
      const mapKey = `${h.symbol}|${h.owner}`;
      const existing = stockMap.get(mapKey);
      if (existing) {
        const totalCost = existing.weighted_avg_cost * existing.total_shares + h.avg_cost * h.shares;
        existing.total_shares += h.shares;
        existing.weighted_avg_cost = totalCost / existing.total_shares;
        existing.ids.push(h.id);
        if (h.tags && !existing.tags.includes(h.tags)) existing.tags.push(h.tags);
      } else {
        const nwKey = `${h.symbol}|${h.owner}|stock`;
        const nw = nwByKey.get(nwKey);
        const entry: GroupedHolding = {
          key: mapKey,
          symbol: h.symbol,
          owner: h.owner,
          holding_type: h.holding_type,
          total_shares: h.shares,
          weighted_avg_cost: h.avg_cost,
          market_value: nw?.market_value ?? 0,
          tags: h.tags ? [h.tags] : [],
          ids: [h.id],
          strike: null,
          expiry: null,
          option_type: null,
        };
        stockMap.set(mapKey, entry);
      }
    }
  }
  // Add stock groups, sorted by symbol
  grouped.push(...[...stockMap.values()].sort((a, b) => a.symbol.localeCompare(b.symbol)));
  // Sort: stocks first, then LEAPS
  grouped.sort((a, b) => {
    if (a.holding_type !== b.holding_type) return a.holding_type === "stock" ? -1 : 1;
    return a.symbol.localeCompare(b.symbol);
  });

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
            step="0.0001"
            className="w-full border rounded px-2 py-1.5 text-sm"
            value={form.shares}
            onChange={(e) => setForm({ ...form, shares: +e.target.value })}
            min={0.0001}
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
            onChange={(e) => {
              const ht = e.target.value;
              setForm({
                ...form,
                holding_type: ht,
                option_type: ht === "leaps" ? (form.option_type || "call") : null,
              });
            }}
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
              <th className="px-4 py-2">Market Value</th>
              <th className="px-4 py-2">Owner</th>
              <th className="px-4 py-2">Type</th>
              <th className="px-4 py-2">Details</th>
              <th className="px-4 py-2">Tags</th>
              <th className="px-4 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {grouped.map((g) => (
              <tr key={g.key} className="border-t hover:bg-gray-50">
                <td className="px-4 py-2 font-medium">
                  {g.symbol}
                  {g.ids.length > 1 && (
                    <span className="ml-1 text-xs text-gray-400">({g.ids.length} lots)</span>
                  )}
                </td>
                <td className="px-4 py-2">{g.total_shares % 1 === 0 ? g.total_shares : g.total_shares.toFixed(4)}</td>
                <td className="px-4 py-2">${g.weighted_avg_cost.toFixed(2)}</td>
                <td className="px-4 py-2 font-medium text-green-700">
                  ${g.market_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </td>
                <td className="px-4 py-2">{g.owner}</td>
                <td className="px-4 py-2 capitalize">{g.holding_type}</td>
                <td className="px-4 py-2 text-gray-500">
                  {g.holding_type === "leaps"
                    ? `${g.option_type?.toUpperCase()} $${g.strike} exp ${g.expiry}`
                    : "—"}
                </td>
                <td className="px-4 py-2 text-gray-500">{g.tags.join(", ") || "—"}</td>
                <td className="px-4 py-2 flex gap-2">
                  {g.ids.length === 1 ? (
                    <>
                      <button
                        onClick={() => {
                          const h = holdings.find((x) => x.id === g.ids[0]);
                          if (h) startEdit(h);
                        }}
                        className="text-blue-600 hover:underline"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(g.ids[0])}
                        className="text-red-600 hover:underline"
                      >
                        Del
                      </button>
                    </>
                  ) : (
                    <span className="text-xs text-gray-400">Grouped</span>
                  )}
                </td>
              </tr>
            ))}
            {holdings.length === 0 && (
              <tr>
                <td colSpan={9} className="px-4 py-6 text-center text-gray-400">
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
