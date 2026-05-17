import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { useApp } from '../context/AppContext'
import forestImg from '../assets/forest.jpg'
import mountainImg from '../assets/login-image.png'
import './AuthPage.css'

/* ── Icons ─────────────────────────────────────────────────────── */
const IconPerson = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="fi">
    <circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
  </svg>
)
const IconMail = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="fi">
    <rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>
  </svg>
)
const IconLock = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="fi">
    <rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>
  </svg>
)
const IconMap = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="fi">
    <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/><circle cx="12" cy="9" r="2.5"/>
  </svg>
)
const IconEye = ({ open }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="fi">
    {open
      ? <><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></>
      : <><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></>
    }
  </svg>
)
const IconLogin = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" width="18" height="18">
    <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/>
  </svg>
)
const IconGoogle = () => (
  <svg viewBox="0 0 24 24" width="18" height="18">
    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/>
    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
  </svg>
)

/* ── Component ─────────────────────────────────────────────────── */
export default function AuthPage() {
  const { user, setUser } = useApp()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [tab, setTab] = useState(searchParams.get('mode') === 'login' ? 'signin' : 'signup')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [agreed, setAgreed] = useState(false)
  const [showPw, setShowPw] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)

  const [signup, setSignup] = useState({
    name: '', surname: '', age: '', gender: 'Female',
    location: '', description: '', email: '', password: '', confirm: ''
  })
  const [loginEmail, setLoginEmail] = useState('')
  const [loginPw, setLoginPw] = useState('')

  useEffect(() => { if (user) navigate('/dashboard') }, [user])

  const handleSignup = async (e) => {
    e.preventDefault()
    setError('')
    if (!signup.name || !signup.surname || !signup.location || !signup.email || !signup.password)
      return setError('Please fill in all required fields.')
    if (signup.password !== signup.confirm)
      return setError('Passwords do not match.')
    if (!agreed)
      return setError('Please agree to the Terms of Service.')
    setLoading(true)
    try {
      const u = await api.signup({
        name: signup.name, surname: signup.surname, age: Number(signup.age) || 0,
        gender: signup.gender, location: signup.location,
        description: signup.description, password: signup.password, email: signup.email,
      })
      setUser({ id: u.user_id, name: u.name, surname: u.surname })
      navigate('/dashboard')
    } catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }

  const handleSignin = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const u = await api.signin(loginEmail, loginPw)
      setUser({ id: u.user_id, name: u.name, surname: u.surname })
      navigate('/dashboard')
    } catch { setError('Invalid email or password. Please try again.') }
    finally { setLoading(false) }
  }

  const switchTab = (t) => { setTab(t); setError(''); setShowPw(false) }

  const isLogin = tab === 'signin'

  return (
    <div className="auth-split">
      {/* ── Left image panel ── */}
      <div className="auth-left">
        <img
          src={isLogin ? mountainImg : forestImg}
          alt=""
          className="auth-left-img"
        />
        <div className="auth-left-overlay" />
        <div className="auth-left-text">
          {isLogin ? (
            <>
              <h1>PathFinder</h1>
              <p>Discover the soul of the Greek wilderness. Navigate ancient trails with precision-engineered AI intelligence.</p>
            </>
          ) : (
            <>
              <h1>Your journey in<br />the wild begins here.</h1>
              <p>"Explore ancient paths and untamed wilderness with AI-powered trail precision."</p>
            </>
          )}
        </div>
      </div>

      {/* ── Right form panel ── */}
      <div className="auth-right">
        <div className="auth-right-inner">
          <button type="button" className="auth-back-btn" onClick={() => navigate('/')}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
              <path d="M19 12H5M12 5l-7 7 7 7"/>
            </svg>
            Back to home
          </button>

          {/* ══ SIGN UP ══ */}
          {!isLogin && (
            <>
              <h2>Create Account</h2>
              <p className="auth-tagline">Embark on your next journey through the Hellenic landscape.</p>

              <div className="auth-oauth-row">
                <button type="button" className="auth-oauth-btn" disabled>
                  <IconGoogle /> Google
                </button>
                <button type="button" className="auth-oauth-btn auth-oauth-btn--apple" disabled>
                  <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.8-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/></svg>
                  Apple
                </button>
              </div>

              <div className="auth-divider"><span>OR WITH EMAIL</span></div>

              {error && <div className="auth-error">{error}</div>}

              <form onSubmit={handleSignup} className="auth-form">
                <div className="form-row">
                  <div className="su-wrap">
                    <input placeholder="First Name" value={signup.name} onChange={e => setSignup({ ...signup, name: e.target.value })} />
                    <IconPerson />
                  </div>
                  <div className="su-wrap">
                    <input placeholder="Last Name" value={signup.surname} onChange={e => setSignup({ ...signup, surname: e.target.value })} />
                    <IconPerson />
                  </div>
                </div>

                <div className="su-wrap">
                  <input type="email" placeholder="Email address" value={signup.email} onChange={e => setSignup({ ...signup, email: e.target.value })} />
                  <IconMail />
                </div>

                <div className="su-wrap">
                  <input placeholder="Location  (e.g. Athens, Greece)" value={signup.location} onChange={e => setSignup({ ...signup, location: e.target.value })} />
                  <IconMap />
                </div>

                <div className="form-row">
                  <div className="su-wrap">
                    <input type="number" min="1" max="120" placeholder="Age" value={signup.age} onChange={e => setSignup({ ...signup, age: e.target.value })} />
                  </div>
                  <div className="su-wrap su-wrap--select">
                    <select value={signup.gender} onChange={e => setSignup({ ...signup, gender: e.target.value })}>
                      <option>Female</option><option>Male</option><option>Other</option><option>Prefer not to say</option>
                    </select>
                  </div>
                </div>

                <div className="su-wrap">
                  <input type="password" placeholder="Password" value={signup.password} onChange={e => setSignup({ ...signup, password: e.target.value })} />
                  <IconLock />
                </div>

                <div className="su-wrap">
                  <input type="password" placeholder="Confirm Password" value={signup.confirm} onChange={e => setSignup({ ...signup, confirm: e.target.value })} />
                  <IconLock />
                </div>

                <label className="auth-checkbox">
                  <input type="checkbox" checked={agreed} onChange={e => setAgreed(e.target.checked)} />
                  <span>I agree to the <a href="#" onClick={e => e.preventDefault()}>Terms of Service</a> and our commitment to the <a href="#" onClick={e => e.preventDefault()}>Environmental Protection Policy</a>.</span>
                </label>

                <button type="submit" className="auth-submit" disabled={loading}>
                  {loading ? 'Creating account…' : 'Create Account →'}
                </button>
              </form>

              <p className="auth-switch">
                Already have an account?{' '}
                <button type="button" onClick={() => switchTab('signin')}>Login here</button>
              </p>
            </>
          )}

          {/* ══ SIGN IN ══ */}
          {isLogin && (
            <>
              <h2>Welcome Back</h2>
              <p className="auth-tagline">Continue your journey through the rugged Hellenic landscapes.</p>

              {error && <div className="auth-error">{error}</div>}

              <form onSubmit={handleSignin} className="auth-form">
                <div className="field-group">
                  <label className="field-label">EMAIL ADDRESS</label>
                  <div className="field-wrap">
                    <IconMail />
                    <input
                      type="email"
                      placeholder="alexandros@example.com"
                      value={loginEmail}
                      onChange={e => setLoginEmail(e.target.value)}
                    />
                  </div>
                </div>

                <div className="field-group">
                  <div className="field-label-row">
                    <span className="field-label">PASSWORD</span>
                    <span className="forgot-link">Forgot password?</span>
                  </div>
                  <div className="field-wrap">
                    <IconLock />
                    <input
                      type={showPw ? 'text' : 'password'}
                      placeholder="••••••••"
                      value={loginPw}
                      onChange={e => setLoginPw(e.target.value)}
                    />
                    <button type="button" className="eye-btn" onClick={() => setShowPw(v => !v)}>
                      <IconEye open={showPw} />
                    </button>
                  </div>
                </div>

                <button type="submit" className="auth-submit auth-submit--login" disabled={loading}>
                  <IconLogin />
                  {loading ? 'SIGNING IN…' : 'LOGIN'}
                </button>

                <div className="auth-divider"><span>OR CONTINUE WITH</span></div>

                <button type="button" className="auth-google-full" disabled>
                  <IconGoogle /> GOOGLE ACCOUNT
                </button>
              </form>

              <p className="auth-switch">
                Don't have an explorer account?{' '}
                <button type="button" onClick={() => switchTab('signup')}>Sign Up for free</button>
              </p>

              <p className="auth-footer">© 2024 PathFinder Orama. Built for the wild.</p>
            </>
          )}

        </div>
      </div>
    </div>
  )
}
