import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'

// Pages
import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Products from './pages/Products'
import Alerts from './pages/Alerts'
import Settings from './pages/Settings'
import Pricing from './pages/Pricing'

// Layout
import Layout from './components/Layout'

// Protected Route Component
function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  
  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>
  }
  
  return user ? children : <Navigate to="/login" />
}

function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/pricing" element={<Pricing />} />
      
      {/* Protected routes */}
      <Route path="/app" element={
        <ProtectedRoute>
          <Layout />
        </ProtectedRoute>
      }>
        <Route index element={<Dashboard />} />
        <Route path="products" element={<Products />} />
        <Route path="alerts" element={<Alerts />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}

export default App
