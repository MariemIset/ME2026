export const mockData = {
  ceo: {
    totalCustomers: { value: 16737, goal: 20000 },
    churnRisk: { value: 2067, goal: 1500 },
    avgClv: { value: 8027.60, goal: 8500 },
    totalRevenue: { value: 1250000, goal: 1500000 },
    monthlyRevenue: [
      { name: 'Jan', value: 4000 },
      { name: 'Feb', value: 3000 },
      { name: 'Mar', value: 5000 },
      { name: 'Apr', value: 4500 },
      { name: 'May', value: 6000 },
      { name: 'Jun', value: 7200 },
    ],
    churnBySegment: [
      { name: 'High Risk', value: 400 },
      { name: 'Medium Risk', value: 800 },
      { name: 'Low Risk', value: 1200 },
    ]
  },
  marketing: {
    goldTier: { value: 4120, goal: 5000 },
    avgPoints: { value: 12450, goal: 15000 },
    redemptionRate: { value: 68.5, goal: 75 },
    conversionRate: { value: 12.4, goal: 15 },
    activeCampaigns: { value: 24, goal: 30 },
    cpa: { value: 45.50, goal: 40.00 }, // Cost Per Acquisition
    roi: { value: 312, goal: 250 }, // Return on Investment %
    engagementRate: { value: 8.7, goal: 10.0 }, // %
    segmentation: [
      { name: 'Frequent Flyers', value: 35 },
      { name: 'Occasional', value: 45 },
      { name: 'New Customers', value: 20 },
    ],
    engagementOverTime: [
      { name: 'Week 1', active: 1200, inactive: 300 },
      { name: 'Week 2', active: 1300, inactive: 280 },
      { name: 'Week 3', active: 1450, inactive: 200 },
      { name: 'Week 4', active: 1600, inactive: 150 },
    ]
  },
  process: {
    totalSatisfaction: { value: 43.45, goal: 50 },
    inflightWifi: { value: 2.7, goal: 4.0 },
    seatComfort: { value: 4.2, goal: 4.5 },
    foodDrink: { value: 3.1, goal: 4.0 },
    resolutionTime: { value: 24.5, goal: 12 }, // hours
    nps: { value: 42, goal: 60 }, // Net Promoter Score
    fcr: { value: 76.5, goal: 85 }, // First Contact Resolution %
    ticketVolume: { value: 12450, goal: 10000 },

    sentimentTimeline: [
      { name: 'Mon', positive: 60, negative: 40 },
      { name: 'Tue', positive: 65, negative: 35 },
      { name: 'Wed', positive: 55, negative: 45 },
      { name: 'Thu', positive: 70, negative: 30 },
      { name: 'Fri', positive: 80, negative: 20 },
    ],
    recentFeedback: [
      { id: 1, text: "The boarding process was very confusing.", sentiment: 'Negative', score: -0.84, time: "2 mins ago" },
      { id: 2, text: "Loved the new seats! Much better legroom.", sentiment: 'Positive', score: 0.92, time: "15 mins ago" },
      { id: 3, text: "Flight was okay, but wifi kept dropping.", sentiment: 'Neutral', score: -0.15, time: "1 hour ago" },
    ]
  }
};
