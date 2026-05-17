import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AppProvider, useApp } from './context/AppContext'
import HomePage from './pages/HomePage'
import AuthPage from './pages/AuthPage'
import DashboardPage from './pages/DashboardPage'
import ExplorePage from './pages/ExplorePage'
import ResultsPage from './pages/ResultsPage'
import TrailDetailPage from './pages/TrailDetailPage'
import DiscoverPage from './pages/DiscoverPage'
import SurprisePage from './pages/SurprisePage'

function ProtectedRoute({ children }) {
  const { user } = useApp()
  return user ? children : <Navigate to="/auth" replace />
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/"        element={<HomePage />} />
      <Route path="/auth"    element={<AuthPage />} />
      <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
      <Route path="/explore"   element={<ProtectedRoute><ExplorePage /></ProtectedRoute>} />
      <Route path="/results"   element={<ProtectedRoute><ResultsPage /></ProtectedRoute>} />
      <Route path="/trail"     element={<ProtectedRoute><TrailDetailPage /></ProtectedRoute>} />
      <Route path="/discover"  element={<ProtectedRoute><DiscoverPage /></ProtectedRoute>} />
      <Route path="/surprise"  element={<ProtectedRoute><SurprisePage /></ProtectedRoute>} />
      <Route path="*"        element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AppProvider>
  )
}
