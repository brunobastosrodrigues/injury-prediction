import { NavLink, Link } from 'react-router-dom'
import { usePipeline } from '../../context/PipelineContext'

const navItems = [
  { path: '/pipeline', label: 'Pipeline Overview', icon: '📊' },
  { path: '/data-generation', label: 'Data Generation', icon: '🔄' },
  { path: '/ingestion', label: 'Data Ingestion', icon: '📤' },
  { path: '/preprocessing', label: 'Preprocessing', icon: '⚙️' },
  { path: '/training', label: 'Training', icon: '🤖' },
  { path: '/results', label: 'Results', icon: '📈' },
  { path: '/analytics', label: 'Analytics', icon: '🔬' },
  { path: '/athletes', label: 'Athlete Dashboard', icon: '🏃' }
]

function Sidebar({ onClose }) {
  const { activeJobs } = usePipeline()
  const runningJobsCount = Object.values(activeJobs).filter(j => j.status === 'running').length

  return (
    <aside className="w-64 h-full bg-slate-900 text-white flex flex-col">
      {/* Logo / Brand */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <Link to="/" className="flex items-center space-x-3 group" onClick={onClose}>
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/20 group-hover:shadow-blue-500/40 transition-shadow flex-shrink-0">
            <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div className="min-w-0">
            <h1 className="text-lg font-bold bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent truncate">Injury Prediction</h1>
            <p className="text-xs text-slate-500">ML Pipeline</p>
          </div>
        </Link>

        {/* Close button for mobile */}
        <button
          onClick={onClose}
          className="lg:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 overflow-y-auto">
        <div className="mb-3">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Pipeline</span>
        </div>
        <ul className="space-y-1">
          {navItems.map(item => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                onClick={onClose}
                className={({ isActive }) =>
                  `flex items-center px-4 py-2.5 rounded-xl transition-all ${
                    isActive
                      ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg shadow-blue-500/25'
                      : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                  }`
                }
              >
                <span className="mr-3 text-lg">{item.icon}</span>
                <span className="text-sm font-medium">{item.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Running Jobs Indicator */}
      {runningJobsCount > 0 && (
        <div className="p-4 border-t border-slate-800">
          <div className="p-3 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl shadow-lg shadow-blue-500/25">
            <div className="flex items-center">
              <div className="relative mr-3 flex-shrink-0">
                <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full"></div>
                <div className="absolute inset-0 animate-ping h-5 w-5 border-2 border-white border-t-transparent rounded-full opacity-25"></div>
              </div>
              <div className="min-w-0">
                <span className="text-sm font-medium">{runningJobsCount} job{runningJobsCount > 1 ? 's' : ''} running</span>
                <p className="text-xs text-blue-200">Processing...</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Back to Landing */}
      <div className="p-4 border-t border-slate-800">
        <Link
          to="/"
          onClick={onClose}
          className="flex items-center px-4 py-2.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-all text-sm"
        >
          <svg className="w-5 h-5 mr-3 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
          Back to Home
        </Link>
      </div>
    </aside>
  )
}

export default Sidebar
