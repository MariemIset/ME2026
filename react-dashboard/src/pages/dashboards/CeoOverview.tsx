import { useState, useEffect } from 'react';
import { MetricCard } from '../../components/charts/MetricCard';
import type { KpiData, RevenueChartItem } from '../../services/api';
import { api } from '../../services/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

const CeoOverview = () => {
  const [kpis, setKpis] = useState<KpiData | null>(null);
  const [revenue, setRevenue] = useState<RevenueChartItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [kpiData, revData] = await Promise.all([
          api.getKpis(),
          api.getRevenueChart(),
        ]);
        setKpis(kpiData);
        setRevenue(revData);
      } catch (err) {
        console.error('Failed to load CEO data:', err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const customTooltipStyle = { backgroundColor: '#0f172a', borderColor: '#334155', color: '#f8fafc', borderRadius: '8px', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)' };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><span className="text-slate-400 text-lg">Loading executive overview...</span></div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-white">Executive Overview</h1>
      </div>

      {kpis && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard title="Total Customers" value={kpis.totalCustomers.value.toLocaleString()} goal={kpis.totalCustomers.goal} isPositive={true} />
          <MetricCard title="High Risk of Churn" value={kpis.churnRisk.value.toLocaleString()} goal={kpis.churnRisk.goal} isPositive={false} />
          <MetricCard title="Average CLV" value={"$" + kpis.avgClv.value.toLocaleString()} goal={kpis.avgClv.goal} formatAsCurrency={true} isPositive={true} />
          <MetricCard title="Total Revenue" value={"$" + (kpis.totalRevenue.value / 1000000).toFixed(2) + "M"} goal={kpis.totalRevenue.goal} formatAsCurrency={true} isPositive={true} />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[400px]">
        <div className="bg-slate-900/60 backdrop-blur-md border border-slate-700/50 rounded-2xl shadow-lg p-6 flex flex-col">
          <h3 className="text-white font-bold tracking-wide">Monthly Revenue (2017)</h3>
          <div className="flex-1 mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={revenue}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" stroke="#64748b" />
                <YAxis stroke="#64748b" tickFormatter={(v) => "$" + (v / 1000).toFixed(0) + "k"} />
                <Tooltip contentStyle={customTooltipStyle} />
                <Line type="monotone" dataKey="value" stroke="#e11d48" strokeWidth={3} dot={{ fill: '#e11d48', r: 4 }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-slate-900/60 backdrop-blur-md border border-slate-700/50 rounded-2xl shadow-lg p-6 flex flex-col">
          <h3 className="text-white font-bold tracking-wide">Churn Risk Distribution</h3>
          <div className="flex-1 mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={kpis ? [
                { name: 'Active', value: kpis.totalCustomers.value - kpis.churnRisk.value },
                { name: 'At Risk', value: kpis.churnRisk.value },
              ] : []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip contentStyle={customTooltipStyle} />
                <Bar dataKey="value" fill="#e11d48" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CeoOverview;


