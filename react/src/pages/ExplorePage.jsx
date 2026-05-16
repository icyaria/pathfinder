import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import Nav from '../components/Nav'
import { api } from '../api/client'
import { useApp } from '../context/AppContext'
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
    id: 'terrain', question: "What kind of landscape are you dreaming of?",
    options: [
      { label: '🏔️ Mountain', value: 'mountain' },
      { label: '🌊 Coastal',   value: 'coastal'  },
      { label: '🌲 Forest',    value: 'forest'   },
      { label: '🗺️ Mixed — surprise me', value: 'mixed' },
    ],
  },
  {
    id: 'duration_days', question: "How many days are you planning for?",
    options: [
      { label: '1 day', value: 1 }, { label: '2 days', value: 2 },
      { label: '3 days', value: 3 }, { label: '4–7 days', value: 5 },
    ],
  },
  {
    id: 'start_date', question: "When are you planning to go?", type: 'date',
    options: [
      { label: 'This weekend', value: nextWeekend() },
      { label: 'Next week',    value: addDays(7)   },
      { label: 'In 2 weeks',   value: addDays(14)  },
    ],
  },
  {
    id: 'fitness_level', question: "What's your fitness level?",
    options: [
      { label: '🐢 Easy-going', value: 'low' },
      { label: '🚶 Average',    value: 'medium' },
      { label: '🏃 Fit & active', value: 'high' },
    ],
  },
  {
    id: 'difficulty', question: "How challenging do you want the trail to be?",
    options: [
      { label: 'Easy', value: 'easy' },
      { label: 'Moderate', value: 'moderate' },
      { label: 'Hard', value: 'hard' },
    ],
  },
  {
    id: 'interests', question: "What do you love most on a hike?", type: 'multi',
    options: [
      { label: '🦅 Wildlife', value: 'wildlife' },
      { label: '🏛️ History & ruins', value: 'history' },
      { label: '📸 Photography', value: 'photography' },
      { label: '🧘 Solitude', value: 'solitude' },
      { label: '🏘️ Local villages', value: 'local culture' },
      { label: '🌿 Nature & flora', value: 'nature' },
      { label: '🌅 Scenic views', value: 'views' },
    ],
  },
  {
    id: 'group_size', question: "Who's coming with you?",
    options: [
      { label: 'Just me 🧍', value: 1 }, { label: '2 people', value: 2 },
      { label: '3–5 people', value: 4 }, { label: '6+ people', value: 7 },
    ],
  },
]

const GREETING = "👋 Hey! I'm **Pathfinder**, your AI trail companion for Greece. Let's find the perfect hike for you — I'll ask a few quick questions.\n\n" + STEPS[0].question

function renderMd(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n\n/g, '<br/><br/>')
    .replace(/\n/g, '<br/>')
}

export default function ExplorePage() {
  const { user, setSearchResults } = useApp()
  const navigate = useNavigate()

  const [messages, setMessages] = useState([{ role: 'assistant', content: GREETING }])
  const [step, setStep] = useState(0)
  const [answers, setAnswers] = useState({})
  const [done, setDone] = useState(false)
  const [loading, setLoading] = useState(false)
  const [freeText, setFreeText] = useState('')
  const [showFree, setShowFree] = useState(false)
  const [multiSelected, setMultiSelected] = useState([])
  const [customDate, setCustomDate] = useState('')
  const chatEndRef = useRef(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const record = (display, value, stepId) => {
    const newMsg = { role: 'user', content: display }
    const newAnswers = { ...answers, [stepId]: value }
    const nextStep = step + 1
    setAnswers(newAnswers)

    if (nextStep < STEPS.length) {
      setMessages(m => [...m, newMsg, { role: 'assistant', content: STEPS[nextStep].question }])
      setStep(nextStep)
    } else {
      setMessages(m => [...m, newMsg, {
        role: 'assistant',
        content: "✅ Perfect! I've got everything I need.\n\nPress **Find my trails** below to get your personalised itinerary!"
      }])
      setStep(nextStep)
      setDone(true)
    }
    setFreeText('')
    setShowFree(false)
    setMultiSelected([])
  }

  const handleSearch = async () => {
    setLoading(true)
    const profile = {
      duration_days: Number(answers.duration_days) || 2,
      difficulty: ['easy','moderate','hard'].includes(answers.difficulty) ? answers.difficulty : 'moderate',
      terrain: ['coastal','mountain','forest','mixed'].includes(answers.terrain) ? answers.terrain : 'mixed',
      interests: Array.isArray(answers.interests) ? answers.interests : [],
      group_size: Number(answers.group_size) || 1,
      fitness_level: ['low','medium','high'].includes(answers.fitness_level) ? answers.fitness_level : 'medium',
      start_date: answers.start_date || '',
    }
    try {
      const result = await api.searchTrails(profile)
      setSearchResults({ ...result, answers })
      navigate('/results')
    } catch (e) {
      setMessages(m => [...m, { role: 'assistant', content: `❌ Something went wrong: ${e.message}` }])
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setMessages([{ role: 'assistant', content: GREETING }])
    setStep(0); setAnswers({}); setDone(false); setFreeText('')
    setShowFree(false); setMultiSelected([])
  }

  const stepDef = STEPS[Math.min(step, STEPS.length - 1)]

  return (
    <div className="explore-page">
      <Nav activeLink="explore" />

      <div className="explore-layout">
        {/* Sidebar */}
        <aside className="explore-sidebar">
          <div className="sidebar-brand">🧭 Pathfinder</div>
          <p className="sidebar-desc">Your AI trail companion for sustainable hiking in Greece.</p>
          <div className="sidebar-steps">
            {STEPS.map((s, i) => (
              <div key={s.id} className={`sidebar-step ${i < step ? 'done' : i === step ? 'active' : ''}`}>
                <span className="step-dot">{i < step ? '✓' : i + 1}</span>
                <span className="step-label">{s.id.replace('_', ' ')}</span>
              </div>
            ))}
          </div>
          {user && (
            <div className="sidebar-user">
              <div className="sidebar-avatar">{user.name[0]}</div>
              <span>{user.name} {user.surname}</span>
            </div>
          )}
        </aside>

        {/* Chat */}
        <main className="explore-main">
          <div className="chat-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`chat-msg ${msg.role}`}>
                {msg.role === 'assistant' && <div className="chat-avatar">🧭</div>}
                <div className="chat-bubble" dangerouslySetInnerHTML={{ __html: renderMd(msg.content) }} />
                {msg.role === 'user' && <div className="chat-avatar user-avatar">{user?.name?.[0] || '👤'}</div>}
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>

          {/* Input area */}
          {!done && step < STEPS.length && (
            <div className="chat-input-area">
              {stepDef.type === 'multi' ? (
                <div className="input-multi">
                  <div className="option-chips">
                    {stepDef.options.map(opt => (
                      <button
                        key={opt.value}
                        className={`chip ${multiSelected.includes(opt.value) ? 'selected' : ''}`}
                        onClick={() => setMultiSelected(s =>
                          s.includes(opt.value) ? s.filter(v => v !== opt.value) : [...s, opt.value]
                        )}
                      >{opt.label}</button>
                    ))}
                  </div>
                  <button className="confirm-btn" onClick={() => {
                    const labels = stepDef.options.filter(o => multiSelected.includes(o.value)).map(o => o.label)
                    record(labels.join(', ') || 'No preference', multiSelected, stepDef.id)
                  }}>Confirm ✓</button>
                </div>
              ) : stepDef.type === 'date' ? (
                <div className="input-date">
                  <div className="option-chips">
                    {stepDef.options.map(opt => (
                      <button key={opt.value} className="chip" onClick={() => record(opt.label, opt.value, stepDef.id)}>
                        {opt.label}
                      </button>
                    ))}
                  </div>
                  <div className="date-picker-row">
                    <input type="date" value={customDate}
                      min={today.toISOString().split('T')[0]}
                      onChange={e => setCustomDate(e.target.value)} />
                    <button className="confirm-btn" disabled={!customDate}
                      onClick={() => record(customDate, customDate, stepDef.id)}>
                      Use this date →
                    </button>
                  </div>
                </div>
              ) : (
                <div className="option-chips">
                  {stepDef.options.map(opt => (
                    <button key={String(opt.value)} className="chip"
                      onClick={() => record(opt.label, opt.value, stepDef.id)}>
                      {opt.label}
                    </button>
                  ))}
                </div>
              )}

              <div className="free-text-toggle">
                <button className="toggle-link" onClick={() => setShowFree(!showFree)}>
                  ✏️ Type your own answer
                </button>
                {showFree && (
                  <div className="free-input-row">
                    <input
                      value={freeText}
                      onChange={e => setFreeText(e.target.value)}
                      onKeyDown={e => e.key === 'Enter' && freeText.trim() && record(freeText.trim(), freeText.trim(), stepDef.id)}
                      placeholder="Your answer…"
                    />
                    <button onClick={() => freeText.trim() && record(freeText.trim(), freeText.trim(), stepDef.id)}
                      disabled={!freeText.trim()}>Submit →</button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Action buttons */}
          <div className="chat-actions">
            {done && (
              <button className="find-btn" onClick={handleSearch} disabled={loading}>
                {loading ? (
                  <span>🔍 Searching trails… <span className="spinner" /></span>
                ) : '🔍 Find my trails'}
              </button>
            )}
            <button className="reset-btn" onClick={handleReset}>🔄 Start over</button>
          </div>
        </main>
      </div>
    </div>
  )
}
