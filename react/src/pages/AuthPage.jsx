import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Nav from '../components/Nav'
import { api } from '../api/client'
import { useApp } from '../context/AppContext'
import './AuthPage.css'

export default function AuthPage() {
  const { user, setUser } = useApp()
  const navigate = useNavigate()
  const [tab, setTab] = useState('signup')
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Signup form
  const [signup, setSignup] = useState({
    name: '', surname: '', age: '', gender: 'Female',
    location: '', description: '', password: '', confirm: ''
  })

  // Signin form
  const [selectedUser, setSelectedUser] = useState('')
  const [signinPw, setSigninPw] = useState('')

  useEffect(() => {
    if (user) navigate('/explore')
  }, [user])

  useEffect(() => {
    api.listUsers().then(d => {
      setUsers(d.users || [])
      if (d.users?.length) setSelectedUser(d.users[0].id)
    }).catch(() => {})
  }, [])

  const handleSignup = async (e) => {
    e.preventDefault()
    setError('')
    if (!signup.name || !signup.surname || !signup.location || !signup.password) {
      return setError('Please fill in all required fields.')
    }
    if (signup.password !== signup.confirm) return setError('Passwords do not match.')
    setLoading(true)
    try {
      const u = await api.signup({
        name: signup.name, surname: signup.surname, age: Number(signup.age) || 0,
        gender: signup.gender, location: signup.location,
        description: signup.description, password: signup.password,
      })
      setUser({ id: u.user_id, name: u.name, surname: u.surname })
      navigate('/explore')
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSignin = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const u = await api.signin(selectedUser, signinPw)
      setUser({ id: u.user_id, name: u.name, surname: u.surname })
      navigate('/explore')
    } catch (e) {
      setError('Invalid password. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <Nav />
      <div className="auth-container">
        <h2>Welcome to PathFinder</h2>
        <p className="auth-sub">Create an account or sign in to start planning your trail.</p>

        <div className="auth-tabs">
          <button className={tab === 'signup' ? 'active' : ''} onClick={() => { setTab('signup'); setError('') }}>
            ✨ Sign Up
          </button>
          <button className={tab === 'signin' ? 'active' : ''} onClick={() => { setTab('signin'); setError('') }}>
            🔑 Sign In
          </button>
        </div>

        {error && <div className="auth-error">{error}</div>}

        {tab === 'signup' && (
          <form onSubmit={handleSignup} className="auth-form">
            <div className="form-row">
              <label>First Name *
                <input value={signup.name} onChange={e => setSignup({...signup, name: e.target.value})} placeholder="e.g., Maria" />
              </label>
              <label>Last Name *
                <input value={signup.surname} onChange={e => setSignup({...signup, surname: e.target.value})} placeholder="e.g., Papadopoulou" />
              </label>
            </div>
            <div className="form-row">
              <label>Age
                <input type="number" min="1" max="120" value={signup.age} onChange={e => setSignup({...signup, age: e.target.value})} />
              </label>
              <label>Gender
                <select value={signup.gender} onChange={e => setSignup({...signup, gender: e.target.value})}>
                  <option>Female</option><option>Male</option><option>Other</option><option>Prefer not to say</option>
                </select>
              </label>
            </div>
            <label>Location *
              <input value={signup.location} onChange={e => setSignup({...signup, location: e.target.value})} placeholder="e.g., Athens, Greece" />
            </label>
            <label>About you (optional)
              <textarea value={signup.description} onChange={e => setSignup({...signup, description: e.target.value})} placeholder="e.g., I love remote mountain hikes with wildlife." maxLength={256} rows={3} />
            </label>
            <label>Password *
              <input type="password" value={signup.password} onChange={e => setSignup({...signup, password: e.target.value})} />
            </label>
            <label>Confirm Password *
              <input type="password" value={signup.confirm} onChange={e => setSignup({...signup, confirm: e.target.value})} />
            </label>
            <button type="submit" className="auth-submit" disabled={loading}>
              {loading ? 'Creating account…' : 'Create Account'}
            </button>
          </form>
        )}

        {tab === 'signin' && (
          <form onSubmit={handleSignin} className="auth-form">
            {users.length === 0 ? (
              <p className="auth-info">No accounts yet. Please sign up first.</p>
            ) : (
              <>
                <label>Select your account
                  <select value={selectedUser} onChange={e => setSelectedUser(e.target.value)}>
                    {users.map(u => (
                      <option key={u.id} value={u.id}>{u.name} {u.surname} ({u.id})</option>
                    ))}
                  </select>
                </label>
                <label>Password
                  <input type="password" value={signinPw} onChange={e => setSigninPw(e.target.value)} />
                </label>
                <button type="submit" className="auth-submit" disabled={loading}>
                  {loading ? 'Signing in…' : 'Sign In'}
                </button>
              </>
            )}
          </form>
        )}
      </div>
    </div>
  )
}
