const API_BASE = 'http://localhost:8002';

interface FetchOptions {
  method?: string;
  body?: unknown;
}

async function request<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const url = `${API_BASE}${path}`;
  const config: RequestInit = {
    method: options.method || 'GET',
    headers: { 'Content-Type': 'application/json' },
    ...(options.body ? { body: JSON.stringify(options.body) } : {}),
  };
  const response = await fetch(url, config);
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

export interface KpiData {
  totalCustomers: { value: number; goal: number };
  churnRisk: { value: number; goal: number };
  avgClv: { value: number; goal: number };
  totalRevenue: { value: number; goal: number };
}

export interface RevenueChartItem {
  name: string;
  value: number;
}

export interface ChurnStats {
  churnBySegment: { name: string; value: number }[];
  barData: { name: string; value: number }[];
  scatterActive: { x: number; y: number }[];
  scatterChurned: { x: number; y: number }[];
}

export interface LoyaltyStats {
  goldTier: number;
  avgPoints: number;
  redemptionRate: number;
  dollarCost: number;
  liability: number;
  segmentation: { name: string; value: number }[];
}

export interface LoyaltyTimelineItem {
  name: string;
  accumulated: number;
  redeemed: number;
}

export interface SatisfactionStats {
  pieData: { name: string; value: number }[];
  wifi: number;
  seatComfort: number;
  foodDrink: number;
  avgDelay: number;
  volume: number;
  nps: number;
  heatmap: { name: string; legRoom: number; wifi: number; food: number }[];
  recentFeedback: { id: number; text: string; sentiment: string; score: number; time: string }[];
  scatter: { x: number; y: number }[];
}

export interface NlpResult {
  sentiment: string;
  score: number;
  topics: string[];
  positiveWords: number;
  negativeWords: number;
}

export interface LatestCommentData {
  id: number;
  text: string;
  satisfaction: string;
  nlp: NlpResult;
  rating?: number;
  flightClass?: string;
}

export interface LatestCommentResponse {
  found: boolean;
  comment: LatestCommentData | null;
}

export interface FeedbackResponse {
  submitted: boolean;
  comment?: LatestCommentData;
  error?: string;
}

export interface ImageAnalysisResult {
  label: string;
  confidence: number;
  topLabel: string;
  topScore: number;
}

export interface LatestImageAnalysisResponse {
  found: boolean;
  analysis: {
    id: number;
    surveyId: number;
    label: string;
    confidence: number;
    topLabel: string;
    topScore: number;
    commentText: string;
    createdAt: string;
  } | null;
}

export interface CustomerSample {
  loyaltyNumber: number;
  loyaltyCard: string;
  city: string;
  province: string;
  clv: number;
  enrollmentType: string;
  isChurned: boolean;
}

export interface ChurnPrediction {
  loyalty_number: number;
  churn_probability: number;
  churn_risk_tier: string;
}

export interface LoyaltyRecommendation {
  loyalty_number: number;
  segment_id: number;
  segment_label: string;
  redemption_proba: number;
  uplift_score: number;
  recommended_reward: string;
  expected_value: number;
  reward_rank: number;
}

export const api = {
  getKpis: (loyaltyCards?: string, provinces?: string) => {
    const params = new URLSearchParams();
    if (loyaltyCards) params.set('loyalty_cards', loyaltyCards);
    if (provinces) params.set('provinces', provinces);
    const qs = params.toString();
    return request<KpiData>(`/api/kpis${qs ? '?' + qs : ''}`);
  },

  getRevenueChart: (loyaltyCards?: string, provinces?: string) => {
    const params = new URLSearchParams();
    if (loyaltyCards) params.set('loyalty_cards', loyaltyCards);
    if (provinces) params.set('provinces', provinces);
    const qs = params.toString();
    return request<RevenueChartItem[]>(`/api/ceo/revenue-chart${qs ? '?' + qs : ''}`);
  },

  getChurnStats: (loyaltyCards?: string, provinces?: string) => {
    const params = new URLSearchParams();
    if (loyaltyCards) params.set('loyalty_cards', loyaltyCards);
    if (provinces) params.set('provinces', provinces);
    const qs = params.toString();
    return request<ChurnStats>(`/api/churn/stats${qs ? '?' + qs : ''}`);
  },

  getLoyaltyStats: (loyaltyCards?: string, provinces?: string) => {
    const params = new URLSearchParams();
    if (loyaltyCards) params.set('loyalty_cards', loyaltyCards);
    if (provinces) params.set('provinces', provinces);
    const qs = params.toString();
    return request<LoyaltyStats>(`/api/loyalty/stats${qs ? '?' + qs : ''}`);
  },

  getLoyaltyTimeline: (loyaltyCards?: string, provinces?: string) => {
    const params = new URLSearchParams();
    if (loyaltyCards) params.set('loyalty_cards', loyaltyCards);
    if (provinces) params.set('provinces', provinces);
    const qs = params.toString();
    return request<LoyaltyTimelineItem[]>(`/api/loyalty/timeline${qs ? '?' + qs : ''}`);
  },

  getLatestComment: () => {
    return request<LatestCommentResponse>('/api/satisfaction/latest-comment');
  },

  submitFeedback: (text: string, rating?: number, flightClass?: string) => {
    return request<FeedbackResponse>('/api/satisfaction/feedback', {
      method: 'POST',
      body: { text, rating: rating ?? 3, flight_class: flightClass ?? "Economy" },
    });
  },

  getSatisfactionStats: (travelTypes?: string, flightClasses?: string) => {
    const params = new URLSearchParams();
    if (travelTypes) params.set('travel_types', travelTypes);
    if (flightClasses) params.set('flight_classes', flightClasses);
    const qs = params.toString();
    return request<SatisfactionStats>(`/api/satisfaction/stats${qs ? '?' + qs : ''}`);
  },

  getSentimentTimeline: () => {
    return request<{ totalComments: number; positivePercent: number; negativePercent: number; timeline: { name: string; value: number }[] }>('/api/nlp/sentiment-timeline');
  },

  getThemes: () => {
    return request<{ keywords: { word: string; count: number }[] }>('/api/nlp/themes');
  },

  uploadImage: (file: File, surveyId: number) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('survey_id', String(surveyId));
    return fetch(`${API_BASE}/api/satisfaction/upload-image`, {
      method: 'POST',
      body: formData,
    }).then(r => r.json()) as Promise<{ uploaded: boolean; analysis: ImageAnalysisResult }>;
  },

  getLatestImageAnalysis: () => {
    return request<LatestImageAnalysisResponse>('/api/satisfaction/latest-image-analysis');
  },

  getCustomerSample: () => {
    return request<CustomerSample[]>('/api/customers/random-sample');
  },

  predictChurn: (loyaltyNumber: number) => {
    return request<ChurnPrediction>('/api/predictions/churn', {
      method: 'POST',
      body: { loyalty_number: loyaltyNumber },
    });
  },

  predictRecommendation: (loyaltyNumber: number) => {
    return request<LoyaltyRecommendation[]>('/api/predictions/recommendation', {
      method: 'POST',
      body: { loyalty_number: loyaltyNumber },
    });
  },
};
