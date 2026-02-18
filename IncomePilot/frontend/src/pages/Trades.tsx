import { useEffect, useState, useRef } from "react";
import toast from "react-hot-toast";
import { tradesApi } from "../api/client";
import type {
  OptionTrade,
  OptionTradeCreate,
  IncomeReport,
  YTDPnL,
} from "../types";

const today = () => new Date().toISOString().slice(0, 10);
const yearStart = () => `${new Date().getFullYear()}-01-01`;

const EMPTY: OptionTradeCreate = {
  symbol: "",
  strategy_type: "CC",
  trade_type: "fresh",
  strike: 0,
  expiry: "",
  premium: 0,
  contracts: 1,
  trade_date: today(),
  owner: "Venky",
  notes: "",
};

export default function Trades() {
  const [trades, setTrades] = useState<OptionTrade[]>([]);
  const [form, setForm] = useState<OptionTradeCreate>({ ...EMPTY });
  const [editId, setEditId] = useState<number | null>(null);
  const [ytd, setYtd] = useState<YTDPnL | null>(null);
  const [report, setReport] = useState<IncomeReport | null>(null);
  const [reportStart, setReportStart] = useState(yearStart());
  const [reportEnd, setReportEnd] = useState(today());
  const [filterOwner, setFilterOwner] = useState("");
  const [filterSymbol, setFilterSymbol] = useState("");
  const [filterStrategy, setFilterStrategy] = useState("");
  const [editingNotes, setEditingNotes] = useState<number | null>(null);
  const [notesValue, setNotesValue] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const loadTrades = () => {
    const params: any = {};
    if (filterOwner) params.owner = filterOwner;
    if (filterSymbol) params.symbol = filterSymbol;
    if (filterStrategy) params.strategy_type = filterStrategy;
    tradesApi.list(params).then(setTrades).catch(() => {});
  };

  const loadYtd = () => tradesApi.ytdPnl(filterOwner || undefined).then(setYtd).catch(() => {});

  useEffect(() => {
    loadTrades();
    loadYtd();
  }, [filterOwner, filterSymbol, filterStrategy]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editId) {
        await tradesApi.update(editId, {
          notes: form.notes,
          premium: form.premium,
          trade_type: form.trade_type,
        } as any);
        toast.success("Trade updated");
      } else {
        await tradesApi.create(form);
        toast.success("Trade recorded");
      }
      setForm({ ...EMPTY });
      setEditId(null);
      loadTrades();
      loadYtd();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const startEdit = (t: OptionTrade) => {
    setEditId(t.id);
    setForm({
      symbol: t.symbol,
      strategy_type: t.strategy_type,
      trade_type: t.trade_type,
      strike: t.strike,
      expiry: t.expiry,
      premium: t.premium,
      contracts: t.contracts,
      trade_date: t.trade_date,
      owner: t.owner,
      notes: t.notes || "",
    });
  };

  const handleDelete = async (id: number) => {
    await tradesApi.remove(id);
    toast.success("Deleted");
    loadTrades();
    loadYtd();
  };

  const handleReport = async () => {
    try {
      const r = await tradesApi.incomeReport(reportStart, reportEnd);
      setReport(r);
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleCSV = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const result = await tradesApi.importCSV(file);
      toast.success(`Imported ${result.imported}, skipped ${result.skipped}`);
      if (result.errors.length) result.errors.forEach((err) => toast.error(err));
      loadTrades();
      loadYtd();
    } catch (err: any) {
      toast.error(err.message);
    }
    e.target.value = "";
  };

  const saveNotes = async (id: number) => {
    try {
      await tradesApi.update(id, { notes: notesValue } as any);
      setEditingNotes(null);
      loadTrades();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const fmt = (n: number) =>
    "$" + n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Trades</h2>

      {/* ── YTD P&L Card ─────────────────────────────────────────────── */}
      {ytd && (
        <div>
          <h3 className="text-lg font-semibold mb-2">
            {filterOwner ? `${filterOwner}'s YTD P&L` : "Family YTD P&L"}
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-500">Total Income (YTD)</p>
            <p className="text-2xl font-bold text-green-600">{fmt(ytd.total_premium_collected)}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-500">Total Losses (YTD)</p>
            <p className="text-2xl font-bold text-red-600">{fmt(ytd.total_losses)}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-500">Net P&L (YTD)</p>
            <p className={`text-2xl font-bold ${ytd.net_pnl >= 0 ? "text-green-600" : "text-red-600"}`}>
              {fmt(ytd.net_pnl)}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-500">Trade Count (YTD)</p>
            <p className="text-2xl font-bold">{ytd.trade_count}</p>
          </div>
        </div>
        </div>
      )}

      {/* ── Trade Entry Form ─────────────────────────────────────────── */}
      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-lg shadow p-4 grid grid-cols-2 sm:grid-cols-5 lg:grid-cols-10 gap-3 items-end"
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
          <label className="block text-xs font-medium text-gray-600 mb-1">Strategy</label>
          <select
            className="w-full border rounded px-2 py-1.5 text-sm"
            value={form.strategy_type}
            onChange={(e) => setForm({ ...form, strategy_type: e.target.value })}
          >
            <option value="CC">CC</option>
            <option value="CSP">CSP</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Type</label>
          <select
            className="w-full border rounded px-2 py-1.5 text-sm"
            value={form.trade_type}
            onChange={(e) => setForm({ ...form, trade_type: e.target.value })}
          >
            <option value="fresh">Fresh</option>
            <option value="roll">Roll</option>
          </select>
        </div>
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
            value={form.expiry}
            onChange={(e) => setForm({ ...form, expiry: e.target.value })}
            required
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Premium</label>
          <input
            type="number"
            step="0.01"
            className="w-full border rounded px-2 py-1.5 text-sm"
            value={form.premium || ""}
            onChange={(e) => setForm({ ...form, premium: +e.target.value })}
            required
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Contracts</label>
          <input
            type="number"
            className="w-full border rounded px-2 py-1.5 text-sm"
            value={form.contracts}
            onChange={(e) => setForm({ ...form, contracts: +e.target.value })}
            min={1}
            required
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Trade Date</label>
          <input
            type="date"
            className="w-full border rounded px-2 py-1.5 text-sm"
            value={form.trade_date}
            onChange={(e) => setForm({ ...form, trade_date: e.target.value })}
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
          <button
            type="submit"
            className="w-full bg-brand-600 text-white rounded px-3 py-1.5 text-sm font-medium hover:bg-brand-700"
          >
            {editId ? "Update" : "Add"}
          </button>
        </div>
        <div className="col-span-2 sm:col-span-5 lg:col-span-10">
          <label className="block text-xs font-medium text-gray-600 mb-1">Notes</label>
          <input
            className="w-full border rounded px-2 py-1.5 text-sm"
            value={form.notes || ""}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
            placeholder="Optional notes..."
          />
        </div>
      </form>

      {/* ── Income Report ────────────────────────────────────────────── */}
      <div className="bg-white rounded-lg shadow p-4 space-y-4">
        <h3 className="font-semibold">Income Report</h3>
        <div className="flex gap-3 items-end flex-wrap">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Start</label>
            <input
              type="date"
              className="border rounded px-2 py-1.5 text-sm"
              value={reportStart}
              onChange={(e) => setReportStart(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">End</label>
            <input
              type="date"
              className="border rounded px-2 py-1.5 text-sm"
              value={reportEnd}
              onChange={(e) => setReportEnd(e.target.value)}
            />
          </div>
          <button
            onClick={handleReport}
            className="px-4 py-1.5 bg-brand-600 text-white rounded text-sm hover:bg-brand-700"
          >
            Generate Report
          </button>
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
        </div>
        {report && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-left text-xs text-gray-500 uppercase">
                <tr>
                  <th className="px-4 py-2">Month</th>
                  <th className="px-4 py-2">CC Income</th>
                  <th className="px-4 py-2">CSP Income</th>
                  <th className="px-4 py-2">Total</th>
                  <th className="px-4 py-2"># Trades</th>
                </tr>
              </thead>
              <tbody>
                {report.monthly_breakdown.map((m) => (
                  <tr key={m.month} className="border-t">
                    <td className="px-4 py-2">{m.month}</td>
                    <td className="px-4 py-2">{fmt(m.cc_income)}</td>
                    <td className="px-4 py-2">{fmt(m.csp_income)}</td>
                    <td className="px-4 py-2 font-medium">{fmt(m.total_income)}</td>
                    <td className="px-4 py-2">{m.trade_count}</td>
                  </tr>
                ))}
                <tr className="border-t bg-gray-50 font-semibold">
                  <td className="px-4 py-2">Total</td>
                  <td className="px-4 py-2">{fmt(report.totals.cc_total)}</td>
                  <td className="px-4 py-2">{fmt(report.totals.csp_total)}</td>
                  <td className="px-4 py-2">{fmt(report.grand_total)}</td>
                  <td className="px-4 py-2"></td>
                </tr>
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Filters ──────────────────────────────────────────────────── */}
      <div className="flex gap-3 items-end flex-wrap">
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Owner</label>
          <select
            className="border rounded px-2 py-1.5 text-sm"
            value={filterOwner}
            onChange={(e) => setFilterOwner(e.target.value)}
          >
            <option value="">All</option>
            <option value="Venky">Venky</option>
            <option value="Bharg">Bharg</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Symbol</label>
          <input
            className="border rounded px-2 py-1.5 text-sm w-24"
            value={filterSymbol}
            onChange={(e) => setFilterSymbol(e.target.value.toUpperCase())}
            placeholder="e.g. TSLA"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Strategy</label>
          <select
            className="border rounded px-2 py-1.5 text-sm"
            value={filterStrategy}
            onChange={(e) => setFilterStrategy(e.target.value)}
          >
            <option value="">All</option>
            <option value="CC">CC</option>
            <option value="CSP">CSP</option>
          </select>
        </div>
      </div>

      {/* ── Trade History Table ───────────────────────────────────────── */}
      <div className="bg-white rounded-lg shadow overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs text-gray-500 uppercase">
            <tr>
              <th className="px-3 py-2">Date</th>
              <th className="px-3 py-2">Symbol</th>
              <th className="px-3 py-2">CC/CSP</th>
              <th className="px-3 py-2">Type</th>
              <th className="px-3 py-2">Strike</th>
              <th className="px-3 py-2">Expiry</th>
              <th className="px-3 py-2">Premium</th>
              <th className="px-3 py-2">Qty</th>
              <th className="px-3 py-2">Total</th>
              <th className="px-3 py-2">Owner</th>
              <th className="px-3 py-2">Notes</th>
              <th className="px-3 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((t) => {
              const total = t.premium * t.contracts * 100;
              return (
                <tr key={t.id} className="border-t hover:bg-gray-50">
                  <td className="px-3 py-2">{t.trade_date}</td>
                  <td className="px-3 py-2 font-medium">{t.symbol}</td>
                  <td className="px-3 py-2">{t.strategy_type}</td>
                  <td className="px-3 py-2 capitalize">{t.trade_type}</td>
                  <td className="px-3 py-2">${t.strike.toFixed(2)}</td>
                  <td className="px-3 py-2">{t.expiry}</td>
                  <td className={`px-3 py-2 ${t.premium >= 0 ? "text-green-600" : "text-red-600"}`}>
                    ${t.premium.toFixed(2)}
                  </td>
                  <td className="px-3 py-2">{t.contracts}</td>
                  <td className={`px-3 py-2 font-medium ${total >= 0 ? "text-green-600" : "text-red-600"}`}>
                    {fmt(total)}
                  </td>
                  <td className="px-3 py-2">{t.owner}</td>
                  <td className="px-3 py-2 max-w-[150px]">
                    {editingNotes === t.id ? (
                      <input
                        className="w-full border rounded px-1 py-0.5 text-sm"
                        value={notesValue}
                        onChange={(e) => setNotesValue(e.target.value)}
                        onBlur={() => saveNotes(t.id)}
                        onKeyDown={(e) => e.key === "Enter" && saveNotes(t.id)}
                        autoFocus
                      />
                    ) : (
                      <span
                        className="cursor-pointer hover:bg-gray-100 px-1 rounded block truncate"
                        onClick={() => {
                          setEditingNotes(t.id);
                          setNotesValue(t.notes || "");
                        }}
                        title={t.notes || "Click to add notes"}
                      >
                        {t.notes || "—"}
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2 flex gap-2">
                    <button
                      onClick={() => startEdit(t)}
                      className="text-blue-600 hover:underline"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(t.id)}
                      className="text-red-600 hover:underline"
                    >
                      Del
                    </button>
                  </td>
                </tr>
              );
            })}
            {trades.length === 0 && (
              <tr>
                <td colSpan={12} className="px-4 py-6 text-center text-gray-400">
                  No trades recorded yet. Add one above.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
