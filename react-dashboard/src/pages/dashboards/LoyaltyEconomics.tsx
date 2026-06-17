import { useState, useEffect } from 'react';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Cell } from 'recharts';
import { Filter, Sparkles, Users } from 'lucide-react';
import { MetricCard } from '../../components/charts/MetricCard';
import type { LoyaltyStats, LoyaltyTimelineItem, LoyaltyRecommendation, CustomerSample } from '../../services/api';
import { api } from '../../services/api';

const LoyaltyEconomics = () => {
  const [stats, setStats] = useState<LoyaltyStats | null>(null);
  const [timeline, setTimeline] = useState<LoyaltyTimelineItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeCards, setActiveCards] = useState<string[]>(["Aurora", "Nova", "Star"]);
  const ALL_PROVINCES = ["Alberta", "British Columbia", "Manitoba", "New Brunswick", "Newfoundland and Labrador", "Nova Scotia", "Ontario", "Prince Edward Island", "Quebec", "Saskatchewan", "Northwest Territories", "Nunavut", "Yukon"];
const [activeProvinces, setActiveProvinces] = useState<string[]>(ALL_PROVINCES);

  const [customerSample, setCustomerSample] = useState<CustomerSample[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<CustomerSample | null>(null);
  const [mlResult, setMlResult] = useState<LoyaltyRecommendation[] | null>(null);
  const [mlLoading, setMlLoading] = useState(false);
  const [mlError, setMlError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const cards = activeCards.join(",");
        const provs = activeProvinces.join(",");
        const [statsData, timelineData, sample] = await Promise.all([
          api.getLoyaltyStats(cards, provs),
          api.getLoyaltyTimeline(cards, provs),
          api.getCustomerSample(),
        ]);
        setStats(statsData);
        setTimeline(timelineData);
        setCustomerSample(sample);
      } catch (err) {
        console.error("Failed to load loyalty data:", err);
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

  const handleMlRecommend = async () => {
    if (!selectedCustomer) return;
    setMlLoading(true);
    setMlError(null);
    setMlResult(null);
    try {
      const result = await api.predictRecommendation(selectedCustomer.loyaltyNumber);
      setMlResult(result);
    } catch {
      setMlError("Failed to get recommendation.");
    } finally {
      setMlLoading(false);
    }
  };

  const customTooltipStyle = { backgroundColor: "#0f172a", borderColor: "#334155", color: "#f8fafc", borderRadius: "8px", boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.5)" };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><span className="text-slate-400 text-lg">Loading loyalty analytics...</span></div>;
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

      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard title="Gold Tier Members" value={stats.goldTier.toLocaleString()} goal={5000} isPositive={true} />
          <MetricCard title="Avg Points Earned" value={Math.round(stats.avgPoints).toLocaleString()} goal={15000} />
          <MetricCard title="Redemption Rate" value={stats.redemptionRate.toFixed(1) + "%"} goal={75} isPositive={true} />
          <MetricCard title="Dollar Cost Redeemed" value={"$" + (stats.dollarCost / 1000000).toFixed(2) + "M"} goal={5000000} formatAsCurrency={true} />
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 h-[400px]">
        <div className="bg-slate-900/60 backdrop-blur-md border border-slate-700/50 rounded-2xl shadow-lg p-6 flex flex-col">
          <h3 className="text-white font-bold tracking-wide">Points Accumulated vs Redeemed (2017)</h3>
          <div className="flex-1 mt-6">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={timeline} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <defs>
                  <linearGradient id="colorAcc" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#e11d48" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#e11d48" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorRed" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" />
                <XAxis dataKey="name" tick={{fontSize: 12, fill: "#64748b"}} stroke="#334155" />
                <YAxis tickFormatter={(v) => v + "K"} tick={{fontSize: 12, fill: "#64748b"}} stroke="#334155" />
                <Tooltip contentStyle={customTooltipStyle} />
                <Legend verticalAlign="top" iconType="circle" wrapperStyle={{ color: "#cbd5e1", paddingBottom: "20px" }} />
                <Area type="monotone" dataKey="accumulated" name="Points Accumulated" stroke="#e11d48" strokeWidth={3} fillOpacity={1} fill="url(#colorAcc)" />
                <Area type="monotone" dataKey="redeemed" name="Points Redeemed" stroke="#8b5cf6" strokeWidth={3} fillOpacity={1} fill="url(#colorRed)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {stats && (
          <div className="bg-slate-900/60 backdrop-blur-md border border-slate-700/50 rounded-2xl shadow-lg p-6 flex flex-col">
            <h3 className="text-white font-bold tracking-wide">Customer Segmentation</h3>
            <div className="flex-1 mt-6">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={stats.segmentation} layout="vertical" margin={{ top: 5, right: 30, left: 30, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} vertical={true} stroke="#334155" />
                  <XAxis type="number" stroke="#64748b" />
                  <YAxis dataKey="name" type="category" tick={{fontSize: 12, fill: "#cbd5e1"}} width={70} stroke="#64748b" />
                  <Tooltip contentStyle={customTooltipStyle} cursor={{fill: "#1e293b"}} />
                  <Bar dataKey="value" barSize={40} radius={[0, 4, 4, 0]}>
                    {stats.segmentation.map((_entry, index) => (
                      <Cell key={"cell-" + index} fill={index === 0 ? "#e11d48" : index === 1 ? "#8b5cf6" : "#fb7185"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        <div className="bg-slate-900/60 backdrop-blur-md border border-slate-700/50 rounded-2xl shadow-lg p-6 flex flex-col">
          <h3 className="text-white font-bold tracking-wide flex items-center gap-2"><Sparkles className="w-5 h-5 text-purple-500" /> ML Recommendation Engine</h3>
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
                  className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg pl-9 pr-3 py-2 text-sm appearance-none focus:outline-none focus:border-purple-500"
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
                onClick={handleMlRecommend}
                disabled={mlLoading || !selectedCustomer}
                className="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50 transition-colors"
              >
                {mlLoading ? "..." : "Get Rec"}
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

            {mlResult && mlResult[0] && (
              <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 w-full max-w-xs text-center space-y-2">
                <p className="text-purple-400 text-sm font-bold">{mlResult[0].segment_label}</p>
                <p className="text-slate-300 text-sm">Redemption Probability: <span className="text-white font-bold">{(mlResult[0].redemption_proba * 100).toFixed(0)}%</span></p>
                <p className="text-slate-300 text-sm">Recommended: <span className="text-emerald-400 font-bold">{mlResult[0].recommended_reward}</span></p>
                <p className="text-slate-300 text-sm">Expected Value: <span className="text-white font-bold">{"$" + mlResult[0].expected_value.toFixed(2)}</span></p>
              </div>
            )}

            {mlError && <p className="text-red-400 text-sm">{mlError}</p>}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoyaltyEconomics;







