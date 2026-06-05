import { useState, useEffect } from 'react';
import { MetricCard } from '../../components/charts/MetricCard';
import type { KpiData, ChurnStats, ChurnPrediction, CustomerSample } from '../../services/api';
import { api } from '../../services/api';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ScatterChart, Scatter, ResponsiveContainer, Legend } from 'recharts';
import { Filter, Brain, Users } from 'lucide-react';

const ChurnRisk = () => {
  const [kpis, setKpis] = useState<KpiData | null>(null);
  const [churnStats, setChurnStats] = useState<ChurnStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeCards, setActiveCards] = useState<string[]>(["Aurora", "Nova", "Star"]);
  const ALL_PROVINCES = ["Alberta", "British Columbia", "Manitoba", "New Brunswick", "Newfoundland and Labrador", "Nova Scotia", "Ontario", "Prince Edward Island", "Quebec", "Saskatchewan", "Northwest Territories", "Nunavut", "Yukon"];
const [activeProvinces, setActiveProvinces] = useState<string[]>(ALL_PROVINCES);

  const [customerSample, setCustomerSample] = useState<CustomerSample[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<CustomerSample | null>(null);
  const [mlResult, setMlResult] = useState<ChurnPrediction | null>(null);
  const [mlLoading, setMlLoading] = useState(false);
  const [mlError, setMlError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const cards = activeCards.join(",");
        const provs = activeProvinces.join(",");
        const [kpiData, churnData, sample] = await Promise.all([
          api.getKpis(cards, provs),
          api.getChurnStats(cards, provs),
          api.getCustomerSample(),
        ]);
        setKpis(kpiData);
        setChurnStats(churnData);
        setCustomerSample(sample);
      } catch (err) {
        console.error("Failed to load churn data:", err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [activeCards, activeProvinces]);

  const toggleCard = (card: string) => {
    setActiveCards(prev => prev.includes(card) ? prev.filter(c => c !== card) : [...prev, card]);
  };
  const toggleProvince = (prov: string) => {
    setActiveProvinces(prev => prev.includes(prov) ? prev.filter(p => p !== prov) : [...prev, prov]);
  };
  const toggleAllProvinces = () => {
    setActiveProvinces(prev => prev.length === ALL_PROVINCES.length ? [] : [...ALL_PROVINCES]);
  };

  const handleMlPredict = async () => {
    if (!selectedCustomer) return;
    setMlLoading(true);
    setMlError(null);
    setMlResult(null);
    try {
      const result = await api.predictChurn(selectedCustomer.loyaltyNumber);
      setMlResult(result);
    } catch {
      setMlError("Failed to get prediction. Check the loyalty number.");
    } finally {
      setMlLoading(false);
    }
  };

  const COLORS = ["#e11d48", "#fb7185", "#fca5a5"];
  const customTooltipStyle = { backgroundColor: "#0f172a", borderColor: "#334155", color: "#f8fafc", borderRadius: "8px", boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.5)" };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><span className="text-slate-400 text-lg">Loading churn analytics...</span></div>;
  }

  return (
    <div className="space-y-8 pb-12">
      <div className="bg-slate-900/60 backdrop-blur-md border border-slate-700/50 p-5 rounded-2xl shadow-lg flex flex-col md:flex-row gap-6 items-start md:items-center">
        <div className="flex items-center gap-3 text-slate-300 font-semibold w-32">
          <Filter className="w-5 h-5 text-rose-500" /> Filters
        </div>
        <div className="flex-1 flex flex-wrap gap-6">
          <div className="space-y-2">
            <span className="text-xs text-slate-500 uppercase tracking-wider font-bold">Loyalty Cards</span>
            <div className="flex gap-2">
              {["Aurora", "Nova", "Star"].map(card => (
                <button key={card} onClick={() => toggleCard(card)}
                  className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-300 border ${
                    activeCards.includes(card)
                    ? "bg-rose-500/20 text-rose-300 border-rose-500/50 shadow-[0_0_10px_rgba(244,63,94,0.3)]"
                    : "bg-slate-800 text-slate-400 border-slate-700 hover:bg-slate-700 hover:text-slate-300"
                  }`}
                >{card}</button>
              ))}
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500 uppercase tracking-wider font-bold">Provinces</span>
              <button onClick={toggleAllProvinces}
                className="text-xs text-rose-400 hover:text-rose-300 hover:underline transition-colors"
              >{activeProvinces.length === ALL_PROVINCES.length ? "Deselect All" : "Select All"}</button>
            </div>
            <div className="flex gap-2 flex-wrap">
              {ALL_PROVINCES.map(prov => (
                <button key={prov} onClick={() => toggleProvince(prov)}
                  className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-300 border ${
                    activeProvinces.includes(prov)
                    ? "bg-rose-500/20 text-rose-300 border-rose-500/50 shadow-[0_0_10px_rgba(244,63,94,0.3)]"
                    : "bg-slate-800 text-slate-400 border-slate-700 hover:bg-slate-700 hover:text-slate-300"
                  }`}
                >{prov}</button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {kpis && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <MetricCard title="Total Customers" value={kpis.totalCustomers.value.toLocaleString()} goal={kpis.totalCustomers.goal} isPositive={true} />
          <MetricCard title="High Risk of Churn" value={kpis.churnRisk.value.toLocaleString()} goal={kpis.churnRisk.goal} isPositive={false} />
          <MetricCard title="Average CLV" value={"$" + kpis.avgClv.value.toLocaleString()} goal={kpis.avgClv.goal} formatAsCurrency={true} isPositive={true} />
        </div>
      )}

      {churnStats && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[400px]">
            <div className="bg-slate-900/60 backdrop-blur-md border border-slate-700/50 rounded-2xl shadow-lg p-6 flex flex-col">
              <h3 className="text-white font-bold tracking-wide">Churn Rate % by Segment</h3>
              <div className="flex-1 mt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={churnStats.churnBySegment} cx="50%" cy="50%" innerRadius={70} outerRadius={110} dataKey="value" stroke="none">
                      {churnStats.churnBySegment.map((_entry, index) => (
                        <Cell key={"cell-" + index} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={customTooltipStyle} />
                    <Legend verticalAlign="bottom" height={36} iconType="circle" wrapperStyle={{ color: "#cbd5e1" }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="bg-slate-900/60 backdrop-blur-md border border-slate-700/50 rounded-2xl shadow-lg p-6 flex flex-col">
              <h3 className="text-white font-bold tracking-wide">Flight Behavior (Active vs Churned)</h3>
              <div className="flex-1 mt-6">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={churnStats.barData} layout="vertical" margin={{ top: 5, right: 30, left: 10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} vertical={true} stroke="#334155" />
                    <XAxis type="number" tickFormatter={(value) => value + "K"} stroke="#64748b" />
                    <YAxis dataKey="name" type="category" tick={{fontSize: 12, fill: "#cbd5e1"}} width={70} stroke="#64748b" />
                    <Tooltip contentStyle={customTooltipStyle} cursor={{fill: "#1e293b"}} />
                    <Bar dataKey="value" barSize={32} radius={[0, 4, 4, 0]}>
                      {churnStats.barData.map((entry, index) => (
                        <Cell key={"cell-" + index} fill={entry.name === "Active" ? "#10b981" : "#e11d48"} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[400px]">
            <div className="bg-slate-900/60 backdrop-blur-md border border-slate-700/50 rounded-2xl shadow-lg p-6 flex flex-col">
              <h3 className="text-white font-bold tracking-wide">Customer Churn Profile by Flight Behavior</h3>
              <div className="flex-1 mt-6">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" />
                    <XAxis type="number" dataKey="x" name="Flight Count" stroke="#64748b" />
                    <YAxis type="number" dataKey="y" name="CLV" tickFormatter={(v) => (v / 1000).toFixed(0) + "K"} stroke="#64748b" />
                    <Tooltip cursor={{ strokeDasharray: "3 3" }} contentStyle={customTooltipStyle} />
                    <Legend verticalAlign="top" iconType="circle" wrapperStyle={{ color: "#cbd5e1", paddingBottom: "20px" }} />
                    <Scatter name="Active" data={churnStats.scatterActive} fill="#10b981" />
                    <Scatter name="Churned" data={churnStats.scatterChurned} fill="#e11d48" />
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="bg-slate-900/60 backdrop-blur-md border border-slate-700/50 rounded-2xl shadow-lg p-6 flex flex-col">
              <h3 className="text-white font-bold tracking-wide flex items-center gap-2"><Brain className="w-5 h-5 text-rose-500" /> ML Churn Predictor</h3>
              <div className="flex-1 flex flex-col items-center justify-center gap-4">
                <div className="flex gap-2 w-full max-w-xs">
                  <div className="relative flex-1">
                    <Users className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                    <select
                      value={selectedCustomer?.loyaltyNumber ?? ""}
                      onChange={(e) => {
                        const cust = customerSample.find(c => c.loyaltyNumber === parseInt(e.target.value));
                        setSelectedCustomer(cust ?? null);
                        setMlResult(null);
                        setMlError(null);
                      }}
                      className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg pl-9 pr-3 py-2 text-sm appearance-none focus:outline-none focus:border-rose-500"
                    >
                      <option value="" disabled>Select a customer...</option>
                      {customerSample.map(c => (
                        <option key={c.loyaltyNumber} value={c.loyaltyNumber}>
                          #{c.loyaltyNumber} — {c.city}, {c.province} ({c.loyaltyCard})
                        </option>
                      ))}
                    </select>
                  </div>
                  <button
                    onClick={handleMlPredict}
                    disabled={mlLoading || !selectedCustomer}
                    className="bg-rose-500 hover:bg-rose-600 text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50 transition-colors"
                  >
                    {mlLoading ? "..." : "Predict"}
                  </button>
                </div>

                {selectedCustomer && !mlResult && !mlError && (
                  <div className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-3 w-full max-w-xs text-xs text-slate-400 space-y-1">
                    <p><span className="text-slate-500">Card:</span> {selectedCustomer.loyaltyCard}</p>
                    <p><span className="text-slate-500">CLV:</span> ${selectedCustomer.clv.toLocaleString()}</p>
                    <p><span className="text-slate-500">Enrollment:</span> {selectedCustomer.enrollmentType}</p>
                    <p><span className="text-slate-500">Status:</span> {selectedCustomer.isChurned ? <span className="text-red-400">Churned</span> : <span className="text-emerald-400">Active</span>}</p>
                  </div>
                )}

                {mlResult && (
                  <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 w-full max-w-xs text-center">
                    <p className="text-slate-400 text-sm">Churn Probability</p>
                    <p className="text-3xl font-black text-white">{(mlResult.churn_probability * 100).toFixed(1)}%</p>
                    <span className={"inline-block mt-2 px-3 py-1 rounded-full text-xs font-bold " + (mlResult.churn_risk_tier === "HIGH" ? "bg-red-500/20 text-red-300" : "bg-emerald-500/20 text-emerald-300")}>
                      {mlResult.churn_risk_tier} RISK
                    </span>
                  </div>
                )}

                {mlError && <p className="text-red-400 text-sm">{mlError}</p>}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ChurnRisk;







