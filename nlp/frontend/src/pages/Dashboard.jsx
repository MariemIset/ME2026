import { useCallback, useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fetchThemes, fetchTrends } from "../api.js";
import ChartCard from "../components/ChartCard.jsx";

const PIE_COLORS = {
  positive: "#34d399",
  negative: "#fb7185",
  neutral: "#94a3b8",
};

function pieFromTotals(totals) {
  return ["positive", "negative", "neutral"].map((key) => ({
    name: key,
    value: totals[key] || 0,
  }));
}

export default function Dashboard() {
  const [trends, setTrends] = useState(null);
  const [themes, setThemes] = useState(null);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [t, th] = await Promise.all([fetchTrends(), fetchThemes()]);
      setTrends(t);
      setThemes(th);
    } catch (e) {
      setError(e.message || "Failed to load dashboard data.");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const pieData = trends ? pieFromTotals(trends.totals || {}) : [];
  const lineData = trends?.by_date || [];
  const barData = themes?.keywords || [];
  const phraseData = (themes?.phrases || []).map((p) => ({
    phrase: p.phrase,
    count: p.count,
  }));
  const complaintTopicData = themes?.complaint_topics || [];

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-white">Dashboard</h2>
          <p className="mt-1 max-w-2xl text-sm text-slate-400">
            Aggregated sentiment, trends over review dates, frequent phrases, and complaint
            themes from comments loaded into the API (PostgreSQL seed plus analyzed reviews).
          </p>
        </div>
        <button
          type="button"
          onClick={load}
          className="self-start rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow hover:bg-indigo-500"
        >
          Refresh
        </button>
      </div>

      {error ? (
        <div className="rounded-xl border border-rose-500/40 bg-rose-950/40 px-4 py-3 text-sm text-rose-100">
          {error}
        </div>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard
          title="Sentiment distribution"
          subtitle="Share of positive, negative, and neutral reviews."
        >
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={pieData}
                dataKey="value"
                nameKey="name"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={2}
              >
                {pieData.map((entry) => (
                  <Cell key={entry.name} fill={PIE_COLORS[entry.name] || "#64748b"} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: "#0f172a", border: "1px solid #1e293b" }}
                labelStyle={{ color: "#e2e8f0" }}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Trend over time"
          subtitle="Counts by sentiment for each review date."
        >
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={lineData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="date" stroke="#94a3b8" tick={{ fill: "#94a3b8", fontSize: 12 }} />
              <YAxis stroke="#94a3b8" tick={{ fill: "#94a3b8", fontSize: 12 }} allowDecimals={false} />
              <Tooltip
                contentStyle={{ background: "#0f172a", border: "1px solid #1e293b" }}
                labelStyle={{ color: "#e2e8f0" }}
              />
              <Legend />
              <Line type="monotone" dataKey="positive" stroke={PIE_COLORS.positive} strokeWidth={2} dot />
              <Line type="monotone" dataKey="negative" stroke={PIE_COLORS.negative} strokeWidth={2} dot />
              <Line type="monotone" dataKey="neutral" stroke={PIE_COLORS.neutral} strokeWidth={2} dot />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard
          title="Frequent keywords"
          subtitle="Token counts after light stopword filtering."
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={barData} layout="vertical" margin={{ left: 8, right: 16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
              <XAxis type="number" stroke="#94a3b8" tick={{ fill: "#94a3b8", fontSize: 12 }} allowDecimals={false} />
              <YAxis
                type="category"
                dataKey="word"
                width={100}
                stroke="#94a3b8"
                tick={{ fill: "#94a3b8", fontSize: 12 }}
              />
              <Tooltip
                contentStyle={{ background: "#0f172a", border: "1px solid #1e293b" }}
                labelStyle={{ color: "#e2e8f0" }}
              />
              <Bar dataKey="count" fill="#818cf8" radius={[0, 6, 6, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Frequent two-word phrases"
          subtitle="Simple bigram counts across the same corpus."
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={phraseData} layout="vertical" margin={{ left: 8, right: 16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
              <XAxis type="number" stroke="#94a3b8" tick={{ fill: "#94a3b8", fontSize: 12 }} allowDecimals={false} />
              <YAxis
                type="category"
                dataKey="phrase"
                width={120}
                stroke="#94a3b8"
                tick={{ fill: "#94a3b8", fontSize: 11 }}
              />
              <Tooltip
                contentStyle={{ background: "#0f172a", border: "1px solid #1e293b" }}
                labelStyle={{ color: "#e2e8f0" }}
              />
              <Bar dataKey="count" fill="#22d3ee" radius={[0, 6, 6, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <ChartCard
        title="Complaint themes"
        subtitle="How many comments mention each topic (keyword-based). One comment can count toward multiple topics."
      >
        {complaintTopicData.length ? (
          <ResponsiveContainer width="100%" height={Math.max(320, complaintTopicData.length * 36)}>
            <BarChart data={complaintTopicData} layout="vertical" margin={{ left: 8, right: 16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
              <XAxis type="number" stroke="#94a3b8" tick={{ fill: "#94a3b8", fontSize: 12 }} allowDecimals={false} />
              <YAxis
                type="category"
                dataKey="topic"
                width={200}
                stroke="#94a3b8"
                tick={{ fill: "#94a3b8", fontSize: 11 }}
              />
              <Tooltip
                contentStyle={{ background: "#0f172a", border: "1px solid #1e293b" }}
                labelStyle={{ color: "#e2e8f0" }}
              />
              <Bar dataKey="count" fill="#f97316" radius={[0, 6, 6, 0]} name="Comments" />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <p className="py-8 text-center text-sm text-slate-500">No complaint topic data yet.</p>
        )}
      </ChartCard>
    </div>
  );
}
