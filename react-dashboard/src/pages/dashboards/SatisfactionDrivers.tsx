import { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Filter, Lightbulb, Sparkles } from 'lucide-react';
import { MetricCard } from '../../components/charts/MetricCard';
import type { SatisfactionStats } from '../../services/api';
import { api } from '../../services/api';

const SatisfactionDrivers = () => {
  const [stats, setStats] = useState<SatisfactionStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTravel, setActiveTravel] = useState<string[]>(["Personal"]);
  const [activeClass, setActiveClass] = useState<string[]>(["Economy Plus"]);
  const [activeTab, setActiveTab] = useState<"influencers" | "segments">("influencers");

  const [satisfactionGoal, setSatisfactionGoal] = useState("Satisfied");
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<string | null>(null);

  const toggleTravel = (t: string) => setActiveTravel(prev => prev.includes(t) ? prev.filter(c => c !== t) : [...prev, t]);
  const toggleClass = (c: string) => setActiveClass(prev => prev.includes(c) ? prev.filter(p => p !== c) : [...prev, c]);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const travels = activeTravel.join(",");
        const classes = activeClass.join(",");
        const data = await api.getSatisfactionStats(travels, classes);
        setStats(data);
      } catch (err) {
        console.error("Failed to load satisfaction data:", err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [activeTravel, activeClass]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setAnalyzing(true);
    setAnalysisResult(null);
    const timer = setTimeout(() => {
      setAnalyzing(false);
      if (satisfactionGoal === "Satisfied") {
        setAnalysisResult("Strong correlation found! When " + activeClass.join(", ") + " passengers travel for " + activeTravel.join(", ") + " reasons, legroom is the primary driver of satisfaction.");
      } else {
        setAnalysisResult("Warning: When " + activeClass.join(", ") + " passengers travel for " + activeTravel.join(", ") + " reasons, poor food quality and flight delays are the leading causes of dissatisfaction.");
      }
    }, 1500);
    return () => clearTimeout(timer);
  }, [activeTravel, activeClass, satisfactionGoal, activeTab]);

  const COLORS = ["#10b981", "#ef4444"];
  const customTooltipStyle = { backgroundColor: "#0f172a", borderColor: "#334155", color: "#f8fafc", borderRadius: "8px", boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.5)" };

  const getScoreColor = (score: number) => {
    if (score >= 4.0) return "text-emerald-400";
    if (score >= 3.0) return "text-yellow-400";
    return "text-rose-500";
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><span className="text-slate-400 text-lg">Loading satisfaction analytics...</span></div>;
  }

  return (
    <div className="space-y-8 pb-12">
      <div className="bg-slate-900/60 backdrop-blur-md border border-slate-700/50 p-5 rounded-2xl shadow-lg flex flex-col md:flex-row gap-6 items-start md:items-center">
        <div className="flex items-center gap-3 text-slate-300 font-semibold w-32">
          <Filter className="w-5 h-5 text-emerald-500" /> Filters
        </div>
        <div className="flex-1 flex flex-wrap gap-6">
          <div className="space-y-2">
            <span className="text-xs text-slate-500 uppercase tracking-wider font-bold">Travel Type</span>
            <div className="flex gap-2">
              {["Business", "Personal"].map(item => (
                <button key={item} onClick={() => toggleTravel(item)}
                  className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-300 border ${
                    activeTravel.includes(item)
                    ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/50 shadow-[0_0_10px_rgba(16,185,129,0.3)]"
                    : "bg-slate-800 text-slate-400 border-slate-700 hover:bg-slate-700 hover:text-slate-300"
                  }`}
                >{item}</button>
              ))}
            </div>
          </div>
          <div className="space-y-2">
            <span className="text-xs text-slate-500 uppercase tracking-wider font-bold">Flight Class</span>
            <div className="flex gap-2 flex-wrap">
              {["Business", "Economy", "Economy Plus"].map(item => (
                <button key={item} onClick={() => toggleClass(item)}
                  className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-300 border ${
                    activeClass.includes(item)
                    ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/50 shadow-[0_0_10px_rgba(16,185,129,0.3)]"
                    : "bg-slate-800 text-slate-400 border-slate-700 hover:bg-slate-700 hover:text-slate-300"
                  }`}
                >{item}</button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {stats && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <MetricCard title="Net Promoter Score" value={stats.nps} goal={60} isPositive={stats.nps >= 40} />
            <MetricCard title="Ticket Volume" value={stats.volume.toLocaleString()} goal={10000} isPositive={stats.volume <= 10000} />
            <MetricCard title="Total Satisfaction" value={stats.pieData[0]?.value.toFixed(1) + "%"} goal={50} isPositive={(stats.pieData[0]?.value || 0) >= 50} />
            <MetricCard title="In-flight WiFi" value={stats.wifi + "/5"} goal={4.0} isPositive={stats.wifi >= 3.0} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-[1fr_2fr] gap-6 h-[350px]">
            <div className="bg-slate-900/60 backdrop-blur-md border border-slate-700/50 rounded-2xl shadow-lg p-6 flex flex-col">
              <h3 className="text-white font-bold tracking-wide">Satisfied Passenger %</h3>
              <div className="flex-1 mt-4 relative">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={stats.pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" stroke="none"
                      label={({ cx, cy, midAngle = 0, outerRadius, value, index }) => {
                        const RADIAN = Math.PI / 180;
                        const radius = outerRadius * 1.25;
                        const x = cx + radius * Math.cos(-midAngle * RADIAN);
                        const y = cy + radius * Math.sin(-midAngle * RADIAN);
                        return (<text x={x} y={y} fill={COLORS[index % COLORS.length]} textAnchor={x > cx ? "start" : "end"} dominantBaseline="central" fontSize="14" fontWeight="bold">{value}%</text>);
                      }}
                    >
                      {stats.pieData.map((_entry, index) => (<Cell key={"cell-" + index} fill={COLORS[index % COLORS.length]} />))}
                    </Pie>
                    <Tooltip contentStyle={customTooltipStyle} />
                    <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ color: "#cbd5e1" }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="bg-slate-900/60 backdrop-blur-md border border-slate-700/50 rounded-2xl shadow-lg p-6 flex flex-col overflow-hidden">
              <h3 className="text-white font-bold tracking-wide mb-6">The Pain-Point Heatmap</h3>
              <div className="flex-1 overflow-x-auto rounded-xl border border-slate-700/50">
                <table className="w-full text-sm text-left text-slate-300">
                  <thead className="text-xs text-slate-400 bg-slate-800/80 border-b border-slate-700">
                    <tr>
                      <th className="px-6 py-4 font-semibold uppercase tracking-wider">Flight Class</th>
                      <th className="px-6 py-4 font-semibold uppercase tracking-wider text-right">Avg Leg Room</th>
                      <th className="px-6 py-4 font-semibold uppercase tracking-wider text-right">Avg WiFi Score</th>
                      <th className="px-6 py-4 font-semibold uppercase tracking-wider text-right">Avg Food Score</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-700/50">
                    {stats.heatmap.map((row) => (
                      <tr key={row.name} className="hover:bg-slate-800/50 transition-colors">
                        <td className="px-6 py-4 font-bold text-white">{row.name}</td>
                        <td className={"px-6 py-4 text-right font-medium " + getScoreColor(row.legRoom)}>{row.legRoom.toFixed(2)}</td>
                        <td className={"px-6 py-4 text-right font-medium " + getScoreColor(row.wifi)}>{row.wifi.toFixed(2)}</td>
                        <td className={"px-6 py-4 text-right font-medium " + getScoreColor(row.food)}>{row.food.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-[1fr_2fr] gap-6 min-h-[350px]">
            <div className="bg-slate-900/60 backdrop-blur-md border border-slate-700/50 rounded-2xl shadow-lg p-6 flex flex-col">
              <h3 className="text-white font-bold tracking-wide mb-4">Impact of Delays by Inflight Score</h3>
              <div className="flex-1">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart margin={{ top: 10, right: 10, bottom: 10, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" />
                    <XAxis type="number" dataKey="x" tick={{fontSize: 10, fill: "#64748b"}} stroke="#334155" />
                    <YAxis type="number" dataKey="y" domain={[0, 5]} ticks={[1,2,3,4,5]} tick={{fontSize: 10, fill: "#64748b"}} width={20} stroke="#334155" />
                    <Tooltip cursor={{ strokeDasharray: "3 3" }} contentStyle={customTooltipStyle} />
                    <Scatter data={stats.scatter} fill="#8b5cf6" />
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="bg-slate-900/60 backdrop-blur-md border border-slate-700/50 rounded-2xl shadow-lg p-6 flex flex-col overflow-hidden">
              <div className="absolute top-[-50px] right-[-50px] w-64 h-64 bg-emerald-500/10 rounded-full blur-[80px] pointer-events-none"></div>
              <div className="flex border-b border-slate-700/50 mb-6 pb-3">
                <span onClick={() => setActiveTab("influencers")}
                  className={"font-bold text-sm pb-3 px-2 mr-6 cursor-pointer transition-colors " + (activeTab === "influencers" ? "text-white border-b-2 border-emerald-500" : "text-slate-500 hover:text-slate-300")}
                >Key influencers</span>
                <span onClick={() => setActiveTab("segments")}
                  className={"font-bold text-sm pb-3 px-2 cursor-pointer transition-colors " + (activeTab === "segments" ? "text-white border-b-2 border-emerald-500" : "text-slate-500 hover:text-slate-300")}
                >Top segments</span>
              </div>
              <div className="flex items-center gap-3 mb-6 z-10 relative">
                <span className="text-sm text-slate-400">{activeTab === "influencers" ? "What influences overall_satisfaction to be" : "When is overall_satisfaction more likely to be"}</span>
                <select value={satisfactionGoal} onChange={(e) => setSatisfactionGoal(e.target.value)}
                  className="bg-slate-800 border border-slate-700 text-white rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-emerald-500"
                >
                  <option value="Satisfied">Satisfied</option>
                  <option value="Dissatisfied">Dissatisfied</option>
                </select>
              </div>
              {analyzing ? (
                <div className="flex-1 bg-slate-800/30 rounded-xl border border-slate-700/50 flex flex-col items-center justify-center p-8 text-center">
                  <div className="flex flex-col items-center animate-pulse">
                    <Lightbulb className="w-12 h-12 text-emerald-500/50 mb-4 animate-bounce" />
                    <span className="text-sm font-medium text-emerald-400">Running AI Analysis...</span>
                  </div>
                </div>
              ) : (
                <div className="flex-1 bg-slate-800/30 rounded-xl border border-slate-700/50 flex flex-col items-center justify-center p-8 text-center">
                  {activeTab === "influencers" ? (
                    <div className="flex flex-col items-center">
                      <Sparkles className="w-8 h-8 text-emerald-400 mb-4" />
                      <p className="text-slate-300 text-lg leading-relaxed max-w-lg">{analysisResult}</p>
                    </div>
                  ) : (
                    <p className="text-slate-300">Segment analysis based on filtered criteria.</p>
                  )}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default SatisfactionDrivers;










