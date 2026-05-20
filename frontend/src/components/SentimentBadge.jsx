const styles = {
  positive: "bg-emerald-500/15 text-emerald-200 ring-emerald-400/30",
  negative: "bg-rose-500/15 text-rose-200 ring-rose-400/30",
  neutral: "bg-slate-500/15 text-slate-200 ring-slate-400/30",
};

export default function SentimentBadge({ sentiment }) {
  const cls = styles[sentiment] || styles.neutral;
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide ring-1 ${cls}`}
    >
      {sentiment}
    </span>
  );
}
