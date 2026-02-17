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
import { journalApi } from "../api/client";
import type { AnalyticsDashboard } from "../types";

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
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    journalApi
      .dashboard()
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading)
    return <p className="text-gray-500">Loading dashboard...</p>;

  if (!data)
    return (
      <p className="text-gray-500">
        No journal data yet. Sell some covered calls and save to the journal!
      </p>
    );

  const { monthly_premiums, delta_distribution, pnl } = data;

  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-bold">Dashboard</h2>

      {/* ── KPI cards ────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card
          label="Premium Collected"
          value={`$${pnl.total_premium_collected.toLocaleString()}`}
        />
        <Card
          label="Realized P&L"
          value={`$${pnl.realized_pnl.toLocaleString()}`}
          color={pnl.realized_pnl >= 0 ? "text-green-600" : "text-red-600"}
        />
        <Card label="Open Positions" value={String(pnl.open_positions)} />
        <Card
          label="Unrealized (est.)"
          value={`$${pnl.unrealized_estimate.toLocaleString()}`}
        />
      </div>

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
