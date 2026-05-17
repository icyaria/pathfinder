import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useApp } from '../context/AppContext'
import './Nav.css'

const IconBell = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="20" height="20">
    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
    <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
  </svg>
)

export default function Nav({ activeLink }) {
  const { user, signOut } = useApp()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef(null)

  useEffect(() => {
    const close = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false)
    }
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [])

  const handleSignOut = () => {
    signOut()
    navigate('/')
    setMenuOpen(false)
  }

  return (
    <nav className="pf-nav">
      <Link to="/" className="pf-nav-logo">Path<span>Finder</span></Link>

      <div className="pf-nav-links">
        {user && (
          <Link to="/dashboard" className={activeLink === 'dashboard' ? 'active' : ''}>Dashboard</Link>
        )}
        <Link to="/" className={activeLink === 'home' ? 'active' : ''}>About Us</Link>
      </div>

      <div className="pf-nav-right">
        {user ? (
          <>
            <button className="pf-nav-bell" aria-label="Notifications">
              <IconBell />
            </button>
            <div className="pf-nav-avatar-wrap" ref={menuRef}>
              <button
                className="pf-nav-avatar"
                onClick={() => setMenuOpen(!menuOpen)}
                aria-label="Account menu"
              >
                {user.name[0].toUpperCase()}
              </button>
              {menuOpen && (
                <div className="pf-nav-dropdown">
                  <Link to="/dashboard" onClick={() => setMenuOpen(false)}>My Dashboard</Link>
                  <Link to="/explore" onClick={() => setMenuOpen(false)}>Find New Trail</Link>
                  <hr className="pf-nav-dropdown-hr" />
                  <button onClick={handleSignOut}>Sign Out</button>
                </div>
              )}
            </div>
          </>
        ) : (
          <>
            <Link to="/auth?mode=login" className="pf-btn-ghost">Login</Link>
            <Link to="/auth" className="pf-btn-olive">Sign Up</Link>
          </>
        )}
      </div>
    </nav>
  )
}
