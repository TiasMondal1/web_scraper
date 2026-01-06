import { Link } from 'react-router-dom'
import { ChartBarIcon, BellIcon, ShoppingCartIcon, CurrencyDollarIcon } from '@heroicons/react/24/outline'

export default function Landing() {
  const features = [
    {
      icon: ChartBarIcon,
      title: 'Price History Tracking',
      description: 'See complete price history and trends for any product across platforms'
    },
    {
      icon: BellIcon,
      title: 'Instant Alerts',
      description: 'Get notified immediately when prices drop below your target'
    },
    {
      icon: ShoppingCartIcon,
      title: 'Multi-Platform Support',
      description: 'Track prices from Amazon, Flipkart, and more marketplaces'
    },
    {
      icon: CurrencyDollarIcon,
      title: 'Save Money',
      description: 'Never miss a deal - save thousands on your purchases'
    }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-50 to-white">
      {/* Navigation */}
      <nav className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-primary-600">Price Tracker Pro</h1>
          <div className="space-x-4">
            <Link to="/pricing" className="text-gray-600 hover:text-gray-900">Pricing</Link>
            <Link to="/login" className="text-gray-600 hover:text-gray-900">Login</Link>
            <Link to="/register" className="btn-primary">Get Started</Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="container mx-auto px-6 py-20 text-center">
        <h2 className="text-5xl font-bold text-gray-900 mb-6">
          Track Prices, Get Alerts,<br />Save Money
        </h2>
        <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
          Stop overpaying! Track product prices across India's top e-commerce platforms 
          and get instant alerts when prices drop.
        </p>
        <Link to="/register" className="inline-block btn-primary text-lg px-8 py-3">
          Start Tracking Free →
        </Link>
        <p className="mt-4 text-gray-500">No credit card required • 3 products free forever</p>
      </div>

      {/* Features */}
      <div className="container mx-auto px-6 py-20">
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <div key={index} className="card text-center hover:shadow-md transition-shadow">
              <feature.icon className="w-12 h-12 mx-auto mb-4 text-primary-600" />
              <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
              <p className="text-gray-600">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* CTA */}
      <div className="container mx-auto px-6 py-20 text-center">
        <h3 className="text-3xl font-bold mb-6">Ready to start saving?</h3>
        <Link to="/register" className="inline-block btn-primary text-lg px-8 py-3">
          Create Free Account
        </Link>
      </div>
    </div>
  )
}
