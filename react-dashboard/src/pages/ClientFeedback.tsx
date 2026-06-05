import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, Navigate } from 'react-router-dom';
import { api, type LatestCommentData, type ImageAnalysisResult } from '../services/api';
import { ThumbsUp, ThumbsDown, Minus, Send, Star, LogOut, MessageSquare, Sparkles, Camera } from 'lucide-react';

const SentimentIcon = ({ sentiment, size = 5 }: { sentiment: string; size?: number }) => {
  if (sentiment === "Positive") return <ThumbsUp className={`w-${size} h-${size} text-emerald-400`} />;
  if (sentiment === "Negative") return <ThumbsDown className={`w-${size} h-${size} text-rose-400`} />;
  return <Minus className={`w-${size} h-${size} text-yellow-400`} />;
};

const ClientFeedback = () => {
  const { role, logout } = useAuth();
  const navigate = useNavigate();

  const [feedbackText, setFeedbackText] = useState("");
  const [rating, setRating] = useState(5);
  const [flightClass, setFlightClass] = useState("Economy");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [lastSubmission, setLastSubmission] = useState<LatestCommentData | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [imageAnalysis, setImageAnalysis] = useState<ImageAnalysisResult | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [recentComments, setRecentComments] = useState<{ id: number; text: string; sentiment: string; score: number; time: string }[]>([]);
  const feedbackEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.getSatisfactionStats().then(data => {
      setRecentComments(
        data.recentFeedback.slice(0, 5).map(fb => ({
          id: fb.id,
          text: fb.text,
          sentiment: fb.sentiment,
          score: fb.score,
          time: fb.time,
        }))
      );
    }).catch(() => {});
  }, []);

  useEffect(() => {
    feedbackEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [recentComments.length]);

  if (!role) {
    return <Navigate to="/login" replace />;
  }

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleSubmit = async () => {
    const text = feedbackText.trim();
    if (!text) return;
    if (text.length < 3) {
      setSubmitError("Comment must be at least 3 characters");
      return;
    }

    setSubmitting(true);
    setSubmitError(null);
    try {
      const result = await api.submitFeedback(text, rating, flightClass);
      if (result.submitted && result.comment) {
        setLastSubmission(result.comment);
        setRecentComments(prev => [{
          id: result.comment!.id,
          text: result.comment!.text,
          sentiment: result.comment!.nlp.sentiment,
          score: result.comment!.nlp.score,
          time: "Just now",
        }, ...prev]);
        setFeedbackText("");

        if (uploadedFile) {
          setAnalyzing(true);
          try {
            const imgResult = await api.uploadImage(uploadedFile, result.comment.id);
            if (imgResult.uploaded) {
              setImageAnalysis(imgResult.analysis);
            }
          } catch {
            // image analysis failed silently
          } finally {
            setAnalyzing(false);
          }
        }
      } else {
        setSubmitError(result.error || "Failed to submit");
      }
    } catch {
      setSubmitError("Failed to submit feedback. Is the server running?");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950">
      <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
        <div className="bg-slate-900/80 backdrop-blur-md border border-slate-700/50 rounded-2xl p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 124.4 64" className="w-9 h-5">
              <path fill="#d81e05" fill-rule="evenodd" clip-rule="evenodd" d="M13.6,53c16.5-13.3,28.2-24.8,31.7-31c1.5-2.4,2-4.7,1.1-6.5c-1.5-3.5-7-4.5-13.6-3.2C62.7,5.5,93.2,1.4,123.8,0c0.3,0,0.6,0.2,0.6,0.5c0,0.2-0.1,0.5-0.4,0.5c-38.8,12.6-74.1,33-104,59.4c0,0-0.1,0.1-0.1,0.1L0.3,64c-0.3,0-0.4-0.3-0.2-0.5C4.7,60.1,9.2,56.6,13.6,53"/>
              <path fill="#93282c" fill-rule="evenodd" clip-rule="evenodd" d="M11,17.4c-0.4,0.1-0.9,0.2-1.3,0.4c-0.3,0.1-0.2,0.4,0,0.5l7.4,1.1L30,21.2c0.1,0,0.1,0,0.1,0c9.1-4.3,15.1-6,16.5-4.1c0.4,0.6,0.3,1.5-0.1,2.6c-0.2,0.4-0.4,0.8-0.6,1.3c1.4-2.3,1.9-4.4,1.1-6.2c-1.5-3.3-6.6-4.3-13.1-3C26.2,13.5,18.6,15.4,11,17.4"/>
            </svg>
            <span className="text-lg font-black text-white tracking-tight">ALI</span>
          </div>
          <button onClick={handleLogout} className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-slate-200 transition-colors bg-slate-800/50 border border-slate-700/50 rounded-lg px-3 py-1.5">
            <LogOut className="w-3.5 h-3.5" /> Sign Out
          </button>
        </div>

        <div className="bg-slate-900/60 backdrop-blur-md border border-slate-700/50 rounded-2xl shadow-lg p-6 md:p-8">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-extrabold text-white tracking-tight">Submit Your Feedback</h1>
            <p className="mt-2 text-slate-400">Tell us about your recent experience with our airline.</p>
          </div>

          <div className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Your Experience</label>
              <textarea
                value={feedbackText}
                onChange={(e) => { setFeedbackText(e.target.value); setSubmitError(null); }}
                placeholder="Tell us what you liked or didn't like..."
                rows={4}
                maxLength={500}
                className="w-full bg-slate-800 border border-slate-700 text-white rounded-xl px-4 py-3 text-sm resize-none focus:outline-none focus:border-rose-500 placeholder-slate-500 transition-colors"
              />
              <div className="flex justify-between mt-1">
                <span className="text-xs text-slate-600">{feedbackText.length}/500</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">Flight Class</label>
                <select
                  value={flightClass}
                  onChange={(e) => setFlightClass(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 text-white rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-rose-500"
                >
                  <option>Economy</option>
                  <option>Business</option>
                  <option>First Class</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">Rating</label>
                <div className="flex gap-1 items-center h-full pt-1">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => setRating(star)}
                      className="transition-all hover:scale-110"
                    >
                      <Star
                        className={`w-7 h-7 ${star <= rating ? 'text-amber-400 fill-amber-400' : 'text-slate-600'}`}
                      />
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Attach Photo <span className="text-slate-500">(optional)</span></label>
              <div className="flex items-center gap-3">
                <label className="cursor-pointer flex items-center gap-2 bg-slate-800 border border-slate-700 text-slate-300 rounded-xl px-4 py-2.5 text-sm hover:border-slate-500 transition-colors">
                  <Camera className="w-4 h-4" />
                  Choose file
                  <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(e) => {
                      if (e.target.files?.[0]) setUploadedFile(e.target.files[0]);
                    }}
                  />
                </label>
                {uploadedFile && (
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-400 truncate max-w-40">{uploadedFile.name}</span>
                    <button
                      type="button"
                      onClick={() => setUploadedFile(null)}
                      className="text-rose-400 hover:text-rose-300 text-xs"
                    >
                      Remove
                    </button>
                  </div>
                )}
              </div>
            </div>

            <button
              onClick={handleSubmit}
              disabled={submitting || !feedbackText.trim()}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-sm font-bold text-white bg-gradient-to-r from-rose-600 to-rose-500 hover:from-rose-500 hover:to-rose-400 disabled:from-slate-700 disabled:to-slate-700 disabled:text-slate-500 transition-all shadow-lg shadow-rose-500/20 disabled:shadow-none"
            >
              <Send className="w-4 h-4" />
              {submitting ? "Submitting..." : "Submit Feedback"}
            </button>

            {submitError && (
              <p className="text-rose-400 text-sm text-center">{submitError}</p>
            )}
          </div>
        </div>

        {lastSubmission && (
          <div className="bg-gradient-to-br from-slate-900 to-slate-800/80 backdrop-blur-md border border-emerald-500/30 rounded-2xl shadow-lg p-6 animate-pulse">
            <div className="flex items-center gap-2 text-emerald-400 font-semibold mb-4">
              <Sparkles className="w-5 h-5" />
              Feedback Received — Survey #{lastSubmission.id}
            </div>
            <div className="flex flex-col lg:flex-row gap-6">
              <div className="flex-1 bg-slate-800/40 border border-slate-700/50 rounded-xl p-5">
                <p className="text-slate-200 text-base leading-relaxed italic">"{lastSubmission.text}"</p>
                <div className="mt-3 flex items-center gap-3 flex-wrap">
                  <span className={"text-xs font-bold px-3 py-1.5 rounded-full " + (
                    lastSubmission.satisfaction === "Satisfied"
                      ? "bg-emerald-500/20 text-emerald-300"
                      : "bg-rose-500/20 text-rose-300"
                  )}>
                    {lastSubmission.satisfaction}
                  </span>
                  {lastSubmission.flightClass && (
                    <span className="text-xs bg-slate-700 text-slate-300 px-3 py-1.5 rounded-full">{lastSubmission.flightClass}</span>
                  )}
                  {lastSubmission.rating && (
                    <span className="text-xs bg-amber-500/10 text-amber-300 px-3 py-1.5 rounded-full">{lastSubmission.rating}/5</span>
                  )}
                  {imageAnalysis && (
                    <span className={"text-xs px-3 py-1.5 rounded-full flex items-center gap-1 " + (
                      imageAnalysis.label === "clean"
                        ? "bg-emerald-500/20 text-emerald-300"
                        : "bg-rose-500/20 text-rose-300"
                    )}>
                      {imageAnalysis.label === "clean" ? "🧹" : "⚠️"} {imageAnalysis.label === "clean" ? "Clean" : "Dirty"} ({(imageAnalysis.confidence * 100).toFixed(0)}%)
                    </span>
                  )}
                  {analyzing && <span className="text-xs text-slate-500">Analyzing image...</span>}
                </div>
              </div>
            </div>
          </div>
        )}

        {recentComments.length > 0 && (
          <div className="bg-slate-900/60 backdrop-blur-md border border-slate-700/50 rounded-2xl shadow-lg p-6">
            <h3 className="text-white font-semibold flex items-center gap-2 mb-5">
              <MessageSquare className="w-4 h-4 text-rose-400" />
              Recent Feedback
            </h3>
            <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
              {recentComments.map((fb) => (
                <div key={fb.id + fb.time} className="p-4 bg-slate-800/40 rounded-xl border border-slate-700/50 hover:border-slate-600/50 transition-colors">
                  <p className="text-sm text-slate-300 leading-relaxed">"{fb.text}"</p>
                  <div className="mt-2 flex justify-between items-center">
                    <span className={"text-xs font-medium px-2 py-1 rounded-md flex items-center gap-1 " + (
                      fb.sentiment === "Positive" ? "bg-emerald-500/20 text-emerald-300"
                        : fb.sentiment === "Negative" ? "bg-rose-500/20 text-rose-300"
                        : "bg-yellow-500/20 text-yellow-300"
                    )}>
                      <SentimentIcon sentiment={fb.sentiment} size={3} />
                      {fb.sentiment} ({(fb.score * 100).toFixed(0)}%)
                    </span>
                    <span className="text-xs text-slate-500">{fb.time}</span>
                  </div>
                </div>
              ))}
              <div ref={feedbackEndRef} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ClientFeedback;
