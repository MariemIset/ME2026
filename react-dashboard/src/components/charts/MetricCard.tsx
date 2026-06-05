
interface MetricCardProps {
  title: string;
  value: string | number;
  trend?: string;
  isPositive?: boolean;
  goal?: number;
  formatAsCurrency?: boolean;
}

export const MetricCard = ({ title, value, trend, isPositive, goal, formatAsCurrency }: MetricCardProps) => {
  const numValue = typeof value === 'string' ? parseFloat(value.replace(/[^0-9.-]+/g, "")) : value;
  let progressPercentage = 0;
  if (goal && !isNaN(numValue)) {
    progressPercentage = Math.min(100, Math.max(0, (numValue / goal) * 100));
  }

  const formattedGoal = goal ? (formatAsCurrency ? `$${goal.toLocaleString()}` : goal.toLocaleString()) : null;

  return (
    <div className="bg-slate-900/60 backdrop-blur-md border border-slate-700/50 p-6 rounded-2xl shadow-lg flex flex-col justify-between relative overflow-hidden group hover:border-slate-600 transition-colors">
      {/* Subtle glow effect on hover */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-rose-500/5 rounded-full blur-2xl group-hover:bg-rose-500/10 transition-colors pointer-events-none"></div>

      <div className="relative z-10">
        <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wider">{title}</h3>
        <div className="mt-3 flex items-baseline gap-3">
          <p className="text-4xl font-black text-white tracking-tight">{value}</p>
          {trend && (
            <span className={`text-sm font-bold px-2 py-1 rounded-md bg-opacity-10 backdrop-blur-sm ${isPositive ? 'text-emerald-400 bg-emerald-500/10 border border-emerald-500/20' : 'text-rose-400 bg-rose-500/10 border border-rose-500/20'}`}>
              {trend}
            </span>
          )}
        </div>
      </div>
      
      {goal && (
        <div className="mt-6 pt-4 border-t border-slate-700/50 relative z-10">
          <div className="flex justify-between text-xs mb-2">
            <span className="text-slate-400 font-medium">Progress</span>
            <span className="font-bold text-slate-300">Goal: {formattedGoal}</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden shadow-inner">
            <div 
              className={`h-full rounded-full transition-all duration-1000 ease-out relative ${progressPercentage > 90 ? 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]' : 'bg-gradient-to-r from-rose-600 to-rose-400 shadow-[0_0_10px_rgba(244,63,94,0.5)]'}`} 
              style={{ width: `${progressPercentage}%` }}
            >
              {/* Shine effect on the progress bar */}
              <div className="absolute top-0 left-0 right-0 bottom-0 bg-white/20 blur-[1px]"></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
