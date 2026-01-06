import { createContext, useContext, useState, useEffect } from 'react'
import api from '../utils/api'

const AuthContext = createContext()

export function useAuth() {
  return useContext(AuthContext)
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem('access_token')
    if (token) {
      fetchUser()
    } else {
      setLoading(false)
    }
  }, [])

  const fetchUser = async () => {
    try {
      const response = await api.get('/api/auth/me')
      setUser(response.data)
    } catch (error) {
      console.error('Error fetching user:', error)
      logout()
    } finally {
      setLoading(false)
    }
  }

  const login = async (email, password) => {
    const response = await api.post('/api/auth/login', { email, password })
    const { access_token, refresh_token } = response.data
    localStorage.setItem('access_token', access_token)
    localStorage.setItem('refresh_token', refresh_token)
    await fetchUser()
    return response.data
  }

  const register = async (userData) => {
    const response = await api.post('/api/auth/register', userData)
    const { access_token, refresh_token } = response.data
    localStorage.setItem('access_token', access_token)
    localStorage.setItem('refresh_token', refresh_token)
    await fetchUser()
    return response.data
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setUser(null)
  }

  const value = {
    user,
    loading,
    login,
    register,
    logout
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
