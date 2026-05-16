import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Nav from '../components/Nav'
import { api } from '../api/client'
import { useApp } from '../context/AppContext'
import TrailMap from '../components/TrailMap'
import './ResultsPage.css'

const SCORE_LABEL = (s) => s >= 80 ? '🌿 Excellent' : s >= 60 ? '✅ Good' : s >= 40 ? '⚠️ Moderate' : '🔴 Poor'
const SCORE_CLS   = (s) => s >= 60 ? 'good' : s >= 40 ? 'moderate' : 'poor'

function WeatherDay({ day }) {
  const label = day.date.slice(5)
  return (
    <div className={`weather-day ${day.is_planned ? 'planned' : ''}`}>
      <div className="wd-date">{label}{day.is_planned ? ' 🎯' : ''}</div>
      {day.available ? (
        <>
          <div className="wd-emoji">{day.emoji || '🌡️'}</div>
          <div className="wd-temp">{day.temp_c}°C</div>
          <div className="wd-cond">{day.conditions}</div>
        </>
      ) : (
        <div className="wd-na">{day.reason === 'too_far' ? '📅 >5 day' : '—'}</div>
      )}
    </div>
  )
}

function ScoreBreakdown({ breakdown }) {
  const items = [
    { label: 'Crowd avoidance', value: breakdown.crowd_avoidance, max: 25 },
    { label: 'Remoteness',      value: breakdown.remoteness,      max: 15 },
    { label: 'Biodiversity',    value: breakdown.biodiversity,    max: 20 },
    { label: 'Local economy',   value: breakdown.local_economy,   max: 20 },
    { label: 'Weather',         value: breakdown.weather,         max: 20 },
  ]
  return (
    <div className="score-breakdown">
      {items.map(item => (
        <div key={item.label} className="breakdown-row">
          <span className="bd-label">{item.label}</span>
          <div className="bd-bar-wrap">
            <div className="bd-bar" style={{ width: `${(item.value / item.max) * 100}%` }} />
          </div>
          <span className="bd-value">{item.value}/{item.max}</span>
        </div>
      ))}
    </div>
  )
}

function TrailCard({ trail, onPlan }) {
  const s   = trail._sustainability
  const ce  = trail._crowd_economy || {}
  const cal = trail._weather_calendar || []
  const [open, setOpen] = useState(false)

  return (
    <div className={`result-card score-border-${SCORE_CLS(s.score)}`}>
      <div className="result-card-header" onClick={() => setOpen(!open)}>
        <div className="result-card-left">
          <span className={`score-badge ${SCORE_CLS(s.score)}`}>{s.score}/100</span>
          <div>
            <div className="result-trail-name">{trail.name}</div>
            <div className="result-trail-meta">{trail.region} · {trail.terrain} · {trail.difficulty}</div>
          </div>
        </div>
        <div className="result-card-right">
          <span className="score-label">{SCORE_LABEL(s.score)}</span>
          <button className="expand-btn">{open ? '▲' : '▼'}</button>
        </div>
      </div>

      {open && (
        <div className="result-card-body">
          <ScoreBreakdown breakdown={s.breakdown} />

          {ce._crowd_poi_count != null && (
            <p className="ce-note">📍 {ce._crowd_poi_count} tourism POIs (3 km) · 🏘️ {ce._economy_poi_count} amenities (10 km)</p>
          )}

          {cal.length > 0 && (
            <div className="weather-calendar">
              <div className="wc-title">Weather around your dates:</div>
              <div className="wc-days">
                {cal.map((d, i) => <WeatherDay key={i} day={d} />)}
              </div>
            </div>
          )}

          {trail._weather?.safety_flags?.map((f, i) => (
            <div key={i} className="safety-flag">⚠️ {f}</div>
          ))}

          {trail._biodiversity?.notable_species?.length > 0 && (
            <p className="bio-note">🦎 <strong>Nearby species:</strong> {trail._biodiversity.notable_species.join(', ')}</p>
          )}

          <button className="plan-btn" onClick={() => onPlan(trail)}>
            📌 Plan this trail
          </button>
        </div>
      )}
    </div>
  )
}

export default function ResultsPage() {
  const { searchResults, user, setPlannedTrail, setTrailStats, setTrailPOIs } = useApp()
  const navigate = useNavigate()

  useEffect(() => {
    if (!searchResults) navigate('/explore')
  }, [searchResults])

  if (!searchResults) return null

  const { trails, itinerary, profile } = searchResults

  const handlePlan = async (trail) => {
    const [stats, poisData] = await Promise.all([
      api.getTrailStats(trail).catch(() => ({})),
      api.getTrailPOIs(trail.lat, trail.lon).catch(() => ({ pois: [] })),
    ])
    setPlannedTrail(trail)
    setTrailStats(stats)
    setTrailPOIs(poisData.pois || [])

    if (user) {
      api.saveTrail(user.id, trail, searchResults.answers || {}).catch(() => {})
    }
    navigate('/trail')
  }

  return (
    <div className="results-page">
      <Nav activeLink="explore" />
      <div className="results-layout">
        <div className="results-left">
          <div className="results-profile">
            <strong>Your profile:</strong>{' '}
            {profile.duration_days} day(s) · {profile.difficulty} · {profile.terrain} · {profile.fitness_level} fitness
            {profile.start_date && ` · ${profile.start_date}`}
          </div>
          <button className="back-btn" onClick={() => navigate('/explore')}>← New search</button>

          <h2 className="results-heading">Sustainability Scores</h2>
          <div className="results-trails">
            {trails.map((t, i) => (
              <TrailCard key={i} trail={t} onPlan={handlePlan} />
            ))}
          </div>

          <div className="itinerary-section">
            <h2>Your Itinerary</h2>
            <div className="itinerary-text" dangerouslySetInnerHTML={{ __html: itinerary.replace(/\n/g, '<br/>') }} />
          </div>
        </div>

        <div className="results-right">
          <h3>Trail Map</h3>
          <TrailMap trails={trails} height={520} />
        </div>
      </div>
    </div>
  )
}
