import { createContext, useContext, useState, useEffect } from 'react'

const AppContext = createContext(null)

export function AppProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('pf_user')) } catch { return null }
  })

  const [searchResults, setSearchResults] = useState(null)
  const [plannedTrail, setPlannedTrail] = useState(null)
  const [trailStats, setTrailStats] = useState(null)
  const [trailPOIs, setTrailPOIs] = useState([])

  useEffect(() => {
    if (user) localStorage.setItem('pf_user', JSON.stringify(user))
    else localStorage.removeItem('pf_user')
  }, [user])

  const signOut = () => {
    setUser(null)
    setSearchResults(null)
    setPlannedTrail(null)
  }

  return (
    <AppContext.Provider value={{
      user, setUser, signOut,
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
