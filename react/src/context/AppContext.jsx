import { createContext, useContext, useState, useEffect, useCallback } from 'react'

const AppContext = createContext(null)

const DEFAULT_PREFS = {
  terrain:    { mountain: 0, coastal: 0, forest: 0, mixed: 0 },
  difficulty: { easy: 0, moderate: 0, hard: 0 },
  regions:    {},   // region string → score
  swipeCount: 0,
}

export function AppProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('pf_user')) } catch { return null }
  })

  const [preferences, setPreferences] = useState(() => {
    try { return JSON.parse(localStorage.getItem('pf_prefs')) || DEFAULT_PREFS } catch { return DEFAULT_PREFS }
  })

  const [searchResults, setSearchResults] = useState(null)
  const [plannedTrail, setPlannedTrail]   = useState(null)
  const [trailStats, setTrailStats]       = useState(null)
  const [trailPOIs, setTrailPOIs]         = useState([])

  useEffect(() => {
    if (user) localStorage.setItem('pf_user', JSON.stringify(user))
    else localStorage.removeItem('pf_user')
  }, [user])

  useEffect(() => {
    localStorage.setItem('pf_prefs', JSON.stringify(preferences))
  }, [preferences])

  // liked: true = right swipe, false = left swipe
  const recordSwipe = useCallback((trail, liked) => {
    setPreferences(prev => {
      const delta = liked ? 2 : -1
      const ter   = trail.terrain    || 'mixed'
      const dif   = trail.difficulty || 'moderate'
      const reg   = trail.region     || ''

      const terrain    = { ...prev.terrain,    [ter]: (prev.terrain[ter]    || 0) + delta }
      const difficulty = { ...prev.difficulty, [dif]: (prev.difficulty[dif] || 0) + delta }
      const regions    = { ...prev.regions,    [reg]: (prev.regions[reg]    || 0) + (liked ? 1 : 0) }

      return { terrain, difficulty, regions, swipeCount: prev.swipeCount + 1 }
    })
  }, [])

  const signOut = () => {
    setUser(null)
    setSearchResults(null)
    setPlannedTrail(null)
  }

  return (
    <AppContext.Provider value={{
      user, setUser, signOut,
      preferences, recordSwipe,
      searchResults, setSearchResults,
      plannedTrail, setPlannedTrail,
      trailStats, setTrailStats,
      trailPOIs, setTrailPOIs,
    }}>
      {children}
    </AppContext.Provider>
  )
}

export const useApp = () => useContext(AppContext)
