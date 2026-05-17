import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useApp } from '../context/AppContext'
import Nav from '../components/Nav'
import TrailModal from '../components/TrailModal'
import DiscoverSection from './DiscoverSection'
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
const IconChat = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="16" height="16">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
  </svg>
)

const TERRAIN_GRADIENTS = {
  mountain: 'linear-gradient(155deg, #b07a14 0%, #c8943a 45%, #4a5a2a 100%)',
  coastal:  'linear-gradient(155deg, #1a5276 0%, #2e86ab 50%, #a8d8ea 100%)',
  forest:   'linear-gradient(155deg, #1b3a1b 0%, #2d5a27 50%, #5a8a3a 100%)',
  mixed:    'linear-gradient(155deg, #2c3e50 0%, #4a6741 50%, #7d8b4a 100%)',
}

const MOCK_GROUP_CHATS = [
  {
    id: 1,
    name: 'Athos Peninsula Hikers',
    members: 14,
    lastMessage: 'Meeting point confirmed at the monastery gate at 8am',
    unread: 2,
    avatar: 'A',
    time: '1h ago',
    color: '#3a5c1a',
  },
  {
    id: 2,
    name: 'Crete Coastal Walkers',
    members: 9,
    lastMessage: 'Weather looks perfect this weekend! 🌤️',
    unread: 0,
    avatar: 'C',
    time: 'Yesterday',
    color: '#1a5276',
  },
  {
    id: 3,
    name: 'Monemvasia Explorers',
    members: 31,
    lastMessage: 'New photos from last week\'s hike just posted 📸',
    unread: 7,
    avatar: 'M',
    time: '3h ago',
    color: '#7a3a1a',
  },
]

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

function computeStats(trails) {
  const elevGain = { mountain: 820, coastal: 160, forest: 380, mixed: 480 }
  return {
    distance: Math.round(trails.reduce((s, t) => s + (t.trail_data?.duration_hours || 3) * 4.2, 0)),
    elevation: trails.reduce((s, t) => s + (elevGain[t.trail_data?.terrain] || 400), 0),
    count: trails.length,
  }
}

function getMonthlyActivity(trails) {
  const now = new Date()
  return Array.from({ length: 6 }, (_, i) => {
    const d = new Date(now.getFullYear(), now.getMonth() - 5 + i, 1)
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
    return {
      key,
      label: d.toLocaleString('en-US', { month: 'short' }).toUpperCase(),
      count: trails.filter(t => (t.saved_at || '').startsWith(key)).length,
    }
  })
}

function MiniCalendar({ trails }) {
  const now = new Date()
  const [view, setView] = useState({ year: now.getFullYear(), month: now.getMonth() })
  const { year, month } = view
  const todayStr = now.toISOString().split('T')[0]

  const trailMap = {}
  trails.forEach(t => {
    if (t.planned_date) {
      trailMap[t.planned_date] = [...(trailMap[t.planned_date] || []), t.trail_name]
    }
  })

  const firstDay = new Date(year, month, 1).getDay()
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const cells = [...Array(firstDay).fill(null)]
  for (let d = 1; d <= daysInMonth; d++) {
    const ds = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    cells.push({ day: d, dateStr: ds })
  }

  const prefix = `${year}-${String(month + 1).padStart(2, '0')}`
  const monthTrails = trails
    .filter(t => t.planned_date?.startsWith(prefix) && t.planned_date >= todayStr)
    .sort((a, b) => a.planned_date.localeCompare(b.planned_date))

  const prevMonth = () =>
    setView(v => v.month === 0 ? { year: v.year - 1, month: 11 } : { ...v, month: v.month - 1 })
  const nextMonth = () =>
    setView(v => v.month === 11 ? { year: v.year + 1, month: 0 } : { ...v, month: v.month + 1 })

  const monthLabel = new Date(year, month).toLocaleString('en-US', { month: 'long', year: 'numeric' })

  return (
    <div className="mini-cal">
      <div className="mini-cal-nav">
        <button className="mini-cal-arrow" onClick={prevMonth}>&#8249;</button>
        <span className="mini-cal-title">{monthLabel}</span>
        <button className="mini-cal-arrow" onClick={nextMonth}>&#8250;</button>
      </div>

      <div className="mini-cal-grid">
        {['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'].map(d => (
          <div key={d} className="cal-weekday">{d}</div>
        ))}
        {cells.map((cell, i) => (
          <div
            key={i}
            className={[
              'cal-day',
              !cell && 'cal-day--empty',
              cell?.dateStr === todayStr && 'cal-day--today',
              cell && trailMap[cell.dateStr] && 'cal-day--trail',
            ].filter(Boolean).join(' ')}
            title={cell && trailMap[cell.dateStr]?.join('\n')}
          >
            <span className="cal-day-num">{cell?.day}</span>
            {cell && trailMap[cell.dateStr] && <span className="cal-trail-dot" />}
          </div>
        ))}
      </div>

      {monthTrails.length > 0 ? (
        <ul className="cal-events">
          {monthTrails.slice(0, 4).map((t, i) => (
            <li key={i} className="cal-event">
              <span className="cal-event-marker" />
              <span className="cal-event-date">
                {new Date(t.planned_date + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              </span>
              <span className="cal-event-name" title={t.trail_name}>
                {t.trail_name.length > 30 ? t.trail_name.slice(0, 30) + '…' : t.trail_name}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="cal-empty-msg">No trails planned this month.</p>
      )}
    </div>
  )
}

function OverviewSection({ trails, loading, onViewAll, onViewMap }) {
  const todayStr = new Date().toISOString().split('T')[0]
  const upcoming = trails
    .filter(t => !t.planned_date || t.planned_date >= todayStr)
    .slice(0, 3)

  const stats = computeStats(trails)
  const monthly = getMonthlyActivity(trails)
  const maxCount = Math.max(...monthly.map(m => m.count), 1)

  return (
    <div className="overview-content">
      <div className="overview-header">
        <h1 className="dash-title">Explorer Dashboard</h1>
        <p className="dash-subtitle">
          Manage your sustainable itineraries, track your physical evolution, and see your impact on the Hellenic landscape.
        </p>
      </div>

      <div className="overview-top">
        {/* My Saved Trails */}
        <section className="overview-card">
          <div className="overview-card-head">
            <h2 className="overview-section-title">My Saved Trails</h2>
            <button className="overview-view-all" onClick={onViewAll}>View All</button>
          </div>
          {loading ? (
            <p className="overview-empty">Loading trails…</p>
          ) : upcoming.length === 0 ? (
            <p className="overview-empty">
              No upcoming trails.{' '}
              <button onClick={onViewAll} className="overview-inline-link">Find some →</button>
            </p>
          ) : (
            <div className="overview-trail-list">
              {upcoming.map((t, i) => (
                <div key={i} className="overview-trail-item" onClick={() => onViewMap(t)}>
                  <div
                    className="overview-trail-thumb"
                    style={{ background: TERRAIN_GRADIENTS[t.trail_data?.terrain] || TERRAIN_GRADIENTS.mixed }}
                  >
                    <span className={`overview-diff-badge ${difficultyClass(t.trail_data?.difficulty)}`}>
                      {difficultyLabel(t.trail_data?.difficulty)}
                    </span>
                  </div>
                  <div className="overview-trail-info">
                    <p className="overview-trail-name">{t.trail_name}</p>
                    <p className="overview-trail-meta">
                      {t.trail_data?.duration_hours
                        ? `${(t.trail_data.duration_hours * 4.2).toFixed(1)} km · ${t.trail_data.duration_hours} hrs`
                        : '—'}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Statistics */}
        <section className="overview-card overview-stats-card">
          <div className="overview-card-head">
            <h2 className="overview-section-title">Statistics</h2>
            <span className="overview-stats-pill">Last 6 Months</span>
          </div>

          <div className="overview-chart">
            {monthly.map((m, i) => {
              const pct = (m.count / maxCount) * 100
              return (
                <div key={m.key} className="chart-bar-wrap">
                  <div className="chart-bar-track">
                    <div
                      className={`chart-bar ${i === monthly.length - 1 ? 'chart-bar--current' : ''}`}
                      style={{ height: m.count > 0 ? `${Math.max(pct, 10)}%` : '3%' }}
                      title={`${m.count} trail${m.count !== 1 ? 's' : ''}`}
                    />
                  </div>
                  <span className="chart-label">{m.label}</span>
                </div>
              )
            })}
          </div>

          <div className="overview-stat-cards">
            <div className="stat-card">
              <span className="stat-card-label">Total Distance</span>
              <strong className="stat-card-value">{stats.distance} km</strong>
            </div>
            <div className="stat-card">
              <span className="stat-card-label">Elevation Gain</span>
              <strong className="stat-card-value">{stats.elevation.toLocaleString()} m</strong>
            </div>
            <div className="stat-card">
              <span className="stat-card-label">Trails Explored</span>
              <strong className="stat-card-value">{stats.count}</strong>
            </div>
          </div>
        </section>
      </div>

      <div className="overview-bottom">
        {/* Calendar */}
        <section className="overview-card">
          <div className="overview-card-head">
            <h2 className="overview-section-title">Upcoming Trails</h2>
          </div>
          <MiniCalendar trails={trails} />
        </section>

        {/* Group Chats */}
        <section className="overview-card">
          <div className="overview-card-head">
            <h2 className="overview-section-title">My Group Chats</h2>
            <span className="overview-chat-count">
              <IconChat /> {MOCK_GROUP_CHATS.length} active
            </span>
          </div>
          <div className="group-chat-list">
            {MOCK_GROUP_CHATS.map(chat => (
              <div key={chat.id} className="group-chat-item">
                <div className="chat-avatar-circle" style={{ background: chat.color }}>
                  {chat.avatar}
                </div>
                <div className="chat-info">
                  <div className="chat-info-top">
                    <span className="chat-name">{chat.name}</span>
                    <span className="chat-time">{chat.time}</span>
                  </div>
                  <div className="chat-info-bottom">
                    <span className="chat-last-msg">{chat.lastMessage}</span>
                    {chat.unread > 0 && <span className="chat-unread">{chat.unread}</span>}
                  </div>
                  <span className="chat-members">{chat.members} members</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}

function MyTrailsSection({ trails, loading, tab, setTab, menuOpen, setMenuOpen, menuRef, handleViewMap, handleRemove, navigate }) {
  const today = new Date().toISOString().split('T')[0]
  const upcoming  = trails.filter(t => !t.planned_date || t.planned_date >= today)
  const completed = trails.filter(t => t.planned_date && t.planned_date < today)
  const shown = tab === 'upcoming' ? upcoming : completed

  return (
    <>
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
              <div
                className="dash-card-img"
                style={{ background: TERRAIN_GRADIENTS[t.trail_data?.terrain] || TERRAIN_GRADIENTS.mixed }}
              >
                {t.planned_date && (
                  <span className="dash-card-date">{formatDate(t.planned_date)}</span>
                )}
                <div className="dash-card-img-overlay" />
              </div>
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
    </>
  )
}

export default function DashboardPage() {
  const { user, setPlannedTrail, recordSwipe } = useApp()
  const navigate = useNavigate()
  const [trails, setTrails] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeSection, setActiveSection] = useState('overview')
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

  const handleViewMap = (trail) => setActiveModal(trail)
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
        <aside className="dash-sidebar">
          <p className="dash-greeting">Hello, {user?.name}!</p>
          <button className="dash-find-btn" onClick={() => navigate('/explore')}>
            Find New Trail
          </button>
          <nav className="dash-sidenav">
            <div
              className={`dash-sidenav-item ${activeSection === 'overview' ? 'active' : ''}`}
              onClick={() => setActiveSection('overview')}
            >
              <IconOverview /> Overview
            </div>
            <div
              className={`dash-sidenav-item ${activeSection === 'mytrails' ? 'active' : ''}`}
              onClick={() => setActiveSection('mytrails')}
            >
              <IconTrails /> My Trails
            </div>
            <div
              className={`dash-sidenav-item ${activeSection === 'discover' ? 'active' : ''}`}
              onClick={() => setActiveSection('discover')}
            >
              <IconDiscover /> Discover
            </div>
            <div className="dash-sidenav-item disabled">
              <IconCommunity /> Community
            </div>
          </nav>
        </aside>

        <main className="dash-main">
          {activeSection === 'overview' && (
            <OverviewSection
              trails={trails}
              loading={loading}
              onViewAll={() => setActiveSection('mytrails')}
              onViewMap={handleViewMap}
            />
          )}
          {activeSection === 'mytrails' && (
            <MyTrailsSection
              trails={trails}
              loading={loading}
              tab={tab}
              setTab={setTab}
              menuOpen={menuOpen}
              setMenuOpen={setMenuOpen}
              menuRef={menuRef}
              handleViewMap={handleViewMap}
              handleRemove={handleRemove}
              navigate={navigate}
            />
          )}
          {activeSection === 'discover' && (
            <DiscoverSection user={user} recordSwipe={recordSwipe} />
          )}
        </main>
      </div>
    </div>
  )
}
