import { useEffect, useState, useRef } from "react";
import toast from "react-hot-toast";
import { holdingsApi } from "../api/client";
import type { Holding, HoldingCreate } from "../types";

const EMPTY: HoldingCreate = {
  symbol: "",
  shares: 100,
  avg_cost: 0,
  account_type: "taxable",
  tags: "",
};

export default function Portfolio() {
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [form, setForm] = useState<HoldingCreate>({ ...EMPTY });
  const [editId, setEditId] = useState<number | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const load = () => holdingsApi.list().then(setHoldings).catch(() => {});

  useEffect(() => {
    load();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editId) {
        await holdingsApi.update(editId, form);
        toast.success("Holding updated");
      } else {
        await holdingsApi.create(form);
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
      account_type: h.account_type,
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Portfolio</h2>
        <div className="flex gap-2">
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

      {/* ── Add / Edit form ──────────────────────────────────────────── */}
      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-lg shadow p-4 grid grid-cols-2 sm:grid-cols-6 gap-3 items-end"
      >
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Symbol
          </label>
          <input
            className="w-full border rounded px-2 py-1.5 text-sm"
            value={form.symbol}
            onChange={(e) =>
              setForm({ ...form, symbol: e.target.value.toUpperCase() })
            }
            required
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Shares
          </label>
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
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Avg Cost
          </label>
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
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Account
          </label>
          <select
            className="w-full border rounded px-2 py-1.5 text-sm"
            value={form.account_type}
            onChange={(e) => setForm({ ...form, account_type: e.target.value })}
          >
            <option value="taxable">Taxable</option>
            <option value="retirement">Retirement</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Tags
          </label>
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
              <th className="px-4 py-2">Account</th>
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
                <td className="px-4 py-2 capitalize">{h.account_type}</td>
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
                <td colSpan={6} className="px-4 py-6 text-center text-gray-400">
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
