import { Link, useLocation } from 'react-router-dom'

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation()

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary-600 rounded flex items-center justify-center text-white font-bold text-sm">
            P
          </div>
          <span className="text-xl font-semibold text-gray-900">PiaxisCD</span>
        </Link>
        <nav className="flex gap-4">
          <Link
            to="/"
            className={`px-3 py-1.5 rounded text-sm font-medium ${
              location.pathname === '/' ? 'bg-primary-50 text-primary-700' : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Projects
          </Link>
          <Link
            to="/settings"
            className={`px-3 py-1.5 rounded text-sm font-medium ${
              location.pathname === '/settings' ? 'bg-primary-50 text-primary-700' : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Settings
          </Link>
        </nav>
      </header>
      <main className="flex-1 p-6">{children}</main>
    </div>
  )
}
