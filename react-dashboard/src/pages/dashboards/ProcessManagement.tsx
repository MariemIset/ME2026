import { useState, useEffect } from 'react';
import { MetricCard } from '../../components/charts/MetricCard';
import type { SatisfactionStats, LatestCommentResponse, LatestImageAnalysisResponse } from '../../services/api';
import { api } from '../../services/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { MessageSquare, Brain, Tags, ThumbsUp, ThumbsDown, Minus, MessageCircle, ImageIcon } from 'lucide-react';

const ProcessManagement = () => {
  const [stats, setStats] = useState<SatisfactionStats | null>(null);
  const [latestComment, setLatestComment] = useState<LatestCommentResponse | null>(null);
  const [imageAnalysis, setImageAnalysis] = useState<LatestImageAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [data, comment, imgAnalysis] = await Promise.all([
          api.getSatisfactionStats(),
          api.getLatestComment(),
          api.getLatestImageAnalysis(),
        ]);
        setStats(data);
        setLatestComment(comment);
        setImageAnalysis(imgAnalysis);
      } catch (err) {
        console.error("Failed to load process data:", err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const customTooltipStyle = { backgroundColor: "#0f172a", borderColor: "#334155", color: "#f8fafc", borderRadius: "8px", boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.5)" };

  const sentimentData = [
    { name: "Mon", positive: stats ? Math.round(stats.nps * 0.4) : 0, negative: stats ? Math.round(stats.volume * 0.01) : 0 },
    { name: "Tue", positive: stats ? Math.round(stats.nps * 0.5) : 0, negative: stats ? Math.round(stats.volume * 0.008) : 0 },
    { name: "Wed", positive: stats ? Math.round(stats.nps * 0.6) : 0, negative: stats ? Math.round(stats.volume * 0.009) : 0 },
    { name: "Thu", positive: stats ? Math.round(stats.nps * 0.7) : 0, negative: stats ? Math.round(stats.volume * 0.007) : 0 },
    { name: "Fri", positive: stats ? Math.round(stats.nps * 0.8) : 0, negative: stats ? Math.round(stats.volume * 0.006) : 0 },
  ];

  if (loading) {
    return <div className="flex items-center justify-center h-64"><span className="text-slate-400 text-lg">Loading process data...</span></div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-white">Satisfaction & NLP (BO3)</h1>
      </div>

      {stats && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
            <MetricCard title="Total Satisfaction" value={stats.pieData[0]?.value.toFixed(1) + "%"} goal={50} isPositive={(stats.pieData[0]?.value || 0) >= 50} />
            <MetricCard title="In-flight WiFi" value={stats.wifi + "/5"} goal={4.0} isPositive={stats.wifi >= 3.0} />
            <MetricCard title="Seat Comfort" value={stats.seatComfort + "/5"} goal={4.5} isPositive={stats.seatComfort >= 4.0} />
            <MetricCard title="Food & Drink" value={stats.foodDrink + "/5"} goal={4.0} isPositive={stats.foodDrink >= 3.0} />
            <MetricCard title="NPS" value={stats.nps} goal={60} isPositive={stats.nps >= 40} />
          </div>

          {latestComment?.found && latestComment.comment && (
            <div className="bg-gradient-to-br from-slate-900 to-slate-800/80 backdrop-blur-md border border-amber-500/30 rounded-2xl shadow-lg p-6">
              <div className="flex items-center gap-2 text-amber-400 font-semibold mb-4">
                <MessageSquare className="w-5 h-5" />
                Latest Client Feedback — Survey #{latestComment.comment.id}
              </div>
              <div className="flex flex-col lg:flex-row gap-6">
                <div className="flex-1 bg-slate-800/40 border border-slate-700/50 rounded-xl p-5">
                  <p className="text-slate-200 text-base leading-relaxed italic">"{latestComment.comment.text}"</p>
                  <div className="mt-3 flex items-center gap-3">
                    <span className={"text-xs font-bold px-3 py-1.5 rounded-full " + (
                      latestComment.comment.satisfaction === "Satisfied"
                        ? "bg-emerald-500/20 text-emerald-300"
                        : "bg-rose-500/20 text-rose-300"
                    )}>
                      {latestComment.comment.satisfaction}
                    </span>
                  </div>
                </div>
                <div className="lg:w-72 space-y-3">
                  <div className="bg-slate-800/40 border border-slate-700/50 rounded-xl p-4">
                    <div className="flex items-center gap-2 text-slate-400 text-xs uppercase tracking-wider mb-3">
                      <Brain className="w-4 h-4 text-purple-400" />
                      NLP Analysis
                    </div>
                    <div className="flex items-center gap-2 mb-3">
                      {latestComment.comment.nlp.sentiment === "Positive" ? (
                        <ThumbsUp className="w-5 h-5 text-emerald-400" />
                      ) : latestComment.comment.nlp.sentiment === "Negative" ? (
                        <ThumbsDown className="w-5 h-5 text-rose-400" />
                      ) : (
                        <Minus className="w-5 h-5 text-yellow-400" />
                      )}
                      <span className={"text-lg font-bold " + (
                        latestComment.comment.nlp.sentiment === "Positive" ? "text-emerald-400"
                          : latestComment.comment.nlp.sentiment === "Negative" ? "text-rose-400"
                          : "text-yellow-400"
                      )}>
                        {latestComment.comment.nlp.sentiment}
                      </span>
                      <span className="text-slate-500 text-sm">({(latestComment.comment.nlp.score * 100).toFixed(0)}%)</span>
                    </div>
                    <div className="flex gap-4 text-xs text-slate-500">
                      <span><span className="text-emerald-400">{latestComment.comment.nlp.positiveWords}</span> pos</span>
                      <span><span className="text-rose-400">{latestComment.comment.nlp.negativeWords}</span> neg</span>
                    </div>
                  </div>
                  {latestComment.comment.nlp.topics.length > 0 && (
                    <div className="bg-slate-800/40 border border-slate-700/50 rounded-xl p-4">
                      <div className="flex items-center gap-2 text-slate-400 text-xs uppercase tracking-wider mb-3">
                        <Tags className="w-4 h-4 text-sky-400" />
                        Key Topics
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {latestComment.comment.nlp.topics.map((topic, i) => (
                          <span key={i} className="bg-sky-500/10 text-sky-300 text-xs px-2.5 py-1 rounded-full border border-sky-500/20">
                            {topic}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {imageAnalysis?.found && imageAnalysis.analysis && imageAnalysis.analysis.surveyId === latestComment.comment.id && (
                    <div className="bg-slate-800/40 border border-slate-700/50 rounded-xl p-4">
                      <div className="flex items-center gap-2 text-slate-400 text-xs uppercase tracking-wider mb-3">
                        <ImageIcon className="w-4 h-4 text-emerald-400" />
                        Image Analysis
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={"text-lg font-bold " + (
                          imageAnalysis.analysis.label === "clean" ? "text-emerald-400" : "text-rose-400"
                        )}>
                          {imageAnalysis.analysis.label === "clean" ? "🧹 Clean" : "⚠️ Dirty"}
                        </span>
                        <span className="text-slate-500 text-sm">({(imageAnalysis.analysis.confidence * 100).toFixed(0)}%)</span>
                      </div>
                      <p className="text-xs text-slate-500 mt-1">{imageAnalysis.analysis.topLabel}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 bg-slate-900/60 backdrop-blur-md border border-slate-700/50 rounded-2xl shadow-lg p-6">
              <h3 className="text-lg font-semibold mb-4 text-white">Sentiment Timeline</h3>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={sentimentData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
                    <XAxis dataKey="name" stroke="#64748b" />
                    <YAxis stroke="#64748b" />
                    <Tooltip contentStyle={customTooltipStyle} />
                    <Line type="monotone" dataKey="positive" stroke="#10b981" strokeWidth={3} dot={{ r: 4 }} />
                    <Line type="monotone" dataKey="negative" stroke="#f43f5e" strokeWidth={3} dot={{ r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="bg-slate-900/60 backdrop-blur-md border border-slate-700/50 rounded-2xl shadow-lg p-6 flex flex-col">
              <h3 className="text-lg font-semibold mb-4 text-white flex items-center gap-2">
                <MessageCircle className="w-4 h-4 text-amber-400" />
                Live Feedback
              </h3>

              <div className="flex-1 space-y-3 overflow-y-auto max-h-80 pr-1">
                {stats.recentFeedback.slice(0, 5).map((fb) => (
                  <div key={fb.id} className="p-3 bg-slate-800/50 rounded-xl border border-slate-700/50 hover:border-slate-600/50 transition-colors">
                    <p className="text-sm text-slate-300 leading-relaxed">"{fb.text}"</p>
                    <div className="mt-2 flex justify-between items-center">
                      <span className={"text-xs font-medium px-2 py-1 rounded-md " + (
                        fb.sentiment === "Positive" ? "bg-emerald-500/20 text-emerald-300"
                          : fb.sentiment === "Negative" ? "bg-rose-500/20 text-rose-300"
                          : "bg-yellow-500/20 text-yellow-300"
                      )}>
                        {fb.sentiment} ({(fb.score * 100).toFixed(0)}%)
                      </span>
                      <span className="text-xs text-slate-500">{fb.time}</span>
                    </div>
                  </div>
                ))}
                {stats.recentFeedback.length === 0 && (
                  <p className="text-slate-500 text-sm text-center py-8">No feedback available</p>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ProcessManagement;
