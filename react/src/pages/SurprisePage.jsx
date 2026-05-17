import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Nav from '../components/Nav'
import RegionFilter from '../components/RegionFilter'
import { api } from '../api/client'
import { useApp } from '../context/AppContext'
import { Zap, Leaf, Compass, Sunset, Users, Bird, Landmark, Rocket, Clock, Sparkles, Milestone, Dices } from 'lucide-react'
import './SurprisePage.css'

const MOOD_CHIPS = [
  { id: 'adventurous', icon: <Zap size={15} />,      label: 'Adventurous',    text: 'I want something challenging and exciting' },
  { id: 'peaceful',    icon: <Leaf size={15} />,      label: 'Peaceful',       text: 'I want calm, quiet nature away from crowds' },
  { id: 'curious',     icon: <Compass size={15} />,   label: 'Curious',        text: 'I want to discover something new and surprising' },
  { id: 'romantic',    icon: <Sunset size={15} />,    label: 'Romantic',       text: 'A scenic trail for two, beautiful views' },
  { id: 'family',      icon: <Users size={15} />,     label: 'Family',         text: 'Easy and fun for all ages including kids' },
  { id: 'wildlife',    icon: <Bird size={15} />,      label: 'Wildlife lover', text: 'I want to spot animals and rare species' },
  { id: 'cultural',    icon: <Landmark size={15} />,  label: 'Cultural',       text: 'History, ruins, and local villages along the way' },
  { id: 'escape',      icon: <Rocket size={15} />,    label: 'Escape the city',text: 'As far from tourists and crowds as possible' },
]

export default function SurprisePage() {
  const { user, preferences, setPlannedTrail, setTrailStats, setTrailPOIs } = useApp()
  const navigate = useNavigate()

  const [selectedMood, setSelectedMood] = useState(null)
  const [customMood,   setCustomMood]   = useState('')
  const [regionId,     setRegionId]     = useState(null)
  const [loading,      setLoading]      = useState(false)
  const [result,       setResult]       = useState(null)
  const [error,        setError]        = useState('')

  const effectiveMood = selectedMood
    ? (MOOD_CHIPS.find(m => m.id === selectedMood)?.text || '') + (customMood ? '. ' + customMood : '')
    : customMood

  const handleSurprise = async () => {
    if (!effectiveMood.trim()) { setError('Pick a mood or describe how you feel.'); return }
    setError('')
    setLoading(true)
    setResult(null)
    try {
      const res = await api.surpriseMe(effectiveMood, regionId, preferences)
      setResult(res)
    } catch (e) {
      setError(e.message || 'Something went wrong.')
    } finally {
      setLoading(false)
    }
  }

  const handlePlan = async () => {
    if (!result?.trail) return
    const trail = result.trail
    api.registerInterest(trail.name).catch(() => {})
    const [stats, poisData] = await Promise.all([
      api.getTrailStats(trail).catch(() => ({})),
      api.getTrailPOIs(trail.lat, trail.lon).catch(() => ({ pois: [] })),
    ])
    setPlannedTrail(trail)
    setTrailStats(stats)
    setTrailPOIs(poisData.pois || [])
    if (user) api.saveTrail(user.id, trail, {}).catch(() => {})
    navigate('/trail')
  }

  const reset = () => { setResult(null); setSelectedMood(null); setCustomMood(''); setError('') }

  const ter = result?.trail?.terrain || 'mixed'
  const TERRAIN_BG = {
    mountain: 'linear-gradient(160deg, #0f1e10 0%, #1c3e14 60%, #0a1a0b 100%)',
    coastal:  'linear-gradient(160deg, #061a30 0%, #0f3560 60%, #041626 100%)',
    forest:   'linear-gradient(160deg, #081408 0%, #14340f 60%, #060e06 100%)',
    mixed:    'linear-gradient(160deg, #1a1206 0%, #372a0c 60%, #120e04 100%)',
  }

  return (
    <div className="surprise-page">
      <Nav activeLink="surprise" />

      <div className="surprise-inner">
        {!result ? (
          <>
            <div className="surprise-hero">
              <div className="surprise-emoji"><Dices size={48} strokeWidth={1.5} /></div>
              <h1>Surprise Me</h1>
              <p>Tell us how you feel right now and we'll find the perfect trail for your mood.</p>
            </div>

            <div className="surprise-controls">
              <div className="surprise-section-label">Choose a vibe</div>
              <div className="mood-chips">
                {MOOD_CHIPS.map(m => (
                  <button
                    key={m.id}
                    className={`mood-chip ${selectedMood === m.id ? 'active' : ''}`}
                    onClick={() => setSelectedMood(selectedMood === m.id ? null : m.id)}
                  >
                    {m.icon} {m.label}
                  </button>
                ))}
              </div>

              <div className="surprise-section-label" style={{ marginTop: 20 }}>Or describe in your own words</div>
              <textarea
                className="mood-textarea"
                placeholder="e.g. I want a hard solo hike, no tourist traps, maybe some wildlife…"
                value={customMood}
                onChange={e => setCustomMood(e.target.value)}
                rows={3}
              />

              <div className="surprise-filters">
                <RegionFilter value={regionId} onChange={setRegionId} />
              </div>

              {error && <p className="surprise-error">{error}</p>}

              <button
                className="surprise-btn"
                onClick={handleSurprise}
                disabled={loading}
              >
                {loading ? <><Sparkles size={16} /> Finding your trail…</> : <><Dices size={16} /> Surprise Me</>}
              </button>
            </div>
          </>
        ) : (
          <div className="surprise-result">
            <div className="sr-trail-card">
              <div className="sr-hero" style={{ background: TERRAIN_BG[ter] }}>
                <div className="sr-hero-overlay" />
                <div className="sr-region">{result.trail.region || 'Greece'}</div>
                <div className="sr-label">Your Surprise Match</div>
              </div>
              <div className="sr-body">
                <div className="sr-tags">
                  <span className="sr-tag">{result.trail.terrain}</span>
                  <span className="sr-tag">{result.trail.difficulty}</span>
                  <span className="sr-tag"><Clock size={12} /> {result.trail.duration_hours}h</span>
                </div>
                <h2 className="sr-name">{result.trail.name}</h2>
                <blockquote className="sr-reason">
                  <span className="sr-reason-icon"><Sparkles size={15} /></span>
                  {result.reason}
                </blockquote>
                {result.trail.highlights?.length > 0 && (
                  <ul className="sr-highlights">
                    {result.trail.highlights.map((h, i) => <li key={i}>{h}</li>)}
                  </ul>
                )}
                <div className="sr-actions">
                  <button className="sr-plan-btn" onClick={handlePlan}><Milestone /> Plan this trail</button>
                  <button className="sr-again-btn" onClick={reset}><Dices /> Try again</button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
