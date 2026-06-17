import { useState } from "react";
import { analyzeReviews } from "../api.js";
import SentimentBadge from "./SentimentBadge.jsx";

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

export default function CommentForm({ onSubmitted, compact = false }) {
  const [comment, setComment] = useState("");
  const [date, setDate] = useState(todayIso());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastResult, setLastResult] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    const text = comment.trim();
    if (!text) {
      setError("Please enter your comment before submitting.");
      return;
    }

    setError(null);
    setLoading(true);
    setLastResult(null);

    try {
      const data = await analyzeReviews([{ review: text, date: date || todayIso() }]);
      const row = data.results?.[0];
      if (!row) {
        throw new Error("No result returned from the server.");
      }
      setLastResult(row);
      setComment("");
      onSubmitted?.(row);
    } catch (err) {
      setError(err.message || "Could not submit your comment.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className={
        compact
          ? "space-y-4"
          : "rounded-2xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg shadow-black/20"
      }
    >
      {!compact ? (
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-white">Share your feedback</h2>
          <p className="mt-1 text-sm text-slate-400">
            Add a comment about your experience. We analyze it right away and include it in the
            dashboard charts.
          </p>
        </div>
      ) : null}

      <div className="space-y-3">
        <label className="block text-sm font-medium text-slate-300" htmlFor="client-comment">
          Your comment
        </label>
        <textarea
          id="client-comment"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          rows={compact ? 4 : 5}
          placeholder="e.g. The delivery was late and customer service was unhelpful."
          className="w-full resize-y rounded-xl border border-slate-800 bg-slate-950/80 p-4 text-sm text-slate-100 outline-none transition focus:border-indigo-500/60 focus:ring-2 focus:ring-indigo-500/30"
        />
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="sm:w-48">
          <label className="block text-sm font-medium text-slate-300" htmlFor="comment-date">
            Date (optional)
          </label>
          <input
            id="comment-date"
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-950/80 px-3 py-2 text-sm text-slate-100 outline-none focus:border-indigo-500/60 focus:ring-2 focus:ring-indigo-500/30"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60 sm:mb-0.5"
        >
          {loading ? "Submitting…" : "Submit comment"}
        </button>
      </div>

      {error ? (
        <div className="rounded-lg border border-rose-500/40 bg-rose-950/40 px-3 py-2 text-sm text-rose-100">
          {error}
        </div>
      ) : null}

      {lastResult ? (
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/20 p-4">
          <p className="text-sm font-medium text-emerald-100">Thank you — your comment was recorded.</p>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <SentimentBadge sentiment={lastResult.sentiment} />
            <span className="text-xs text-slate-400">
              polarity {lastResult.polarity}
              {lastResult.date ? ` · ${lastResult.date}` : ""}
            </span>
          </div>
          <p className="mt-2 text-sm leading-relaxed text-slate-200">{lastResult.review}</p>
        </div>
      ) : null}
    </form>
  );
}
