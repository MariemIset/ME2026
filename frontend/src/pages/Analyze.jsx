import { useMemo, useState } from "react";
import { analyzeReviews, fetchSampleReviews } from "../api.js";
import CommentForm from "../components/CommentForm.jsx";
import SentimentBadge from "../components/SentimentBadge.jsx";

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function parseInput(raw) {
  const text = raw.trim();
  if (!text) return [];

  if (text.startsWith("[")) {
    const data = JSON.parse(text);
    if (!Array.isArray(data)) throw new Error("JSON must be an array of objects.");
    return data.map((row, i) => {
      if (!row || typeof row.review !== "string") {
        throw new Error(`Item ${i + 1} must include a string "review" field.`);
      }
      return {
        review: row.review,
        date: row.date || todayIso(),
      };
    });
  }

  return text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((review) => ({ review, date: todayIso() }));
}

export default function Analyze() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [results, setResults] = useState([]);

  const hint = useMemo(
    () =>
      'Paste one review per line, or paste a JSON array like [{"review":"...","date":"2024-01-01"}].',
    []
  );

  async function handleAnalyze() {
    setError(null);
    setLoading(true);
    setResults([]);
    try {
      const reviews = parseInput(text);
      if (!reviews.length) {
        throw new Error("Add at least one review.");
      }
      const data = await analyzeReviews(reviews);
      setResults(data.results || []);
    } catch (e) {
      setError(e.message || "Analysis failed.");
    } finally {
      setLoading(false);
    }
  }

  async function handleLoadSample() {
    setError(null);
    setLoading(true);
    try {
      const sample = await fetchSampleReviews();
      setText(JSON.stringify(sample, null, 2));
    } catch (e) {
      setError(e.message || "Could not load sample reviews.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-semibold text-white">Submit feedback</h2>
        <p className="mt-1 max-w-3xl text-sm text-slate-400">
          Share a single comment below, or use the bulk import section for many reviews at once.
        </p>
      </div>

      <CommentForm onSubmitted={(row) => setResults((prev) => [row, ...prev])} />

      <details className="group rounded-2xl border border-slate-800 bg-slate-900/40">
        <summary className="cursor-pointer list-none px-5 py-4 text-sm font-medium text-slate-200 marker:content-none [&::-webkit-details-marker]:hidden">
          <span className="text-indigo-300 group-open:hidden">▸</span>
          <span className="hidden text-indigo-300 group-open:inline">▾</span> Import multiple
          reviews (advanced)
        </summary>
        <div className="border-t border-slate-800 px-5 pb-5 pt-2">
          <p className="mb-4 text-sm text-slate-400">{hint}</p>

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="space-y-3">
              <label className="block text-sm font-medium text-slate-300" htmlFor="reviews">
                Reviews
              </label>
              <textarea
                id="reviews"
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={14}
                placeholder={'e.g. "Loved the packaging" on its own line, or paste JSON...'}
                className="w-full resize-y rounded-xl border border-slate-800 bg-slate-900/80 p-4 font-mono text-sm text-slate-100 outline-none ring-indigo-500/0 transition focus:border-indigo-500/60 focus:ring-2"
              />
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={handleAnalyze}
                  disabled={loading}
                  className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {loading ? "Analyzing…" : "Run sentiment analysis"}
                </button>
                <button
                  type="button"
                  onClick={handleLoadSample}
                  disabled={loading}
                  className="rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-sm font-medium text-slate-100 hover:border-slate-500 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  Load sample JSON
                </button>
              </div>
              {error ? (
                <div className="rounded-lg border border-rose-500/40 bg-rose-950/40 px-3 py-2 text-sm text-rose-100">
                  {error}
                </div>
              ) : null}
            </div>

            <div className="space-y-3">
              <h3 className="text-sm font-medium text-slate-300">Results</h3>
              <div className="max-h-[32rem] space-y-3 overflow-y-auto rounded-xl border border-slate-800 bg-slate-900/50 p-3">
                {!results.length ? (
                  <p className="text-sm text-slate-500">
                    Submit reviews to see per-item sentiment labels.
                  </p>
                ) : (
                  results.map((row, idx) => (
                    <article
                      key={`${row.review}-${idx}`}
                      className="rounded-lg border border-slate-800 bg-slate-950/60 p-3"
                    >
                      <div className="flex flex-wrap items-center gap-2">
                        <SentimentBadge sentiment={row.sentiment} />
                        <span className="text-xs text-slate-500">
                          polarity {row.polarity}
                          {row.date ? ` · ${row.date}` : ""}
                        </span>
                      </div>
                      <p className="mt-2 text-sm leading-relaxed text-slate-200">{row.review}</p>
                    </article>
                  ))
                )}
              </div>
              <p className="text-xs text-slate-500">
                Each run calls <code className="text-indigo-300">POST /analyze</code> and appends
                to the server history used by the dashboard.
              </p>
            </div>
          </div>
        </div>
      </details>
    </div>
  );
}
