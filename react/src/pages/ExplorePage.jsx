import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useApp } from '../context/AppContext'
import TrailMap from '../components/TrailMap'
import forestImg from '../assets/ai.jpeg'
import './ExplorePage.css'

const today = new Date()
const addDays = (n) => { const d = new Date(today); d.setDate(d.getDate() + n); return d.toISOString().split('T')[0] }
const nextWeekend = () => {
  const day = today.getDay()
  const daysUntilSat = (6 - day + 7) % 7 || 7
  return addDays(daysUntilSat)
}

const STEPS = [
  {
    id: 'terrain',
    question: "Kalispera! I'm your AI guide. To tailor your experience, tell me: do you prefer coastal paths with sea views or rugged mountain peaks?",
    options: [
      { label: 'Coastal', value: 'coastal' },
      { label: 'Mountain', value: 'mountain' },
      { label: 'Forest', value: 'forest' },
      { label: 'Mixed', value: 'mixed' },
    ],
  },
  {
    id: 'duration_days',
    question: "How many days are you planning for this adventure?",
    options: [
      { label: '1 day', value: 1 },
      { label: '2 days', value: 2 },
      { label: '3 days', value: 3 },
      { label: '4–7 days', value: 5 },
    ],
  },
  {
    id: 'start_date',
    question: "When are you planning to set off?",
    type: 'date',
    options: [
      { label: 'This weekend', value: nextWeekend() },
      { label: 'Next week', value: addDays(7) },
      { label: 'In 2 weeks', value: addDays(14) },
    ],
  },
  {
    id: 'difficulty',
    question: "Also, what is your preferred challenge level for today's trek?",
    options: [
      { label: 'Easy', value: 'easy' },
      { label: 'Moderate', value: 'moderate' },
      { label: 'Challenging', value: 'hard' },
    ],
  },
  {
    id: 'fitness_level',
    question: "What's your current fitness level?",
    options: [
      { label: 'Easy-going', value: 'low' },
      { label: 'Average', value: 'medium' },
      { label: 'Fit & active', value: 'high' },
    ],
  },
  {
    id: 'interests',
    question: "What do you love most on a hike? Pick all that apply.",
    type: 'multi',
    options: [
      { label: 'Wildlife', value: 'wildlife' },
      { label: 'History & ruins', value: 'history' },
      { label: 'Photography', value: 'photography' },
      { label: 'Solitude', value: 'solitude' },
      { label: 'Local villages', value: 'local culture' },
      { label: 'Nature & flora', value: 'nature' },
      { label: 'Scenic views', value: 'views' },
    ],
  },
  {
    id: 'group_size',
    question: "Last one — who's coming with you?",
    options: [
      { label: 'Just me', value: 1 },
      { label: '2 people', value: 2 },
      { label: '3–5 people', value: 4 },
      { label: '6+ people', value: 7 },
    ],
  },
]

function AiAvatar() {
  return (
    <div className="ep-ai-avatar">
      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="12" cy="12" r="3" fill="white" />
        <path d="M6.3 17.7a8 8 0 0 1 0-11.4" stroke="white" strokeWidth="1.8" strokeLinecap="round" />
        <path d="M17.7 6.3a8 8 0 0 1 0 11.4" stroke="white" strokeWidth="1.8" strokeLinecap="round" />
        <path d="M9.2 14.8a4 4 0 0 1 0-5.6" stroke="white" strokeWidth="1.8" strokeLinecap="round" />
        <path d="M14.8 9.2a4 4 0 0 1 0 5.6" stroke="white" strokeWidth="1.8" strokeLinecap="round" />
      </svg>
    </div>
  )
}

export default function ExplorePage() {
  const { user, setSearchResults } = useApp()
  const navigate = useNavigate()

  const [messages, setMessages] = useState([{ role: 'assistant', content: STEPS[0].question }])
  const [step, setStep] = useState(0)
  const [answers, setAnswers] = useState({})
  const [done, setDone] = useState(false)
  const [loading, setLoading] = useState(false)
  const [freeText, setFreeText] = useState('')
  const [multiSelected, setMultiSelected] = useState([])
  const [customDate, setCustomDate] = useState('')
  const [mapTrails, setMapTrails] = useState(null)
  const chatEndRef = useRef(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const record = (display, value, stepId) => {
    const newAnswers = { ...answers, [stepId]: value }
    const nextStep = step + 1
    setAnswers(newAnswers)

    if (nextStep < STEPS.length) {
      setMessages(m => [...m,
        { role: 'user', content: display },
        { role: 'assistant', content: STEPS[nextStep].question },
      ])
      setStep(nextStep)
    } else {
      setMessages(m => [...m,
        { role: 'user', content: display },
        { role: 'assistant', content: "Perfect! I've got everything I need. Press Find my trails to see your personalised options on the map." },
      ])
      setStep(nextStep)
      setDone(true)
    }
    setFreeText('')
    setMultiSelected([])
  }

  const handleSearch = async () => {
    setLoading(true)
    const profile = {
      duration_days: Number(answers.duration_days) || 2,
      difficulty: ['easy', 'moderate', 'hard'].includes(answers.difficulty) ? answers.difficulty : 'moderate',
      terrain: ['coastal', 'mountain', 'forest', 'mixed'].includes(answers.terrain) ? answers.terrain : 'mixed',
      interests: Array.isArray(answers.interests) ? answers.interests : [],
      group_size: Number(answers.group_size) || 1,
      fitness_level: ['low', 'medium', 'high'].includes(answers.fitness_level) ? answers.fitness_level : 'medium',
      start_date: answers.start_date || '',
      region_filter: '',
    }
    try {
      const result = await api.searchTrails(profile)
      setSearchResults({ ...result, answers })
      setMapTrails(result.trails)
      setMessages(m => [...m, {
        role: 'assistant',
        content: `Found ${result.trails.length} trails matching your profile! Explore them on the map, or tap View full results for sustainability scores and details.`,
      }])
    } catch (e) {
      setMessages(m => [...m, { role: 'assistant', content: `Something went wrong: ${e.message}` }])
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setMessages([{ role: 'assistant', content: STEPS[0].question }])
    setStep(0)
    setAnswers({})
    setDone(false)
    setFreeText('')
    setMultiSelected([])
    setMapTrails(null)
  }

  const stepDef = STEPS[Math.min(step, STEPS.length - 1)]

  return (
    <div className="ep-page">
      {/* ── Left panel: background image or trail map ── */}
      <div className="ep-left">
        {mapTrails ? (
          <div className="ep-map-wrap">
            <TrailMap trails={mapTrails} height="100%" />
          </div>
        ) : (
          <div className="ep-bg" style={{ backgroundImage: `url(${forestImg})` }} />
        )}
      </div>

      {/* ── Right panel: chat ── */}
      <div className="ep-right">
        <div className="ep-header">
          <button className="ep-back-btn" onClick={() => navigate('/dashboard')}>
            ← Back to dashboard
          </button>
          <h1 className="ep-title">Plan your trail</h1>
          <p className="ep-subtitle">Tell us about your preferences to find the perfect trail for your next adventure.</p>
        </div>

        <div className="ep-divider" />

        <div className="ep-messages">
          {messages.map((msg, i) => (
            <div key={i} className={`ep-msg ep-msg--${msg.role}`}>
              {msg.role === 'assistant' && <AiAvatar />}
              <div className="ep-bubble">{msg.content}</div>
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>

        {/* Option chips for current step */}
        {!done && step < STEPS.length && (
          <div className="ep-options">
            {stepDef.type === 'multi' ? (
              <>
                <div className="ep-chips">
                  {stepDef.options.map(opt => (
                    <button
                      key={opt.value}
                      className={`ep-chip ${multiSelected.includes(opt.value) ? 'ep-chip--sel' : ''}`}
                      onClick={() => setMultiSelected(s =>
                        s.includes(opt.value) ? s.filter(v => v !== opt.value) : [...s, opt.value]
                      )}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
                <button className="ep-confirm-btn" onClick={() => {
                  const labels = stepDef.options.filter(o => multiSelected.includes(o.value)).map(o => o.label)
                  record(labels.join(', ') || 'No preference', multiSelected, stepDef.id)
                }}>
                  Confirm →
                </button>
              </>
            ) : stepDef.type === 'date' ? (
              <>
                <div className="ep-chips">
                  {stepDef.options.map(opt => (
                    <button key={opt.value} className="ep-chip" onClick={() => record(opt.label, opt.value, stepDef.id)}>
                      {opt.label}
                    </button>
                  ))}
                </div>
                <div className="ep-date-row">
                  <input
                    type="date"
                    className="ep-date-input"
                    value={customDate}
                    min={today.toISOString().split('T')[0]}
                    onChange={e => setCustomDate(e.target.value)}
                  />
                  <button className="ep-confirm-btn" disabled={!customDate}
                    onClick={() => record(customDate, customDate, stepDef.id)}>
                    Use this date →
                  </button>
                </div>
              </>
            ) : (
              <div className="ep-chips">
                {stepDef.options.map(opt => (
                  <button key={String(opt.value)} className="ep-chip"
                    onClick={() => record(opt.label, opt.value, stepDef.id)}>
                    {opt.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Done state: find / view results / reset */}
        {done && (
          <div className="ep-actions">
            {!mapTrails && (
              <button className="ep-find-btn" onClick={handleSearch} disabled={loading}>
                {loading ? <><span className="ep-spinner" /> Searching…</> : 'Find my trails →'}
              </button>
            )}
            {mapTrails && (
              <button className="ep-results-btn" onClick={() => navigate('/results')}>
                View full results →
              </button>
            )}
            <button className="ep-reset-btn" onClick={handleReset}>Start over</button>
          </div>
        )}

        {/* Text input (always visible) */}
        <div className="ep-input-row">
          <input
            className="ep-text-input"
            placeholder="Type your answer…"
            value={freeText}
            onChange={e => setFreeText(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && freeText.trim() && !done && step < STEPS.length) {
                record(freeText.trim(), freeText.trim(), stepDef.id)
              }
            }}
            disabled={done}
          />
          <button
            className="ep-send-btn"
            disabled={!freeText.trim() || done}
            onClick={() => {
              if (freeText.trim() && !done && step < STEPS.length) {
                record(freeText.trim(), freeText.trim(), stepDef.id)
              }
            }}
          >
            →
          </button>
        </div>
      </div>
    </div>
  )
}
