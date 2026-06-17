import React, { useState } from 'react'
import { BrowserRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom'
import Churn from './pages/Churn.jsx'
import Segmentation from './pages/Segmentation.jsx'
import Satisfaction from './pages/Satisfaction.jsx'

const NAV = [
  {
    to: '/churn',
    label: 'Churn Risk',
    icon: '📉',
    activeClass: 'bg-purple-600 text-white',
  },
  {
    to: '/segmentation',
    label: 'Segmentation',
    icon: '🔵',
    activeClass: 'bg-teal-600 text-white',
  },
  {
    to: '/satisfaction',
    label: 'Satisfaction',
    icon: '⭐',
    activeClass: 'bg-orange-500 text-white',
  },
]

function Sidebar({ open, onClose }) {
  return (
    <>
      {/* Mobile backdrop */}
      {open && (
        <div
          className="fixed inset-0 bg-black/40 z-20 md:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={[
          'fixed inset-y-0 left-0 z-30 w-64 bg-gray-900 flex flex-col',
          'transform transition-transform duration-300 ease-in-out',
          open ? 'translate-x-0' : '-translate-x-full',
          'md:static md:translate-x-0',
        ].join(' ')}
      >
        {/* Brand */}
        <div className="px-6 py-5 border-b border-gray-700 flex-shrink-0">
          <p className="text-white text-xl font-bold tracking-tight">✈ ME2026</p>
          <p className="text-gray-400 text-xs mt-0.5">Airline ML Platform</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {NAV.map(({ to, label, icon, activeClass }) => (
            <NavLink
              key={to}
              to={to}
              onClick={onClose}
              className={({ isActive }) =>
                [
                  'flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium',
                  'transition-colors duration-150',
                  isActive
                    ? activeClass
                    : 'text-gray-300 hover:bg-gray-800 hover:text-white',
                ].join(' ')
              }
            >
              <span className="text-base">{icon}</span>
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-700 flex-shrink-0">
          <p className="text-gray-500 text-xs">3ALINFO3 · 2026</p>
        </div>
      </aside>
    </>
  )
}

export default function App() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <BrowserRouter>
      <div className="flex h-screen overflow-hidden bg-gray-50">
        <Sidebar open={menuOpen} onClose={() => setMenuOpen(false)} />

        <div className="flex-1 flex flex-col overflow-hidden min-w-0">
          {/* Mobile top bar */}
          <header className="md:hidden flex-shrink-0 bg-gray-900 px-4 py-3 flex items-center gap-3">
            <button
              onClick={() => setMenuOpen(true)}
              className="text-white text-2xl leading-none focus:outline-none"
              aria-label="Open navigation menu"
            >
              ☰
            </button>
            <span className="text-white font-bold text-lg">✈ ME2026</span>
          </header>

          {/* Page content */}
          <main className="flex-1 overflow-y-auto p-4 md:p-8">
            <Routes>
              <Route path="/" element={<Navigate to="/churn" replace />} />
              <Route path="/churn" element={<Churn />} />
              <Route path="/segmentation" element={<Segmentation />} />
              <Route path="/satisfaction" element={<Satisfaction />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  )
}
