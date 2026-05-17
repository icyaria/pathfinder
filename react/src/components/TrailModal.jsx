import { useState, useEffect, useRef } from 'react'
import TrailMap from './TrailMap'
import { api } from '../api/client'
import { useApp } from '../context/AppContext'
import './TrailModal.css'

const TERRAIN_GRADIENTS = {
  mountain: 'linear-gradient(160deg, #6b4e11 0%, #b8893a 40%, #4a5a2a 100%)',
  coastal:  'linear-gradient(160deg, #0d3d5c 0%, #1a6a94 50%, #5db8d8 100%)',
  forest:   'linear-gradient(160deg, #0e2210 0%, #1e4a1a 50%, #4a7a30 100%)',
  mixed:    'linear-gradient(160deg, #1c2e1e 0%, #3a5430 50%, #6a8040 100%)',
}

const WEATHER_EMOJI = {
  Clear: '☀️', Clouds: '⛅', Rain: '🌧️', Drizzle: '🌦️',
  Thunderstorm: '⛈️', Snow: '❄️', Mist: '🌫️', Fog: '🌫️', Haze: '🌁',
}

const FAUNA_EMOJI = ['🦅', '🦌', '🐺', '🦊', '🐗', '🦎', '🦋', '🐦']

function cap(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : '—' }
function fmtDate(d) {
  if (!d) return null
  return new Date(d + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}
function renderMd(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br/>')
}

/* ── Star Rating component ───────────────────────────────────────── */
function StarRating({ avg, count, userRating, onRate, submitting }) {
  const [hovered, setHovered] = useState(null)
  const display = hovered ?? userRating ?? 0

  return (
    <div className="tm-rating">
      <div className="tm-stars">
        {[1, 2, 3, 4, 5].map(n => (
          <button
            key={n}
            className={`tm-star ${display >= n ? 'filled' : ''}`}
            onMouseEnter={() => setHovered(n)}
            onMouseLeave={() => setHovered(null)}
            onClick={() => !submitting && onRate(n)}
            aria-label={`Rate ${n} star${n > 1 ? 's' : ''}`}
          >★</button>
        ))}
      </div>
      <span className="tm-rating-meta">
        {avg != null
          ? <><strong>{avg}</strong> · {count} rating{count !== 1 ? 's' : ''}</>
          : 'No ratings yet'}
        {userRating && <span className="tm-my-rating"> · Your rating: {userRating}★</span>}
      </span>
    </div>
  )
}

/* ── Icons ───────────────────────────────────────────────────────── */
const IconDistance   = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" width="20" height="20"><path d="M3 12h18M3 6h18M3 18h18"/></svg>
const IconDuration   = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" width="20" height="20"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg>
const IconDifficulty = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" width="20" height="20"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
const IconGain       = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" width="20" height="20"><path d="M3 20l6-8 4 4 4-6 4 2"/><path d="M20 8V4h-4"/></svg>
const IconSend       = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>

/* ── Main modal ──────────────────────────────────────────────────── */
export default function TrailModal({ trail: saved, onClose }) {
  const { user } = useApp()
  const td = saved.trail_data
  const trailName = td?.name || saved.trail_name
  const overlayRef = useRef(null)
  const chatEndRef  = useRef(null)
  const chatInputRef = useRef(null)

  /* data state */
  const [stats,   setStats]   = useState(null)
  const [pois,    setPois]    = useState([])
  const [weather, setWeather] = useState(null)
  const [fauna,   setFauna]   = useState([])
  const [loading, setLoading] = useState(true)

  /* rating state */
  const [ratingData,  setRatingData]  = useState({ avg: null, count: 0 })
  const [userRating,  setUserRating]  = useState(null)
  const [submittingR, setSubmittingR] = useState(false)

  /* chat state */
  const [chatHistory,  setChatHistory]  = useState([])
  const [chatInput,    setChatInput]    = useState('')
  const [chatLoading,  setChatLoading]  = useState(false)

  /* lock scroll */
  useEffect(() => {
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = '' }
  }, [])

  /* close on Escape */
  useEffect(() => {
    const fn = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', fn)
    return () => window.removeEventListener('keydown', fn)
  }, [onClose])

  /* fetch trail data */
  useEffect(() => {
    const lat  = td?.lat
    const lon  = td?.lon
    const date = saved?.planned_date || ''

    Promise.all([
      api.getTrailStats(td).catch(() => null),
      lat && lon ? api.getTrailPOIs(lat, lon).catch(() => ({ pois: [] }))    : Promise.resolve({ pois: [] }),
      lat && lon ? api.getTrailWeather(lat, lon, date).catch(() => null)      : Promise.resolve(null),
      lat && lon ? api.getTrailBiodiversity(lat, lon).catch(() => null)       : Promise.resolve(null),
    ]).then(([s, poisData, w, bio]) => {
      setStats(s)
      setPois(poisData?.pois || [])
      setWeather(w)
      setFauna(bio?.notable_species || [])
      setLoading(false)
    })
  }, [])

  /* fetch ratings */
  useEffect(() => {
    api.getTrailRating(trailName).catch(() => null).then(r => r && setRatingData(r))
    if (user?.id) {
      api.getMyRating(user.id, trailName).catch(() => null).then(r => r?.rating != null && setUserRating(r.rating))
    }
  }, [trailName, user?.id])

  /* scroll chat to bottom */
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatHistory])

  const handleOverlay = (e) => { if (e.target === overlayRef.current) onClose() }

  /* rate trail */
  const handleRate = async (stars) => {
    if (!user?.id || submittingR) return
    setSubmittingR(true)
    setUserRating(stars)
    try {
      const result = await api.rateTrail(user.id, trailName, stars)
      setRatingData(result)
    } catch {}
    setSubmittingR(false)
  }

  /* send chat */
  const handleChat = async () => {
    const msg = chatInput.trim()
    if (!msg || chatLoading) return
    setChatInput('')
    const newHistory = [...chatHistory, { role: 'user', content: msg }]
    setChatHistory(newHistory)
    setChatLoading(true)
    try {
      const enrichedTrail = {
        ...td,
        _weather: weather || {},
        _biodiversity: { notable_species: fauna, total_observations: fauna.length },
      }
      const res = await api.chat(enrichedTrail, stats || {}, pois, chatHistory, msg)
      setChatHistory(h => [...h, { role: 'assistant', content: res.reply }])
    } catch (e) {
      setChatHistory(h => [...h, { role: 'assistant', content: `Sorry, something went wrong: ${e.message}` }])
    } finally {
      setChatLoading(false)
    }
  }

  const highlights  = td?.highlights || []
  const nearbyPois  = pois.slice(0, 3)
  const weatherEmoji = WEATHER_EMOJI[weather?.weather_main] || '🌤️'

  return (
    <div className="tm-overlay" ref={overlayRef} onClick={handleOverlay}>
      <div className="tm-modal" role="dialog" aria-modal="true">

        {/* ══ LEFT PANEL ══ */}
        <div className="tm-left">
          <div
            className="tm-hero"
            style={{ background: TERRAIN_GRADIENTS[td?.terrain] || TERRAIN_GRADIENTS.mixed }}
          >
            <div className="tm-hero-overlay" />
            <span className="tm-hero-terrain">{cap(td?.terrain)}</span>
          </div>

          <div className="tm-map-section">
            <div className="tm-map-header">
              <span className="tm-map-title">Nearby Points</span>
              {pois.length > 0 && <span className="tm-map-count">{pois.length} found</span>}
            </div>

            <div className="tm-map-wrap">
              {td?.lat && td?.lon ? (
                <TrailMap trails={[td]} pois={pois.slice(0, 20)} height={220} />
              ) : (
                <div className="tm-map-placeholder" />
              )}
            </div>

            {nearbyPois.length > 0 && (
              <div className="tm-poi-list">
                {nearbyPois.map((poi, i) => (
                  <div key={i} className="tm-poi-row">
                    <span className="tm-poi-emoji">{poi.emoji}</span>
                    <div className="tm-poi-info">
                      <span className="tm-poi-name">{poi.name}</span>
                      <span className="tm-poi-cat">{poi.category}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* ══ RIGHT PANEL ══ */}
        <div className="tm-right">
          <button className="tm-close" onClick={onClose} aria-label="Close">✕</button>

          <div className="tm-right-scroll">

            {/* Header + Rating */}
            <div className="tm-header">
              <h2 className="tm-name">{trailName}</h2>
              <p className="tm-location">{td?.region || 'Greece'}</p>
              <StarRating
                avg={ratingData.avg}
                count={ratingData.count}
                userRating={userRating}
                onRate={handleRate}
                submitting={submittingR}
              />
            </div>

            {/* Stat boxes */}
            <div className="tm-stats">
              <div className="tm-stat">
                <IconDistance />
                <span className="tm-stat-label">DISTANCE</span>
                <strong className="tm-stat-val">
                  {loading ? '…' : stats?.distance_km ? `${stats.distance_km}km` : '—'}
                </strong>
              </div>
              <div className="tm-stat">
                <IconDuration />
                <span className="tm-stat-label">DURATION</span>
                <strong className="tm-stat-val">
                  {saved.profile?.duration_days
                    ? `${saved.profile.duration_days} days`
                    : td?.duration_hours ? `${td.duration_hours} hrs` : '—'}
                </strong>
              </div>
              <div className="tm-stat">
                <IconDifficulty />
                <span className="tm-stat-label">DIFFICULTY</span>
                <strong className="tm-stat-val">
                  {loading ? '…' : cap(stats?.difficulty || td?.difficulty)}
                </strong>
              </div>
              <div className="tm-stat">
                <IconGain />
                <span className="tm-stat-label">GAIN</span>
                <strong className="tm-stat-val">
                  {loading ? '…' : stats?.ascent_m ? `+${stats.ascent_m}m` : '—'}
                </strong>
              </div>
            </div>

            {/* Weather */}
            <div className="tm-section">
              <div className="tm-section-title"><span>☀️</span> WEATHER FORECAST</div>
              {weather && !weather._skipped && weather.temp_c != null ? (
                <div className="tm-weather">
                  <div className="tm-weather-info">
                    <div className="tm-weather-temp">{weather.temp_c}°C</div>
                    <div className="tm-weather-cond">{cap(weather.conditions)}</div>
                    {saved.planned_date && (
                      <div className="tm-weather-date">
                        Scheduled: {fmtDate(saved.planned_date)}
                        {weather._forecast_note && ' (current conditions)'}
                      </div>
                    )}
                  </div>
                  <div className="tm-weather-emoji">{weatherEmoji}</div>
                </div>
              ) : (
                <div className="tm-empty-block">
                  {loading ? 'Loading forecast…' : 'Weather data unavailable'}
                </div>
              )}
            </div>

            {/* Highlights */}
            {highlights.length > 0 && (
              <div className="tm-section">
                <div className="tm-section-title"><span>📅</span> LOCAL HIGHLIGHTS</div>
                <div className="tm-events">
                  {highlights.map((h, i) => (
                    <div key={i} className="tm-event">
                      <div className="tm-event-name">{h}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Local Fauna */}
            {(loading || fauna.length > 0) && (
              <div className="tm-section">
                <div className="tm-section-title"><span>🦎</span> LOCAL FAUNA</div>
                {loading ? (
                  <div className="tm-empty-block">Loading species data…</div>
                ) : (
                  <div className="tm-fauna">
                    {fauna.slice(0, 4).map((species, i) => (
                      <div key={i} className="tm-fauna-card">
                        <div className="tm-fauna-avatar">{FAUNA_EMOJI[i % FAUNA_EMOJI.length]}</div>
                        <div className="tm-fauna-name">{species}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Mini chatbox */}
            <div className="tm-section">
              <div className="tm-section-title"><span>💬</span> ASK ABOUT THIS TRAIL</div>
              <div className="tm-chat">
                <div className="tm-chat-messages">
                  {chatHistory.length === 0 && (
                    <div className="tm-chat-hint">
                      Ask anything — what to pack, safety tips, best season, local villages…
                    </div>
                  )}
                  {chatHistory.map((m, i) => (
                    <div key={i} className={`tm-chat-msg tm-chat-msg--${m.role}`}>
                      <div
                        className="tm-chat-bubble"
                        dangerouslySetInnerHTML={{ __html: renderMd(m.content) }}
                      />
                    </div>
                  ))}
                  {chatLoading && (
                    <div className="tm-chat-msg tm-chat-msg--assistant">
                      <div className="tm-chat-bubble tm-chat-bubble--thinking">
                        <span className="tm-chat-dots"><span/><span/><span/></span>
                      </div>
                    </div>
                  )}
                  <div ref={chatEndRef} />
                </div>

                <div className="tm-chat-input-row">
                  <input
                    ref={chatInputRef}
                    className="tm-chat-input"
                    value={chatInput}
                    onChange={e => setChatInput(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleChat()}
                    placeholder="Ask a question…"
                    disabled={chatLoading}
                  />
                  <button
                    className="tm-chat-send"
                    onClick={handleChat}
                    disabled={chatLoading || !chatInput.trim()}
                    aria-label="Send"
                  >
                    <IconSend />
                  </button>
                </div>
              </div>
            </div>

            {/* Action button */}
            <div className="tm-actions">
              <button className="tm-btn tm-btn--secondary" disabled>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                  <line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
                </svg>
                Edit Dates
              </button>
            </div>

          </div>
        </div>

      </div>
    </div>
  )
}
