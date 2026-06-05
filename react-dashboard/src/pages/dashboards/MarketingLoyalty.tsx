import { useState, useEffect } from 'react';
import { MetricCard } from '../../components/charts/MetricCard';
import type { LoyaltyStats } from '../../services/api';
import { api } from '../../services/api';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Legend } from 'recharts';

const MarketingLoyalty = () => {
  const [stats, setStats] = useState<LoyaltyStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await api.getLoyaltyStats();
        setStats(data);
      } catch (err) {
        console.error("Failed to load marketing loyalty data:", err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const COLORS = ["#e11d48", "#8b5cf6", "#fb7185"];
  const customTooltipStyle = { backgroundColor: "#0f172a", borderColor: "#334155", color: "#f8fafc", borderRadius: "8px", boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.5)" };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><span className="text-slate-400 text-lg">Loading loyalty data...</span></div>;
  }

  const engagementData = [
    { name: "Gold Tier", active: stats ? stats.goldTier : 0, inactive: 0 },
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-white">Loyalty & Segmentation</h1>
      </div>

      {stats && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <MetricCard title="Gold Tier Members" value={stats.goldTier.toLocaleString()} goal={5000} isPositive={true} />
            <MetricCard title="Avg Points Earned" value={Math.round(stats.avgPoints).toLocaleString()} goal={15000} />
            <MetricCard title="Redemption Rate" value={stats.redemptionRate.toFixed(1) + "%"} goal={75} isPositive={stats.redemptionRate >= 68} />
            <MetricCard title="Liability" value={stats.liability.toFixed(2) + "bn"} goal={2.5} isPositive={stats.liability <= 2.5} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="bg-slate-900/60 backdrop-blur-md border border-slate-700/50 rounded-2xl shadow-lg p-6">
              <h3 className="text-lg font-semibold mb-4 text-white">Customer Segments</h3>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={stats.segmentation} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={5} dataKey="value" stroke="none">
                      {stats.segmentation.map((_entry, index) => (
                        <Cell key={"cell-" + index} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={customTooltipStyle} />
                    <Legend verticalAlign="bottom" iconType="circle" wrapperStyle={{ color: "#cbd5e1" }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="lg:col-span-2 bg-slate-900/60 backdrop-blur-md border border-slate-700/50 rounded-2xl shadow-lg p-6">
              <h3 className="text-lg font-semibold mb-4 text-white">Gold Tier Activity</h3>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={engagementData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
                    <XAxis dataKey="name" stroke="#64748b" />
                    <YAxis stroke="#64748b" />
                    <Tooltip contentStyle={customTooltipStyle} />
                    <Area type="monotone" dataKey="active" stackId="1" stroke="#e11d48" fill="#e11d48" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default MarketingLoyalty;



