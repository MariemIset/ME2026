import { NavLink, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard.jsx";
import Analyze from "./pages/Analyze.jsx";

function NavItem({ to, children }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        [
          "rounded-lg px-4 py-2 text-sm font-medium transition",
          isActive
            ? "bg-indigo-500/20 text-indigo-200 ring-1 ring-indigo-400/40"
            : "text-slate-400 hover:bg-slate-800 hover:text-slate-100",
        ].join(" ")
      }
    >
      {children}
    </NavLink>
  );
}

export default function App() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-indigo-300">
              ME2026 · NLP
            </p>
            <h1 className="text-xl font-semibold text-white">Customer review sentiment</h1>
          </div>
          <nav className="flex gap-2">
            <NavItem to="/">Dashboard</NavItem>
            <NavItem to="/analyze">Submit feedback</NavItem>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/analyze" element={<Analyze />} />
        </Routes>
      </main>
    </div>
  );
}
