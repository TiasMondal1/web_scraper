import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import api from '../utils/api'
import { ChartBarIcon, BellIcon, ShoppingBagIcon, CurrencyDollarIcon } from '@heroicons/react/24/outline'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      const response = await api.get('/api/dashboard/stats')
      setStats(response.data)
    } catch (error) {
      console.error('Error fetching stats:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="flex items-center justify-center h-64">Loading...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <Link to="/app/products" className="btn-primary">
          Track New Product
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Products Tracked</p>
              <p className="text-3xl font-bold mt-1">{stats?.total_products || 0}</p>
            </div>
            <ShoppingBagIcon className="w-12 h-12 text-primary-600" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Active Alerts</p>
              <p className="text-3xl font-bold mt-1">{stats?.active_alerts || 0}</p>
            </div>
            <BellIcon className="w-12 h-12 text-yellow-600" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Price Drops Today</p>
              <p className="text-3xl font-bold mt-1">{stats?.price_drops_today || 0}</p>
            </div>
            <ChartBarIcon className="w-12 h-12 text-green-600" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Savings This Month</p>
              <p className="text-3xl font-bold mt-1">₹{stats?.savings_this_month || 0}</p>
            </div>
            <CurrencyDollarIcon className="w-12 h-12 text-green-600" />
          </div>
        </div>
      </div>

      {/* Subscription Info */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">Current Plan</h3>
            <p className="text-gray-600">{stats?.subscription_plan}</p>
          </div>
          <Link to="/pricing" className="btn-secondary">
            Upgrade Plan
          </Link>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid md:grid-cols-2 gap-6">
        <Link to="/app/products" className="card hover:shadow-md transition-shadow">
          <h3 className="text-lg font-semibold mb-2">View All Products</h3>
          <p className="text-gray-600">See all your tracked products and their current prices</p>
        </Link>

        <Link to="/app/alerts" className="card hover:shadow-md transition-shadow">
          <h3 className="text-lg font-semibold mb-2">Recent Alerts</h3>
          <p className="text-gray-600">Check your latest price drop notifications</p>
        </Link>
      </div>
    </div>
  )
}
