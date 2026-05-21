import React, { useState } from 'react'
import axios from 'axios'

const API = 'http://localhost:8000'

// ---------------------------------------------------------------------------
// Score fields (slider)
// ---------------------------------------------------------------------------
const SCORE_FIELDS = [
  ['online_boarding_score',  'Online Boarding'],
  ['seat_comfort_score',     'Seat Comfort'],
  ['inflight_service_score', 'In-flight Service'],
  ['wifi_score',             'Wi-Fi'],
  ['entertainment_score',    'Entertainment'],
  ['leg_room_score',         'Leg Room'],
  ['cleanliness_score',      'Cleanliness'],
  ['food_drink_score',       'Food & Drink'],
]

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function Spinner() {
  return (
    <div className="flex justify-center py-10">
      <div className="animate-spin rounded-full h-10 w-10 border-4 border-gray-200 border-t-orange-500" />
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
  ...Object.fromEntries(SCORE_FIELDS.map(([k]) => [k, 3])),
  departure_delay: '',
  arrival_delay:   '',
  customer_type:   'Loyal Customer',
  type_of_travel:  'Business travel',
  travel_class:    'Business',
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function Satisfaction() {
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
      const payload = {
        ...Object.fromEntries(SCORE_FIELDS.map(([k]) => [k, Number(form[k])])),
        departure_delay: Number(form.departure_delay),
        arrival_delay:   Number(form.arrival_delay),
        customer_type:   form.customer_type,
        type_of_travel:  form.type_of_travel,
        travel_class:    form.travel_class,
      }
      const { data } = await axios.post(`${API}/predict/satisfaction`, payload)
      setResult(data)
    } catch (err) {
      setError(err.response?.data?.detail ?? 'API is unreachable. Is the backend running on port 8000?')
    } finally {
      setLoading(false)
    }
  }

  const pct      = result ? Math.round(result.satisfaction_probability * 100) : 0
  const inputCls = 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500'

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-800 mb-1">Satisfaction Prediction</h1>
      <p className="text-gray-500 text-sm mb-6">
        Predict whether a passenger will be satisfied based on service scores and flight conditions.
      </p>

      {error && <ErrorBanner message={error} />}

      <form onSubmit={submit} className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-6">
        {/* Service score sliders */}
        <fieldset>
          <legend className="text-sm font-semibold text-gray-700 mb-3">
            Service Scores <span className="font-normal text-gray-400">(1 = Poor · 5 = Excellent)</span>
          </legend>
          <div className="space-y-3">
            {SCORE_FIELDS.map(([name, label]) => (
              <div key={name} className="flex items-center gap-3">
                <span className="text-sm text-gray-600 w-40 flex-shrink-0">{label}</span>
                <input
                  type="range"
                  name={name}
                  min="1" max="5" step="1"
                  value={form[name]}
                  onChange={handle}
                  className="flex-1 accent-orange-500 h-2 cursor-pointer"
                />
                <span className="text-sm font-bold text-orange-600 w-5 text-center">
                  {form[name]}
                </span>
              </div>
            ))}
          </div>
        </fieldset>

        {/* Delay inputs */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Departure Delay (min)</label>
            <input
              type="number" name="departure_delay" value={form.departure_delay}
              onChange={handle} required min="0" className={inputCls}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Arrival Delay (min)</label>
            <input
              type="number" name="arrival_delay" value={form.arrival_delay}
              onChange={handle} required min="0" className={inputCls}
            />
          </div>
        </div>

        {/* Dropdowns */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Customer Type</label>
            <select name="customer_type" value={form.customer_type} onChange={handle} className={inputCls}>
              {['Loyal Customer', 'Disloyal Customer'].map(v => <option key={v}>{v}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Type of Travel</label>
            <select name="type_of_travel" value={form.type_of_travel} onChange={handle} className={inputCls}>
              {['Business travel', 'Personal Travel'].map(v => <option key={v}>{v}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Travel Class</label>
            <select name="travel_class" value={form.travel_class} onChange={handle} className={inputCls}>
              {['Business', 'Eco', 'Eco Plus'].map(v => <option key={v}>{v}</option>)}
            </select>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-orange-500 hover:bg-orange-600 disabled:opacity-50 text-white font-semibold py-2.5 rounded-lg transition-colors"
        >
          {loading ? 'Predicting…' : 'Predict Satisfaction'}
        </button>
      </form>

      {loading && <Spinner />}

      {result && !loading && (
        <div className="mt-6 bg-white rounded-xl border border-orange-100 shadow-sm p-6 space-y-4">
          <h2 className="text-lg font-semibold text-gray-800">Prediction Result</h2>

          {/* Progress bar */}
          <div>
            <div className="flex justify-between text-sm text-gray-500 mb-1.5">
              <span>Satisfaction Probability</span>
              <span className="font-semibold">{pct}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
              <div
                className="h-4 rounded-full transition-all duration-700"
                style={{
                  width: `${pct}%`,
                  backgroundColor: result.satisfaction_label === 1 ? '#22c55e' : '#ef4444',
                }}
              />
            </div>
          </div>

          {/* Verdict badge */}
          <div className="flex justify-center">
            <span
              className={[
                'px-6 py-2 rounded-full text-sm font-bold border',
                result.satisfaction_label === 1
                  ? 'bg-green-100 text-green-700 border-green-200'
                  : 'bg-red-100 text-red-700 border-red-200',
              ].join(' ')}
            >
              {result.verdict}
            </span>
          </div>

          <p className="text-gray-600 text-sm text-center">
            Predicted satisfaction probability: <strong>{pct}%</strong>
          </p>
        </div>
      )}
    </div>
  )
}
