import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Nav from '../components/Nav'
import { api } from '../api/client'
import './HomePage.css'

const TERRAIN_CLS = {
  mountain: 'card-mountain', coastal: 'card-coastal',
  forest: 'card-forest', mixed: 'card-mixed',
}
const TERRAIN_EMJ = { mountain: '🏔️', coastal: '🌊', forest: '🌲', mixed: '🗺️' }

const PLACEHOLDER_TRAILS = [
  { name: 'Mytikas Summit Trail', region: 'Mount Olympus, Pieria', terrain: 'mountain', difficulty: 'hard',   duration_hours: 8 },
  { name: 'Caldera Rim Walk',     region: 'Santorini, Cyclades',  terrain: 'coastal',  difficulty: 'easy',   duration_hours: 3 },
  { name: 'Vikos Gorge Path',     region: 'Zagori, Epirus',       terrain: 'forest',   difficulty: 'moderate', duration_hours: 6 },
]

function TrailCard({ trail }) {
  const ter  = trail.terrain || 'mixed'
  const diff = trail.difficulty || 'moderate'
  return (
    <Link to="/explore" className={`trail-card ${TERRAIN_CLS[ter] || 'card-mixed'}`}>
      <div className="card-overlay" />
      <div className="card-badges">
        <span className="badge">{TERRAIN_EMJ[ter]} {ter.charAt(0).toUpperCase() + ter.slice(1)}</span>
        <span className="badge">{diff.charAt(0).toUpperCase() + diff.slice(1)}</span>
        {trail.sustainability_score && (
          <span className="badge badge-green">♻ {trail.sustainability_score}/100</span>
        )}
      </div>
      <div className="card-body">
        <div className="card-stars">★★★★☆</div>
        <div className="card-region">{trail.region || 'Greece'}</div>
        <h3>{trail.name}</h3>
        <div className="card-meta">⏱ {trail.duration_hours}h · {diff.charAt(0).toUpperCase() + diff.slice(1)}</div>
      </div>
    </Link>
  )
}

export default function HomePage() {
  const [featured, setFeatured] = useState(PLACEHOLDER_TRAILS)

  useEffect(() => {
    api.getFeaturedTrails(3)
      .then(d => { if (d.trails?.length) setFeatured(d.trails) })
      .catch(() => {})
  }, [])

  return (
    <div className="home">
      <Nav activeLink="home" />

      {/* Hero */}
      <section className="hero">
        <div className="hero-content">
          <span className="hero-badge">🌿 Sustainable Trekking v2.0</span>
          <h1>Discover Greece's<br /><em>Hidden Trails</em></h1>
          <p className="hero-sub">
            AI-powered trail recommendations that match your pace, protect local ecosystems,
            and connect you with the authentic soul of Greece.
          </p>
          <div className="hero-ctas">
            <Link to="/explore" className="cta-primary">Start New Trail</Link>
            <Link to="/explore" className="cta-secondary">Consult AI Guide</Link>
          </div>
        </div>
      </section>

      {/* Featured trails */}
      <section className="section">
        <p className="eyebrow">Featured Paths</p>
        <h2>Trails Worth The Journey</h2>
        <p className="section-lead">Hand-scored for sustainability, biodiversity, and authentic local experience.</p>
        <div className="trail-cards">
          {featured.map((t, i) => <TrailCard key={i} trail={t} />)}
        </div>
      </section>

      {/* Feature grid */}
      <section className="section alt-bg">
        <p className="eyebrow">Engineered for the Wild</p>
        <h2>Every Step, Data-Backed</h2>
        <p className="section-lead">Live feeds from OpenStreetMap, iNaturalist, and OpenWeatherMap — not guesses.</p>
        <div className="features">

          <div className="feature">
            <div className="feature-icon">🛰️</div>
            <h3>Real-Time Intelligence</h3>
            <p>Weather forecasts, trail crowd levels, and biodiversity data sourced live from open APIs on every search.</p>
            <div className="weather-box">
              <div className="weather-temp">22°C</div>
              <div className="weather-info">
                ☀️ Clear skies<br />
                <strong>Ideal hiking conditions</strong><br />
                Wind 12 km/h · Humidity 45%
              </div>
            </div>
          </div>

          <div className="feature feature-dark">
            <div className="feature-icon">🏛️</div>
            <h3>Cultural Anchors</h3>
            <p>Every trail mapped to nearby historic sites, local villages, and cultural events — so you never hike in a vacuum.</p>
            <div style={{ marginTop: 18 }}>
              <span className="event-tag">Local Event</span>
              <p className="event-text">
                <strong>Zagori Mountain Festival</strong><br />
                Traditional music &amp; food — every August in Monodendri village
              </p>
            </div>
          </div>

          <div className="feature feature-dark2">
            <div className="feature-icon">🤝</div>
            <h3>Trek Together</h3>
            <p>Solo or group — our AI adapts to your party size, fitness, and shared interests for a tailored experience.</p>
            <blockquote className="quote">
              "Found a trail I'd never have discovered on my own — perfect difficulty, zero crowds."
              <cite>— Nikos K., Athens · 3 trails planned</cite>
            </blockquote>
            <blockquote className="quote">
              "The sustainability score made me reconsider my route. Absolutely worth it."
              <cite>— Marianna T., Thessaloniki</cite>
            </blockquote>
          </div>

        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div>
          <div className="footer-logo">Path<span>Finder</span></div>
          <p>Deloitte Makeathon 2026 · Sustainable Tourism Initiative</p>
        </div>
        <div className="footer-links">
          <Link to="/explore">Explore</Link>
          <Link to="/">About</Link>
          <Link to="/auth">Sign Up</Link>
        </div>
        <p className="footer-data">Data: OpenStreetMap · OpenWeatherMap · iNaturalist · NASA SRTM</p>
      </footer>
    </div>
  )
}
