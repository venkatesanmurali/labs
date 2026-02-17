import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { settingsApi } from "../api/client";
import type { StrategyConfig } from "../types";

interface FieldDef {
  key: keyof StrategyConfig;
  label: string;
  step?: string;
  group: string;
}

const FIELDS: FieldDef[] = [
  { key: "target_delta_min", label: "Target Delta Min", step: "0.01", group: "Delta & DTE" },
  { key: "target_delta_max", label: "Target Delta Max", step: "0.01", group: "Delta & DTE" },
  { key: "preferred_dte_min", label: "Preferred DTE Min", step: "1", group: "Delta & DTE" },
  { key: "preferred_dte_max", label: "Preferred DTE Max", step: "1", group: "Delta & DTE" },
  {
    key: "min_annualized_yield",
    label: "Min Annualised Yield (%)",
    step: "0.5",
    group: "Filters",
  },
  {
    key: "max_assignment_probability",
    label: "Max Assignment Prob (%)",
    step: "1",
    group: "Filters",
  },
  {
    key: "avoid_earnings_before_days",
    label: "Avoid Earnings Before (days)",
    step: "1",
    group: "Filters",
  },
  {
    key: "avoid_earnings_after_days",
    label: "Avoid Earnings After (days)",
    step: "1",
    group: "Filters",
  },
  { key: "min_open_interest", label: "Min Open Interest", step: "1", group: "Filters" },
  { key: "min_volume", label: "Min Volume", step: "1", group: "Filters" },
  { key: "w_yield", label: "Weight: Yield", step: "0.05", group: "Scoring Weights" },
  { key: "w_delta_fit", label: "Weight: Delta Fit", step: "0.05", group: "Scoring Weights" },
  { key: "w_liquidity", label: "Weight: Liquidity", step: "0.05", group: "Scoring Weights" },
  { key: "w_distance", label: "Weight: Distance", step: "0.05", group: "Scoring Weights" },
  {
    key: "w_earnings_safety",
    label: "Weight: Earnings Safety",
    step: "0.05",
    group: "Scoring Weights",
  },
  { key: "roll_max_debit", label: "Roll Max Debit ($)", step: "0.10", group: "Roll Engine" },
];

export default function Settings() {
  const [config, setConfig] = useState<StrategyConfig | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    settingsApi
      .get()
      .then(setConfig)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    if (!config) return;
    try {
      const updated = await settingsApi.update(config);
      setConfig(updated);
      toast.success("Settings saved");
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  if (loading) return <p className="text-gray-500">Loading settings...</p>;
  if (!config) return <p className="text-red-500">Failed to load settings.</p>;

  const groups = [...new Set(FIELDS.map((f) => f.group))];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Strategy Settings</h2>

      {groups.map((group) => (
        <div key={group} className="bg-white rounded-lg shadow p-4 space-y-3">
          <h3 className="font-semibold text-gray-700">{group}</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {FIELDS.filter((f) => f.group === group).map((f) => (
              <div key={f.key}>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  {f.label}
                </label>
                <input
                  type="number"
                  step={f.step || "any"}
                  className="w-full border rounded px-2 py-1.5 text-sm"
                  value={(config as any)[f.key] ?? ""}
                  onChange={(e) =>
                    setConfig({ ...config, [f.key]: +e.target.value })
                  }
                />
              </div>
            ))}
          </div>
        </div>
      ))}

      <button
        onClick={handleSave}
        className="bg-brand-600 text-white rounded px-6 py-2 text-sm font-medium hover:bg-brand-700"
      >
        Save Settings
      </button>
    </div>
  );
}
