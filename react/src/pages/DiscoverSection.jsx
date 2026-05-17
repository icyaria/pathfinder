import { useState, useEffect, useRef } from 'react'
import { api } from '../api/client'
import forestImg from '../assets/ai.jpeg'

const TERRAIN_EMJ = { mountain: '🏔️', coastal: '🌊', forest: '🌲', mixed: '🗺️' }
const DIFF_COLOR  = { easy: '#6b9e3a', moderate: '#d4891a', hard: '#c0392b' }

function SwipeCard({ trail, onSwipe, isTop }) {
  const cardRef  = useRef(null)
  const startX   = useRef(null)
  const currentX = useRef(0)

  const applyDrag = (dx) => {
    if (!cardRef.current) return
    const rotate = dx * 0.06
    cardRef.current.style.transform = `translateX(${dx}px) rotate(${rotate}deg)`
    cardRef.current.style.opacity = Math.max(0.6, 1 - Math.abs(dx) / 500)
    const likeEl = cardRef.current.querySelector('.ds-hint-like')
    const skipEl = cardRef.current.querySelector('.ds-hint-skip')
    if (likeEl) likeEl.style.opacity = dx > 30  ? Math.min(1, (dx - 30) / 80)  : 0
    if (skipEl) skipEl.style.opacity = dx < -30 ? Math.min(1, (-dx - 30) / 80) : 0
  }

  const settle = (liked) => {
    if (!cardRef.current) return
    const target = liked ? 700 : -700
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
  const onTouchEnd = () => {
    if (Math.abs(currentX.current) > 100) {
      settle(currentX.current > 0)
    } else {
      if (cardRef.current) {
        cardRef.current.style.transition = 'transform .3s'
        cardRef.current.style.transform  = ''
        cardRef.current.style.opacity    = '1'
      }
      const likeEl = cardRef.current?.querySelector('.ds-hint-like')
      const skipEl = cardRef.current?.querySelector('.ds-hint-skip')
      if (likeEl) likeEl.style.opacity = 0
      if (skipEl) skipEl.style.opacity = 0
    }
    currentX.current = 0
  }

  const ter = trail.terrain || 'mixed'

  return (
    <div
      ref={cardRef}
      className={`ds-card ${isTop ? 'ds-card-top' : 'ds-card-under'}`}
      onTouchStart={onTouchStart}
      onTouchMove={onTouchMove}
      onTouchEnd={onTouchEnd}
    >
      {isTop && <div className="ds-hint-like">SAVE ❤️</div>}
      {isTop && <div className="ds-hint-skip">SKIP ✕</div>}

      <div className="ds-card-hero">
        <img src={forestImg} alt="trail" className="ds-card-photo" />
        <div className="ds-card-overlay" />
        <span className="ds-card-region">{(trail.region || 'Greece').toUpperCase()}</span>
      </div>

      <div className="ds-card-body">
        <div className="ds-card-tags">
          <span className="ds-tag" style={{ color: DIFF_COLOR[trail.difficulty] || '#555' }}>
            ● {(trail.difficulty || 'moderate').charAt(0).toUpperCase() + (trail.difficulty || 'moderate').slice(1)}
          </span>
          <span className="ds-tag">⏱ {trail.duration_hours}h</span>
          <span className="ds-tag">{TERRAIN_EMJ[ter]} {ter.charAt(0).toUpperCase() + ter.slice(1)}</span>
        </div>

        <h2 className="ds-trail-name">{trail.name}</h2>

        {trail.highlights?.length > 0 && (
          <ul className="ds-highlights">
            {trail.highlights.slice(0, 3).map((h, i) => <li key={i}>{h}</li>)}
          </ul>
        )}

        {isTop && (
          <div className="ds-actions">
            <button className="ds-btn ds-skip" onClick={() => settle(false)} title="Skip">✕</button>
            <button className="ds-btn ds-like" onClick={() => settle(true)}  title="Save">❤️</button>
          </div>
        )}
      </div>
    </div>
  )
}

export default function DiscoverSection({ user, recordSwipe }) {
  const [trails,      setTrails]      = useState([])
  const [index,       setIndex]       = useState(0)
  const [loading,     setLoading]     = useState(true)
  const [showLiked,   setShowLiked]   = useState(false)
  const [likedTrails, setLikedTrails] = useState(() => {
    try { return JSON.parse(localStorage.getItem('pf_liked_trails')) || [] } catch { return [] }
  })

  useEffect(() => {
    api.discoverTrails(null, 40)
      .then(d => { setTrails(d.trails || []); setIndex(0) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    localStorage.setItem('pf_liked_trails', JSON.stringify(likedTrails))
  }, [likedTrails])

  const handleSwipe = (liked) => {
    const trail = trails[index]
    if (!trail) return
    recordSwipe(trail, liked)
    if (liked) {
      const updated = [...likedTrails, trail]
      setLikedTrails(updated)
      if (user) api.saveTrail(user.id, trail, {}).catch(() => {})
      api.registerInterest(trail.name).catch(() => {})
    }
    setIndex(i => i + 1)
  }

  const reload = () => {
    setLoading(true)
    api.discoverTrails(null, 40)
      .then(d => { setTrails(d.trails || []); setIndex(0) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  const current  = trails[index]
  const nextOne  = trails[index + 1]
  const exhausted = !loading && index >= trails.length

  return (
    <div className="ds-section">
      {/* Header */}
      <div className="ds-header">
        <div className="ds-header-text">
          <h1 className="dash-title">Discover</h1>
          <p className="ds-desc">
            Find your next trail match. Like the ones that call to you, skip the rest.
            You can find all your liked trails on the button above, and save the ones you are interested in.
          </p>
        </div>
        <button className="ds-my-trails-btn" onClick={() => setShowLiked(true)}>
          My <span className="ds-heart">❤️</span> Trails
          {likedTrails.length > 0 && <span className="ds-liked-badge">{likedTrails.length}</span>}
        </button>
      </div>

      {/* Liked trails panel */}
      {showLiked && (
        <div className="ds-liked-overlay" onClick={() => setShowLiked(false)}>
          <div className="ds-liked-panel" onClick={e => e.stopPropagation()}>
            <div className="ds-liked-head">
              <h2 className="ds-liked-title">My ❤️ Trails</h2>
              <button className="ds-liked-close" onClick={() => setShowLiked(false)}>✕</button>
            </div>
            {likedTrails.length === 0 ? (
              <p className="ds-liked-empty">No liked trails yet — start swiping!</p>
            ) : (
              <div className="ds-liked-list">
                {likedTrails.map((t, i) => (
                  <div key={i} className="ds-liked-item">
                    <div className="ds-liked-thumb">
                      <img src={forestImg} alt="" />
                      <span className="ds-liked-emoji">{TERRAIN_EMJ[t.terrain || 'mixed']}</span>
                    </div>
                    <div className="ds-liked-info">
                      <p className="ds-liked-name">{t.name}</p>
                      <p className="ds-liked-meta">
                        <span style={{ color: DIFF_COLOR[t.difficulty] || '#888' }}>
                          ● {(t.difficulty || 'moderate').charAt(0).toUpperCase() + (t.difficulty || 'moderate').slice(1)}
                        </span>
                        {' · '}⏱ {t.duration_hours}h · {(t.terrain || 'mixed').charAt(0).toUpperCase() + (t.terrain || 'mixed').slice(1)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Card stack */}
      {loading ? (
        <div className="ds-loading">Loading trails…</div>
      ) : exhausted ? (
        <div className="ds-done">
          <div className="ds-done-emoji">🎉</div>
          <h2>You've seen them all!</h2>
          <p>{likedTrails.length} trail{likedTrails.length !== 1 ? 's' : ''} liked.</p>
          <button className="ds-reload-btn" onClick={reload}>Shuffle Again</button>
        </div>
      ) : (
        <div className="ds-stage">
          {nextOne && <SwipeCard key={index + 1} trail={nextOne} onSwipe={() => {}} isTop={false} />}
          {current && <SwipeCard key={index}     trail={current} onSwipe={handleSwipe} isTop />}
          <p className="ds-counter">{index + 1} / {trails.length}</p>
        </div>
      )}
    </div>
  )
}
