const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json();
}

export function fetchTrends() {
  return request("/trends");
}

export function fetchThemes() {
  return request("/themes");
}

export function fetchSampleReviews() {
  return request("/sample-reviews");
}

export function analyzeReviews(reviews) {
  return request("/analyze", {
    method: "POST",
    body: JSON.stringify({ reviews }),
  });
}
