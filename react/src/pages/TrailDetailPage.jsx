import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import Nav from '../components/Nav'
import TrailMap from '../components/TrailMap'
import { api } from '../api/client'
import { useApp } from '../context/AppContext'
import './TrailDetailPage.css'

function renderMd(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br/>')
}

export default function TrailDetailPage() {
  const { plannedTrail, trailStats: stats, trailPOIs: pois, user } = useApp()
  const navigate = useNavigate()
  const [chatHistory, setChatHistory] = useState([])
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const chatEndRef = useRef(null)

  useEffect(() => {
    if (!plannedTrail) navigate('/results')
  }, [plannedTrail])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatHistory])

  if (!plannedTrail) return null

  const t = plannedTrail
  const s = t._sustainability || {}
  const w = t._weather || {}
  const bio = t._biodiversity || {}

  const handleChat = async () => {
    if (!chatInput.trim()) return
    const msg = chatInput.trim()
    setChatInput('')
    const newHistory = [...chatHistory, { role: 'user', content: msg }]
    setChatHistory(newHistory)
    setChatLoading(true)
    try {
      const res = await api.chat(t, stats, pois, chatHistory, msg)
      setChatHistory(h => [...h, { role: 'assistant', content: res.reply }])
    } catch (e) {
      setChatHistory(h => [...h, { role: 'assistant', content: `Error: ${e.message}` }])
    } finally {
      setChatLoading(false)
    }
  }

  return (
    <div className="detail-page">
      <Nav activeLink="explore" />

      <div className="detail-header">
        <button className="back-link" onClick={() => navigate('/results')}>← Back to results</button>
        <h1>{t.name}</h1>
        <p className="detail-sub">{t.region} · Sustainability {s.score}/100 {s.label}</p>
      </div>

      {/* Stats bar */}
      <div className="stats-bar">
        <div className="stat">
          <div className="stat-value">{stats?.distance_km ?? '?'} km</div>
          <div className="stat-label">Distance</div>
          <div className="stat-hint">{stats?.source || ''}</div>
        </div>
        <div className="stat">
          <div className="stat-value">{stats?.duration_h ?? '?'} h</div>
          <div className="stat-label">Est. time</div>
          <div className="stat-hint">Naismith's Rule</div>
        </div>
        <div className="stat">
          <div className="stat-value">{(stats?.difficulty || t.difficulty || '?').charAt(0).toUpperCase() + (stats?.difficulty || t.difficulty || '?').slice(1)}</div>
          <div className="stat-label">Difficulty</div>
        </div>
        <div className="stat">
          <div className="stat-value">{stats?.ascent_m ?? '?'} m</div>
          <div className="stat-label">Ascent</div>
        </div>
        <div className="stat">
          <div className="stat-value">{(t.terrain || '?').charAt(0).toUpperCase() + (t.terrain || '?').slice(1)}</div>
          <div className="stat-label">Terrain</div>
        </div>
      </div>

      {stats?.source === 'estimated' && (
        <div className="stats-note warn">⚠️ Distance estimated — OSM tags unavailable for this trail.</div>
      )}
      {stats?.source === 'osm_tags' && (
        <div className="stats-note ok">✅ Distance from official OSM trail tags.</div>
      )}

      <div className="detail-layout">
        {/* Left: info + chat */}
        <div className="detail-left">
          {t.highlights?.length > 0 && (
            <div className="detail-card">
              <div className="detail-card-title">Highlights</div>
              <p>{t.highlights.join(' · ')}</p>
            </div>
          )}

          {w.temp_c != null && (
            <div className="detail-card">
              <div className="detail-card-title">Weather on your date</div>
              <p>🌤 {w.temp_c}°C, {w.conditions} · 💨 {w.wind_kmh} km/h</p>
              {w.safety_flags?.map((f, i) => (
                <div key={i} className="safety-flag">⚠️ {f}</div>
              ))}
            </div>
          )}

          {bio.notable_species?.length > 0 && (
            <div className="detail-card">
              <div className="detail-card-title">🦎 Nearby Wildlife</div>
              <p>{bio.notable_species.join(', ')}</p>
            </div>
          )}

          {/* Chat */}
          <div className="detail-card chat-card">
            <div className="detail-card-title">💬 Ask about this trail</div>
            <p className="chat-hint">Ask anything — what to pack, safety tips, nearby villages, best season…</p>

            <div className="chat-log">
              {chatHistory.length === 0 && (
                <div className="chat-empty">Ask Pathfinder anything about {t.name}…</div>
              )}
              {chatHistory.map((m, i) => (
                <div key={i} className={`detail-chat-msg ${m.role}`}>
                  <div className="detail-chat-bubble" dangerouslySetInnerHTML={{ __html: renderMd(m.content) }} />
                </div>
              ))}
              {chatLoading && (
                <div className="detail-chat-msg assistant">
                  <div className="detail-chat-bubble thinking">Thinking…</div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            <div className="chat-input-row">
              <input
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && !chatLoading && handleChat()}
                placeholder="Ask a question…"
                disabled={chatLoading}
              />
              <button onClick={handleChat} disabled={chatLoading || !chatInput.trim()}>
                {chatLoading ? '…' : 'Send'}
              </button>
            </div>

            {chatHistory.length > 0 && (
              <button className="clear-chat" onClick={() => setChatHistory([])}>Clear chat</button>
            )}
          </div>
        </div>

        {/* Right: map */}
        <div className="detail-right">
          <div className="detail-card">
            <div className="detail-card-title">🗺️ Trail &amp; Nearby Attractions</div>
            <TrailMap trails={[t]} pois={pois} height={420} />

            {pois.length > 0 && (
              <div className="poi-legend">
                {Object.entries(
                  pois.reduce((acc, p) => { acc[p.category] = acc[p.category] || []; acc[p.category].push(p); return acc }, {})
                ).map(([cat, items]) => (
                  <div key={cat} className="poi-legend-row">
                    <span>{items[0].emoji} <strong>{cat}</strong> ({items.length})</span>
                    <span className="poi-names">{items.slice(0,3).map(p => p.name).join(', ')}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
