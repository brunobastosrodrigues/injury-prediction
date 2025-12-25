import { usePipeline } from '../../context/PipelineContext'

function Header({ onMenuClick }) {
  const { currentDataset, currentSplit, activeJobs } = usePipeline()
  const runningJobs = Object.entries(activeJobs).filter(([, j]) => j.status === 'running')

  return (
    <header className="bg-slate-900 border-b border-slate-800 px-4 sm:px-6 py-3 sm:py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2 sm:space-x-4">
          {/* Mobile menu button */}
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 -ml-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          {currentDataset && (
            <div className="flex items-center px-2 sm:px-3 py-1 sm:py-1.5 rounded-lg bg-blue-500/10 border border-blue-500/20">
              <svg className="w-4 h-4 text-blue-400 mr-1 sm:mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
              </svg>
              <span className="hidden sm:inline text-xs text-slate-400 mr-2">Dataset</span>
              <span className="text-xs sm:text-sm font-medium text-blue-400 truncate max-w-[100px] sm:max-w-none">{currentDataset}</span>
            </div>
          )}
          {currentSplit && (
            <div className="hidden sm:flex items-center px-3 py-1.5 rounded-lg bg-green-500/10 border border-green-500/20">
              <svg className="w-4 h-4 text-green-400 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
              </svg>
              <span className="text-xs text-slate-400 mr-2">Split</span>
              <span className="text-sm font-medium text-green-400">{currentSplit}</span>
            </div>
          )}
          {!currentDataset && !currentSplit && (
            <div className="flex items-center text-slate-500 text-xs sm:text-sm">
              <svg className="w-4 h-4 mr-1 sm:mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="hidden sm:inline">No dataset selected</span>
              <span className="sm:hidden">No dataset</span>
            </div>
          )}
        </div>

        {runningJobs.length > 0 && (
          <div className="flex items-center space-x-2 sm:space-x-4">
            {runningJobs.slice(0, 1).map(([jobId, job]) => (
              <div
                key={jobId}
                className="flex items-center px-2 sm:px-3 py-1 sm:py-1.5 rounded-lg bg-purple-500/10 border border-purple-500/20"
              >
                <div className="relative mr-1 sm:mr-2 flex-shrink-0">
                  <div className="animate-spin h-3 w-3 border-2 border-purple-400 border-t-transparent rounded-full"></div>
                </div>
                <span className="hidden sm:inline text-sm text-slate-300">{job.description}</span>
                <div className="flex items-center">
                  <div className="w-12 sm:w-16 h-1.5 bg-slate-700 rounded-full overflow-hidden sm:ml-3">
                    <div
                      className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full transition-all duration-300"
                      style={{ width: `${job.progress}%` }}
                    />
                  </div>
                  <span className="ml-1 sm:ml-2 text-xs font-medium text-purple-400">{job.progress}%</span>
                </div>
              </div>
            ))}
            {runningJobs.length > 1 && (
              <span className="text-xs text-slate-400 hidden sm:inline">+{runningJobs.length - 1} more</span>
            )}
          </div>
        )}
      </div>
    </header>
  )
}

export default Header
