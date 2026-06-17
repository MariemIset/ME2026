import React, { useState } from 'react'
import axios from 'axios'

const API = 'http://localhost:8000'

// ---------------------------------------------------------------------------
// Cluster label map (generic — updated once cluster_profiles.csv is analysed)
// ---------------------------------------------------------------------------
const CLUSTER_LABELS = {
  0: { name: 'Low Engagement',      desc: 'Infrequent flyers with minimal point activity.' },
  1: { name: 'High Earners',        desc: 'Frequent long-haul flyers with strong point accumulation.' },
  2: { name: 'Occasional Flyers',   desc: 'Moderate activity with low redemption rate.' },
  3: { name: 'Budget Travelers',    desc: 'Short-haul, cost-conscious passengers.' },
  4: { name: 'Loyal Redeemers',     desc: 'Consistent earners who actively redeem rewards.' },
  5: { name: 'Premium Members',     desc: 'High CLV, long-distance business travelers.' },
}

function clusterInfo(id) {
  return CLUSTER_LABELS[id] ?? { name: `Segment ${id}`, desc: 'Identified customer segment.' }
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function Spinner() {
  return (
    <div className="flex justify-center py-10">
      <div className="animate-spin rounded-full h-10 w-10 border-4 border-gray-200 border-t-teal-600" />
    </div>
  )
}

function ErrorBanner({ message }) {
  return (
    <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 mb-4 text-sm">
      ⚠ {message}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Form defaults
// ---------------------------------------------------------------------------

const INITIAL = {
  loyalty_card:          'Star',
  gender:                'Male',
  marital_status:        'Single',
  total_flights:         '',
  total_distance:        '',
  total_points_earned:   '',
  total_points_redeemed: '',
  redemption_rate:       '',
  avg_points_per_flight: '',
  clv:                   '',
  salary:                '',
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function Segmentation() {
  const [form,    setForm]    = useState(INITIAL)
  const [result,  setResult]  = useState(null)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState(null)

  const handle = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const { data } = await axios.post(`${API}/predict/segmentation`, {
        loyalty_card:          form.loyalty_card,
        gender:                form.gender,
        marital_status:        form.marital_status,
        total_flights:         Number(form.total_flights),
        total_distance:        Number(form.total_distance),
        total_points_earned:   Number(form.total_points_earned),
        total_points_redeemed: Number(form.total_points_redeemed),
        redemption_rate:       Number(form.redemption_rate),
        avg_points_per_flight: Number(form.avg_points_per_flight),
        clv:                   Number(form.clv),
        salary:                Number(form.salary),
      })
      setResult(data)
    } catch (err) {
      setError(err.response?.data?.detail ?? 'API is unreachable. Is the backend running on port 8000?')
    } finally {
      setLoading(false)
    }
  }

  const inputCls  = 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500'
  const selectCls = inputCls

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-800 mb-1">Customer Segmentation</h1>
      <p className="text-gray-500 text-sm mb-6">
        Identify which behavioural cluster a customer belongs to and flag anomalous activity.
      </p>

      {error && <ErrorBanner message={error} />}

      <form onSubmit={submit} className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-5">
        {/* Categorical */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            ['loyalty_card',   'Loyalty Card',   ['Star', 'Nova', 'Aurora']],
            ['gender',         'Gender',         ['Male', 'Female']],
            ['marital_status', 'Marital Status', ['Single', 'Married', 'Divorced']],
          ].map(([name, label, opts]) => (
            <div key={name}>
              <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
              <select name={name} value={form[name]} onChange={handle} className={selectCls}>
                {opts.map(v => <option key={v}>{v}</option>)}
              </select>
            </div>
          ))}
        </div>

        {/* Numeric */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            ['total_flights',         'Total Flights'],
            ['total_distance',        'Total Distance (km)'],
            ['total_points_earned',   'Total Points Earned'],
            ['total_points_redeemed', 'Total Points Redeemed'],
            ['avg_points_per_flight', 'Avg Points Per Flight'],
            ['clv',                   'Customer Lifetime Value (CLV)'],
            ['salary',                'Salary'],
          ].map(([name, label]) => (
            <div key={name}>
              <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
              <input
                type="number" name={name} value={form[name]} onChange={handle}
                required min="0" className={inputCls}
              />
            </div>
          ))}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Redemption Rate <span className="text-gray-400">(0–1)</span>
            </label>
            <input
              type="number" name="redemption_rate" value={form.redemption_rate} onChange={handle}
              required min="0" max="1" step="0.01" className={inputCls}
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white font-semibold py-2.5 rounded-lg transition-colors"
        >
          {loading ? 'Analyzing…' : 'Analyze Segment'}
        </button>
      </form>

      {loading && <Spinner />}

      {result && !loading && (
        <div className="mt-6 bg-white rounded-xl border border-teal-100 shadow-sm p-6 space-y-4">
          <h2 className="text-lg font-semibold text-gray-800">Segmentation Result</h2>

          {/* Cluster card */}
          <div className="flex items-center gap-4 p-4 bg-teal-50 rounded-lg border border-teal-100">
            <div className="w-14 h-14 rounded-full bg-teal-600 flex items-center justify-center text-white text-2xl font-bold flex-shrink-0">
              {result.cluster_id}
            </div>
            <div>
              <p className="font-semibold text-gray-800">
                Cluster {result.cluster_id} — {clusterInfo(result.cluster_id).name}
              </p>
              <p className="text-sm text-gray-500 mt-0.5">
                {clusterInfo(result.cluster_id).desc}
              </p>
            </div>
          </div>

          {/* Anomaly banner */}
          {result.is_anomaly ? (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="font-semibold text-red-700">⚠ Anomaly Detected</p>
              <p className="text-sm text-red-600 mt-1">
                This customer's behaviour is statistically unusual compared to their cluster peers.
                Flag for manual review.
              </p>
              <p className="text-sm text-red-500 mt-2">
                Anomaly score: <strong>{result.anomaly_score.toFixed(4)}</strong>
              </p>
            </div>
          ) : (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="font-semibold text-green-700">✓ Normal Behavior</p>
              <p className="text-sm text-green-600 mt-1">
                No anomalies detected. Behaviour is consistent with typical cluster patterns.
              </p>
              <p className="text-sm text-green-500 mt-2">
                Anomaly score: <strong>{result.anomaly_score.toFixed(4)}</strong>
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
