import { NavLink } from 'react-router-dom'
import { usePipeline } from '../../context/PipelineContext'

const navItems = [
  { path: '/', label: 'Dashboard', icon: '📊' },
  { path: '/data-generation', label: 'Data Generation', icon: '🔄' },
  { path: '/preprocessing', label: 'Preprocessing', icon: '⚙️' },
  { path: '/training', label: 'Training', icon: '🤖' },
  { path: '/results', label: 'Results', icon: '📈' },
  { path: '/analytics', label: 'Analytics', icon: '🔬' }
]

function Sidebar() {
  const { activeJobs } = usePipeline()
  const runningJobsCount = Object.values(activeJobs).filter(j => j.status === 'running').length

  return (
    <aside className="w-64 bg-gray-800 text-white">
      <div className="p-4 border-b border-gray-700">
        <h1 className="text-xl font-bold">Injury Prediction</h1>
        <p className="text-sm text-gray-400">ML Pipeline</p>
      </div>

      <nav className="p-4">
        <ul className="space-y-2">
          {navItems.map(item => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center px-4 py-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-300 hover:bg-gray-700'
                  }`
                }
              >
                <span className="mr-3">{item.icon}</span>
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {runningJobsCount > 0 && (
        <div className="absolute bottom-4 left-4 right-4 mx-4 p-3 bg-blue-600 rounded-lg">
          <div className="flex items-center">
            <div className="animate-spin mr-2 h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
            <span className="text-sm">{runningJobsCount} job(s) running</span>
          </div>
        </div>
      )}
    </aside>
  )
}

export default Sidebar
