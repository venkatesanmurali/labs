import { Routes, Route, NavLink } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Portfolio from "./pages/Portfolio";
import Recommendations from "./pages/Recommendations";
import RollAssistant from "./pages/RollAssistant";
import Settings from "./pages/Settings";

const NAV = [
  { to: "/", label: "Dashboard" },
  { to: "/portfolio", label: "Portfolio" },
  { to: "/recommendations", label: "Recommendations" },
  { to: "/roll", label: "Roll Assistant" },
  { to: "/settings", label: "Settings" },
];

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* ── Top nav ──────────────────────────────────────────────────── */}
      <header className="bg-gray-900 text-white">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <h1 className="text-xl font-bold tracking-tight">IncomePilot</h1>
          <nav className="flex gap-1">
            {NAV.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                end={n.to === "/"}
                className={({ isActive }) =>
                  `px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-brand-600 text-white"
                      : "text-gray-300 hover:text-white hover:bg-gray-700"
                  }`
                }
              >
                {n.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      {/* ── Page content ─────────────────────────────────────────────── */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/portfolio" element={<Portfolio />} />
          <Route path="/recommendations" element={<Recommendations />} />
          <Route path="/roll" element={<RollAssistant />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>

      <footer className="text-center text-xs text-gray-400 py-3">
        IncomePilot v0.1 &mdash; Decision intelligence for covered-call investors
      </footer>
    </div>
  );
}
