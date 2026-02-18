import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { journalApi, holdingsApi, tradesApi } from "../api/client";
import type { AnalyticsDashboard, NetWorthSummary, YTDPnL } from "../types";

const COLORS = [
  "#22c55e",
  "#3b82f6",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#ec4899",
  "#14b8a6",
];

export default function Dashboard() {
  const [data, setData] = useState<AnalyticsDashboard | null>(null);
  const [netWorth, setNetWorth] = useState<NetWorthSummary | null>(null);
  const [ytd, setYtd] = useState<YTDPnL | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      journalApi.dashboard().catch(() => null),
      holdingsApi.netWorth().catch(() => null),
      tradesApi.ytdPnl().catch(() => null),
    ]).then(([d, nw, y]) => {
      setData(d);
      setNetWorth(nw);
      setYtd(y);
      setLoading(false);
    });
  }, []);

  if (loading)
    return <p className="text-gray-500">Loading dashboard...</p>;

  const pnl = data?.pnl;
  const monthly_premiums = data?.monthly_premiums || [];
  const delta_distribution = data?.delta_distribution || [];

  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-bold">Dashboard</h2>

      {/* ── KPI cards ────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {netWorth && netWorth.total_net_worth > 0 && (
          <Card
            label="Family Net Worth"
            value={`$${netWorth.total_net_worth.toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
            color="text-green-600"
          />
        )}
        {ytd && (
          <>
            <Card
              label="YTD Trade Income"
              value={`$${ytd.total_premium_collected.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
              color="text-green-600"
            />
            <Card
              label="YTD Losses"
              value={`$${ytd.total_losses.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
              color="text-red-600"
            />
            <Card
              label="YTD Net P&L"
              value={`$${ytd.net_pnl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
              color={ytd.net_pnl >= 0 ? "text-green-600" : "text-red-600"}
            />
          </>
        )}
      </div>

      {!ytd && !netWorth && !data && (
        <p className="text-gray-500">
          No data yet. Add holdings in Portfolio or record trades!
        </p>
      )}

      {/* ── Charts ───────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly premium bar chart */}
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="font-semibold mb-3">Monthly Premium Income</h3>
          {monthly_premiums.length === 0 ? (
            <p className="text-sm text-gray-400">No data yet</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={monthly_premiums}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="total_premium" fill="#22c55e" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Delta distribution pie chart */}
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="font-semibold mb-3">Delta Distribution</h3>
          {delta_distribution.length === 0 ? (
            <p className="text-sm text-gray-400">No data yet</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={delta_distribution}
                  dataKey="count"
                  nameKey="bucket"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={(e) => e.bucket}
                >
                  {delta_distribution.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  );
}

function Card({
  label,
  value,
  color = "text-gray-900",
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
    </div>
  );
}
