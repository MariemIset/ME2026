import React, { useState } from 'react'
import axios from 'axios'

const API = 'http://localhost:8000'

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function Spinner() {
  return (
    <div className="flex justify-center py-10">
      <div className="animate-spin rounded-full h-10 w-10 border-4 border-gray-200 border-t-purple-600" />
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

/**
 * SVG circular progress gauge.
 * Rotated -90° so progress starts from the top.
 * Text overlay uses an absolutely-positioned div so it stays upright.
 */
function CircleGauge({ probability }) {
  const pct = Math.round(probability * 100)
  const R   = 52
  const circ = 2 * Math.PI * R
  const offset = circ - (pct / 100) * circ
  const color = pct < 40 ? '#22c55e' : pct <= 70 ? '#eab308' : '#ef4444'

  return (
    <div className="relative w-36 h-36 mx-auto">
      <svg
        viewBox="0 0 144 144"
        className="w-full h-full"
        style={{ transform: 'rotate(-90deg)' }}
      >
        <circle cx="72" cy="72" r={R} fill="none" stroke="#e5e7eb" strokeWidth="12" />
        <circle
          cx="72" cy="72" r={R}
          fill="none"
          stroke={color}
          strokeWidth="12"
          strokeDasharray={`${circ} ${circ}`}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 0.6s ease' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        <span className="text-2xl font-bold" style={{ color }}>{pct}%</span>
        <span className="text-xs text-gray-500 mt-0.5">churn risk</span>
      </div>
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
}

const RISK_PILL = {
  Low:    'bg-green-100  text-green-700  border-green-200',
  Medium: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  High:   'bg-red-100    text-red-700    border-red-200',
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function Churn() {
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
      const { data } = await axios.post(`${API}/predict/churn`, {
        loyalty_card:          form.loyalty_card,
        gender:                form.gender,
        marital_status:        form.marital_status,
        total_flights:         Number(form.total_flights),
        total_distance:        Number(form.total_distance),
        total_points_earned:   Number(form.total_points_earned),
        total_points_redeemed: Number(form.total_points_redeemed),
        redemption_rate:       Number(form.redemption_rate),
        avg_points_per_flight: Number(form.avg_points_per_flight),
      })
      setResult(data)
    } catch (err) {
      setError(err.response?.data?.detail ?? 'API is unreachable. Is the backend running on port 8000?')
    } finally {
      setLoading(false)
    }
  }

  const inputCls = 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500'
  const selectCls = inputCls

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-800 mb-1">Churn Risk Prediction</h1>
      <p className="text-gray-500 text-sm mb-6">
        Predict the probability that a loyalty member will cancel their membership.
      </p>

      {error && <ErrorBanner message={error} />}

      <form onSubmit={submit} className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-5">
        {/* Categorical fields */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Loyalty Card</label>
            <select name="loyalty_card" value={form.loyalty_card} onChange={handle} className={selectCls}>
              {['Star', 'Nova', 'Aurora'].map(v => <option key={v}>{v}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Gender</label>
            <select name="gender" value={form.gender} onChange={handle} className={selectCls}>
              {['Male', 'Female'].map(v => <option key={v}>{v}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Marital Status</label>
            <select name="marital_status" value={form.marital_status} onChange={handle} className={selectCls}>
              {['Single', 'Married', 'Divorced'].map(v => <option key={v}>{v}</option>)}
            </select>
          </div>
        </div>

        {/* Numeric fields */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            ['total_flights',         'Total Flights',          {}],
            ['total_distance',        'Total Distance (km)',     {}],
            ['total_points_earned',   'Total Points Earned',    {}],
            ['total_points_redeemed', 'Total Points Redeemed',  {}],
            ['avg_points_per_flight', 'Avg Points Per Flight',  {}],
          ].map(([name, label, extra]) => (
            <div key={name}>
              <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
              <input
                type="number" name={name} value={form[name]} onChange={handle}
                required min="0" {...extra} className={inputCls}
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
          className="w-full bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white font-semibold py-2.5 rounded-lg transition-colors"
        >
          {loading ? 'Predicting…' : 'Predict Churn Risk'}
        </button>
      </form>

      {loading && <Spinner />}

      {result && !loading && (
        <div className="mt-6 bg-white rounded-xl border border-purple-100 shadow-sm p-6 flex flex-col items-center gap-4">
          <h2 className="text-lg font-semibold text-gray-800 self-start">Prediction Result</h2>

          <CircleGauge probability={result.churn_probability} />

          <span className={`px-5 py-1.5 rounded-full text-sm font-semibold border ${RISK_PILL[result.risk_level]}`}>
            {result.risk_level} Risk
          </span>

          <p className="text-gray-600 text-sm text-center">
            This customer has a{' '}
            <strong>{Math.round(result.churn_probability * 100)}%</strong> churn risk —{' '}
            <strong>{result.risk_level}</strong>.
          </p>
        </div>
      )}
    </div>
  )
}
