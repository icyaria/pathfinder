import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useApp } from '../context/AppContext'
import Nav from '../components/Nav'
import TrailModal from '../components/TrailModal'
import './DashboardPage.css'

const IconOverview = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="18" height="18">
    <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
  </svg>
)
const IconTrails = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="18" height="18">
    <polygon points="3 17 12 3 21 17"/><line x1="3" y1="20" x2="21" y2="20"/>
  </svg>
)
const IconDiscover = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="18" height="18">
    <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
  </svg>
)
const IconCommunity = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="18" height="18">
    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
    <circle cx="9" cy="7" r="4"/>
    <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
    <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
  </svg>
)
const IconDots = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16">
    <circle cx="12" cy="5" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="12" cy="19" r="1.5"/>
  </svg>
)

const TERRAIN_GRADIENTS = {
  mountain: 'linear-gradient(155deg, #b07a14 0%, #c8943a 45%, #4a5a2a 100%)',
  coastal:  'linear-gradient(155deg, #1a5276 0%, #2e86ab 50%, #a8d8ea 100%)',
  forest:   'linear-gradient(155deg, #1b3a1b 0%, #2d5a27 50%, #5a8a3a 100%)',
  mixed:    'linear-gradient(155deg, #2c3e50 0%, #4a6741 50%, #7d8b4a 100%)',
}

function formatDate(dateStr) {
  if (!dateStr) return null
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function difficultyClass(d) {
  return { easy: 'badge-easy', moderate: 'badge-moderate', hard: 'badge-hard' }[d] || 'badge-moderate'
}

function difficultyLabel(d) {
  return { easy: 'EASY', moderate: 'MODERATE', hard: 'DIFFICULT' }[d] || (d || '').toUpperCase()
}

export default function DashboardPage() {
  const { user, setPlannedTrail } = useApp()
  const navigate = useNavigate()
  const [trails, setTrails] = useState([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState('upcoming')
  const [menuOpen, setMenuOpen] = useState(null)
  const [activeModal, setActiveModal] = useState(null)
  const menuRef = useRef(null)

  useEffect(() => {
    if (!user) return
    api.getSavedTrails(user.id)
      .then(data => setTrails(Array.isArray(data?.trails) ? data.trails : []))
      .catch(() => setTrails([]))
      .finally(() => setLoading(false))
  }, [user])

  useEffect(() => {
    const close = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(null)
    }
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [])

  const today = new Date().toISOString().split('T')[0]
  const upcoming  = trails.filter(t => !t.planned_date || t.planned_date >= today)
  const completed = trails.filter(t => t.planned_date && t.planned_date < today)
  const shown = tab === 'upcoming' ? upcoming : completed

  const handleViewMap = (trail) => {
    setActiveModal(trail)
  }

  const handleRemove = async (trail) => {
    try {
      await api.removeTrail(user.id, trail.trail_name)
      setTrails(prev => prev.filter(t => t.trail_name !== trail.trail_name))
    } catch {}
    setMenuOpen(null)
  }

  return (
    <div className="dash-page">
      <Nav activeLink="dashboard" />
      {activeModal && (
        <TrailModal trail={activeModal} onClose={() => setActiveModal(null)} />
      )}

      <div className="dash-body">
        {/* Left Sidebar */}
        <aside className="dash-sidebar">
          <p className="dash-greeting">Hello, {user?.name}!</p>
          <button className="dash-find-btn" onClick={() => navigate('/explore')}>
            Find New Trail
          </button>
          <nav className="dash-sidenav">
            <div className="dash-sidenav-item">
              <IconOverview /> Overview
            </div>
            <div className="dash-sidenav-item active">
              <IconTrails /> My Trails
            </div>
            <Link to="/discover" className="dash-sidenav-item">
              <IconDiscover /> Discover
            </Link>
            <div className="dash-sidenav-item disabled">
              <IconCommunity /> Community
            </div>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="dash-main">
          <div className="dash-header">
            <div className="dash-header-text">
              <h1 className="dash-title">My Upcoming Adventures</h1>
              <p className="dash-subtitle">
                Prepare for your next descent into the Hellenic wild. Review your planned routes and manage your trail permits.
              </p>
            </div>
            <div className="dash-tabs">
              <button
                className={`dash-tab ${tab === 'upcoming' ? 'active' : ''}`}
                onClick={() => setTab('upcoming')}
              >
                Upcoming
              </button>
              <button
                className={`dash-tab ${tab === 'completed' ? 'active' : ''}`}
                onClick={() => setTab('completed')}
              >
                Completed
              </button>
            </div>
          </div>

          {loading ? (
            <div className="dash-empty">Loading your trails…</div>
          ) : shown.length === 0 ? (
            <div className="dash-empty">
              <p>No {tab} trails yet.</p>
              <button className="dash-find-btn dash-find-btn--centered" onClick={() => navigate('/explore')}>
                Find New Trail
              </button>
            </div>
          ) : (
            <div className="dash-cards">
              {shown.map((t, i) => (
                <div className="dash-card" key={i} onClick={() => handleViewMap(t)} style={{ cursor: 'pointer' }}>
                  {/* Card image / gradient */}
                  <div
                    className="dash-card-img"
                    style={{ background: TERRAIN_GRADIENTS[t.trail_data?.terrain] || TERRAIN_GRADIENTS.mixed }}
                  >
                    {t.planned_date && (
                      <span className="dash-card-date">{formatDate(t.planned_date)}</span>
                    )}
                    <div className="dash-card-img-overlay" />
                  </div>

                  {/* Card body */}
                  <div className="dash-card-body">
                    <div className="dash-card-title-row">
                      <h3 className="dash-card-title">{t.trail_name}</h3>
                      <span className={`dash-diff-badge ${difficultyClass(t.trail_data?.difficulty)}`}>
                        {difficultyLabel(t.trail_data?.difficulty)}
                      </span>
                    </div>

                    <div className="dash-card-stats">
                      <div className="dash-stat">
                        <span className="dash-stat-label">DURATION</span>
                        <strong>{t.trail_data?.duration_hours ?? '—'} hrs</strong>
                      </div>
                      <div className="dash-stat">
                        <span className="dash-stat-label">TERRAIN</span>
                        <strong className="dash-stat-terrain">{t.trail_data?.terrain || '—'}</strong>
                      </div>
                    </div>

                    <div className="dash-card-actions" onClick={(e) => e.stopPropagation()}>
                      <button className="dash-view-btn" onClick={() => handleViewMap(t)}>
                        View Trail Map
                      </button>
                      <div className="dash-menu-wrap" ref={menuOpen === i ? menuRef : null}>
                        <button
                          className="dash-dots-btn"
                          onClick={() => setMenuOpen(menuOpen === i ? null : i)}
                          aria-label="Options"
                        >
                          <IconDots />
                        </button>
                        {menuOpen === i && (
                          <div className="dash-menu">
                            <button onClick={() => handleRemove(t)}>Remove trail</button>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
