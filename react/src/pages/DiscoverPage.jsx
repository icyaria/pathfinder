import { useEffect, useState, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import Nav from '../components/Nav'
import RegionFilter from '../components/RegionFilter'
import { api } from '../api/client'
import { useApp } from '../context/AppContext'
import './DiscoverPage.css'

const TERRAIN_EMJ = { mountain: '🏔️', coastal: '🌊', forest: '🌲', mixed: '🗺️' }
const DIFF_COLOR  = { easy: '#6b9e3a', moderate: '#d4891a', hard: '#c0392b' }

function TrailSwipeCard({ trail, onSwipe, isTop }) {
  const cardRef  = useRef(null)
  const startX   = useRef(null)
  const currentX = useRef(0)

  const applyDrag = (dx) => {
    if (!cardRef.current) return
    const rotate = dx * 0.06
    const opacity = Math.max(0.6, 1 - Math.abs(dx) / 500)
    cardRef.current.style.transform = `translateX(${dx}px) rotate(${rotate}deg)`
    cardRef.current.style.opacity   = opacity
    const likeEl = cardRef.current.querySelector('.swipe-hint-like')
    const skipEl = cardRef.current.querySelector('.swipe-hint-skip')
    if (likeEl) likeEl.style.opacity = dx > 30  ? Math.min(1, (dx - 30) / 80)  : 0
    if (skipEl) skipEl.style.opacity = dx < -30 ? Math.min(1, (-dx - 30) / 80) : 0
  }

  const settle = (liked) => {
    if (!cardRef.current) return
    const target = liked ? 600 : -600
    cardRef.current.style.transition = 'transform .35s ease, opacity .35s'
    cardRef.current.style.transform  = `translateX(${target}px) rotate(${liked ? 20 : -20}deg)`
    cardRef.current.style.opacity    = '0'
    setTimeout(() => onSwipe(liked), 360)
  }

  const onTouchStart = (e) => { startX.current = e.touches[0].clientX }
  const onTouchMove  = (e) => {
    currentX.current = e.touches[0].clientX - startX.current
    applyDrag(currentX.current)
  }
  const onTouchEnd   = () => {
    if (Math.abs(currentX.current) > 100) { settle(currentX.current > 0) }
    else {
      if (cardRef.current) { cardRef.current.style.transition = 'transform .3s'; cardRef.current.style.transform = '' ; cardRef.current.style.opacity = '1' }
      const likeEl = cardRef.current?.querySelector('.swipe-hint-like')
      const skipEl = cardRef.current?.querySelector('.swipe-hint-skip')
      if (likeEl) likeEl.style.opacity = 0
      if (skipEl) skipEl.style.opacity = 0
    }
    currentX.current = 0
  }

  const ter = trail.terrain || 'mixed'

  return (
    <div
      ref={cardRef}
      className={`swipe-card ${isTop ? 'swipe-card-top' : 'swipe-card-under'}`}
      onTouchStart={onTouchStart}
      onTouchMove={onTouchMove}
      onTouchEnd={onTouchEnd}
    >
      <div className="swipe-hint-like">SAVE ❤️</div>
      <div className="swipe-hint-skip">SKIP ✕</div>

      <div className="swipe-card-hero">
        <div className={`swipe-terrain-bg terrain-${ter}`} />
        <div className="swipe-terrain-emoji">{TERRAIN_EMJ[ter]}</div>
        <div className="swipe-card-overlay" />
        <div className="swipe-card-region">{trail.region || 'Greece'}</div>
      </div>

      <div className="swipe-card-body">
        <div className="swipe-card-tags">
          <span className="swipe-tag" style={{ color: DIFF_COLOR[trail.difficulty] || '#555' }}>
            ● {(trail.difficulty || 'moderate').charAt(0).toUpperCase() + (trail.difficulty || 'moderate').slice(1)}
          </span>
          <span className="swipe-tag">⏱ {trail.duration_hours}h</span>
          <span className="swipe-tag">{TERRAIN_EMJ[ter]} {ter.charAt(0).toUpperCase() + ter.slice(1)}</span>
        </div>
        <h2 className="swipe-trail-name">{trail.name}</h2>
        {trail.highlights?.length > 0 && (
          <ul className="swipe-highlights">
            {trail.highlights.slice(0, 3).map((h, i) => <li key={i}>{h}</li>)}
          </ul>
        )}
      </div>

      {isTop && (
        <div className="swipe-actions">
          <button className="swipe-btn skip-btn" onClick={() => settle(false)} title="Skip">✕</button>
          <button className="swipe-btn like-btn" onClick={() => settle(true)}  title="Save">❤️</button>
        </div>
      )}
    </div>
  )
}

export default function DiscoverPage() {
  const { user, preferences, recordSwipe, setPlannedTrail, setTrailStats, setTrailPOIs } = useApp()
  const navigate = useNavigate()

  const [trails,    setTrails]    = useState([])
  const [index,     setIndex]     = useState(0)
  const [regionId,  setRegionId]  = useState(null)
  const [loading,   setLoading]   = useState(true)
  const [saved,     setSaved]     = useState(0)
  const [showPrefs, setShowPrefs] = useState(false)

  const load = useCallback((rid) => {
    setLoading(true)
    api.discoverTrails(rid, 40)
      .then(d => { setTrails(d.trails || []); setIndex(0) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { load(regionId) }, [regionId])

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'ArrowRight') handleSwipe(true)
      if (e.key === 'ArrowLeft')  handleSwipe(false)
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  })

  const handleSwipe = (liked) => {
    const trail = trails[index]
    if (!trail) return
    recordSwipe(trail, liked)
    if (liked) {
      setSaved(s => s + 1)
      if (user) api.saveTrail(user.id, trail, {}).catch(() => {})
      api.registerInterest(trail.name).catch(() => {})
    }
    setIndex(i => i + 1)
  }

  const handlePlan = async (trail) => {
    const [stats, poisData] = await Promise.all([
      api.getTrailStats(trail).catch(() => ({})),
      api.getTrailPOIs(trail.lat, trail.lon).catch(() => ({ pois: [] })),
    ])
    setPlannedTrail(trail)
    setTrailStats(stats)
    setTrailPOIs(poisData.pois || [])
    navigate('/trail')
  }

  const current  = trails[index]
  const nextOne  = trails[index + 1]
  const exhausted = !loading && index >= trails.length

  const topPrefs = () => {
    const ter = Object.entries(preferences.terrain || {}).sort((a,b)=>b[1]-a[1]).filter(([,v])=>v>0)
    const dif = Object.entries(preferences.difficulty || {}).sort((a,b)=>b[1]-a[1]).filter(([,v])=>v>0)
    return { ter, dif }
  }

  return (
    <div className="discover-page">
      <Nav activeLink="discover" />

      <div className="discover-header">
        <div className="discover-header-left">
          <h1 className="discover-title">Discover Trails</h1>
          <p className="discover-sub">Swipe right to save · left to skip · ← → keys work too</p>
        </div>
        <div className="discover-header-right">
          <RegionFilter value={regionId} onChange={setRegionId} />
          <button className="prefs-toggle" onClick={() => setShowPrefs(!showPrefs)}>
            🧠 {preferences.swipeCount > 0 ? `${preferences.swipeCount} swipes` : 'Preferences'}
          </button>
        </div>
      </div>

      {showPrefs && preferences.swipeCount > 0 && (
        <div className="prefs-panel">
          <strong>Your taste profile (auto-learned)</strong>
          {(() => { const { ter, dif } = topPrefs(); return (
            <div className="prefs-chips">
              {ter.map(([t, v]) => <span key={t} className="pref-chip terrain">{TERRAIN_EMJ[t]} {t} ({v>0?'+':''}{v})</span>)}
              {dif.map(([d, v]) => <span key={d} className="pref-chip diff">{d} ({v>0?'+':''}{v})</span>)}
            </div>
          )})()}
          <p className="prefs-note">These weights quietly influence Surprise Me recommendations.</p>
        </div>
      )}

      {loading ? (
        <div className="discover-loading">Loading trails…</div>
      ) : exhausted ? (
        <div className="discover-done">
          <div className="discover-done-emoji">🎉</div>
          <h2>You've seen them all!</h2>
          <p>{saved} trail{saved !== 1 ? 's' : ''} saved to your profile.</p>
          <div className="discover-done-btns">
            <button className="disc-action-btn primary" onClick={() => load(regionId)}>Shuffle Again</button>
            <button className="disc-action-btn" onClick={() => navigate('/explore')}>Full Search</button>
          </div>
        </div>
      ) : (
        <div className="swipe-stage">
          {/* Next card behind */}
          {nextOne && <TrailSwipeCard key={index + 1} trail={nextOne} onSwipe={() => {}} isTop={false} />}
          {/* Current card on top */}
          {current && <TrailSwipeCard key={index} trail={current} onSwipe={handleSwipe} isTop />}

          <div className="swipe-counter">{index + 1} / {trails.length}</div>

          <button className="plan-inline-btn" onClick={() => handlePlan(current)}>
            📌 Plan now
          </button>
        </div>
      )}
    </div>
  )
}
