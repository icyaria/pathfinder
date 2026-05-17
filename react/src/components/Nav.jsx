import { Link, useNavigate } from 'react-router-dom'
import { useApp } from '../context/AppContext'
import './Nav.css'

export default function Nav({ activeLink }) {
  const { user, signOut } = useApp()
  const navigate = useNavigate()

  const handleSignOut = () => {
    signOut()
    navigate('/')
  }

  return (
    <nav className="pf-nav">
      <Link to="/" className="pf-nav-logo">Path<span>Finder</span></Link>
      <div className="pf-nav-links">
        <Link to="/explore"   className={activeLink === 'explore'   ? 'active' : ''}>Explore</Link>
        <Link to="/discover"  className={activeLink === 'discover'  ? 'active' : ''}>Discover</Link>
        <Link to="/surprise"  className={activeLink === 'surprise'  ? 'active' : ''}>Surprise Me</Link>
        <Link to="/"          className={activeLink === 'home'      ? 'active' : ''}>About Us</Link>
      </div>
      <div className="pf-nav-right">
        {user ? (
          <>
            <span className="pf-nav-user">Hi, {user.name}!</span>
            {activeLink !== 'explore' && (
              <Link to="/explore" className="pf-btn-olive">Open App →</Link>
            )}
            <button onClick={handleSignOut} className="pf-btn-ghost">Sign Out</button>
          </>
        ) : (
          <>
            <Link to="/auth" className="pf-btn-ghost">Login</Link>
            <Link to="/auth" className="pf-btn-olive">Sign Up</Link>
          </>
        )}
      </div>
    </nav>
  )
}
