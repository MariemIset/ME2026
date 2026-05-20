export default function ChartCard({ title, subtitle, children }) {
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg shadow-black/20">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-white">{title}</h2>
        {subtitle ? <p className="mt-1 text-sm text-slate-400">{subtitle}</p> : null}
      </div>
      <div className="h-72 w-full">{children}</div>
    </section>
  );
}
