import { usePipeline } from '../../context/PipelineContext'

function Header() {
  const { currentDataset, currentSplit, activeJobs } = usePipeline()
  const runningJobs = Object.entries(activeJobs).filter(([, j]) => j.status === 'running')

  return (
    <header className="bg-white shadow-sm border-b px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-6">
          {currentDataset && (
            <div className="flex items-center">
              <span className="text-sm text-gray-500 mr-2">Dataset:</span>
              <span className="text-sm font-medium bg-blue-100 text-blue-800 px-2 py-1 rounded">
                {currentDataset}
              </span>
            </div>
          )}
          {currentSplit && (
            <div className="flex items-center">
              <span className="text-sm text-gray-500 mr-2">Split:</span>
              <span className="text-sm font-medium bg-green-100 text-green-800 px-2 py-1 rounded">
                {currentSplit}
              </span>
            </div>
          )}
        </div>

        {runningJobs.length > 0 && (
          <div className="flex items-center space-x-4">
            {runningJobs.slice(0, 2).map(([jobId, job]) => (
              <div key={jobId} className="flex items-center text-sm">
                <div className="animate-pulse mr-2 h-2 w-2 bg-blue-500 rounded-full"></div>
                <span className="text-gray-600">{job.description}</span>
                <span className="ml-2 text-blue-600">{job.progress}%</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </header>
  )
}

export default Header
