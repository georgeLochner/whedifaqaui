import { Link, useLocation } from 'react-router-dom'

const NAV_ITEMS = [
  { to: '/', label: 'Library', testId: 'nav-library' },
  { to: '/upload', label: 'Upload', testId: 'nav-upload' },
  { to: '/search', label: 'Search', testId: 'nav-search' },
  { to: '/workspace', label: 'Workspace', testId: 'nav-workspace' },
] as const

export default function Navigation() {
  const { pathname } = useLocation()

  return (
    <nav className="bg-white shadow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <span className="text-xl font-bold text-gray-900">
                Whedifaqaui
              </span>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              {NAV_ITEMS.map(({ to, label, testId }) => {
                const active =
                  to === '/'
                    ? pathname === '/' || pathname === '/library'
                    : pathname.startsWith(to)
                return (
                  <Link
                    key={to}
                    to={to}
                    data-testid={testId}
                    className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                      active
                        ? 'border-blue-500 text-gray-900'
                        : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    }`}
                  >
                    {label}
                  </Link>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}
