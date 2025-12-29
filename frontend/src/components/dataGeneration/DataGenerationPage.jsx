import { useState, useEffect, useCallback } from 'react'
import { usePipeline } from '../../context/PipelineContext'
import { dataApi } from '../../api'
import { usePolling } from '../../hooks/usePolling'
import Card from '../common/Card'
import ProgressBar from '../common/ProgressBar'
import StatusBadge from '../common/StatusBadge'

function DataGenerationPage() {
  const { datasets, refreshDatasets, setCurrentDataset, addJob, updateJob, removeJob } = usePipeline()

  // Form state
  const [config, setConfig] = useState({
    n_athletes: 100,
    simulation_year: 2024,
    random_seed: 42
  })

  // Job state
  const [currentJobId, setCurrentJobId] = useState(null)
  const [jobStatus, setJobStatus] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState(null)

  // Polling for job status
  const { data: statusData } = usePolling(
    useCallback(() => currentJobId ? dataApi.getStatus(currentJobId).then(r => r.data) : null, [currentJobId]),
    2000,
    !!currentJobId && jobStatus?.status === 'running'
  )

  useEffect(() => {
    if (statusData) {
      setJobStatus(statusData)
      updateJob(currentJobId, {
        progress: statusData.progress,
        status: statusData.status
      })

      if (statusData.status === 'completed' || statusData.status === 'failed') {
        refreshDatasets()
        if (statusData.status === 'completed' && statusData.result?.dataset_id) {
          setCurrentDataset(statusData.result.dataset_id)
        }
      }
    }
  }, [statusData, currentJobId, updateJob, refreshDatasets, setCurrentDataset])

  useEffect(() => {
    refreshDatasets()
  }, [refreshDatasets])

  const handleGenerate = async () => {
    setIsSubmitting(true)
    setSubmitError(null)
    // Show immediate feedback in the progress panel
    setJobStatus({ status: 'starting', progress: 0, current_step: 'Initializing generation...' })

    try {
      const response = await dataApi.generate(config)
      const jobId = response.data.job_id
      setCurrentJobId(jobId)
      setJobStatus({ status: 'running', progress: 0, current_step: 'Starting athlete simulation...' })
      addJob(jobId, 'data_generation', `Generating ${config.n_athletes} athletes`)
    } catch (error) {
      console.error('Failed to start generation:', error)
      const errorMessage = error.response?.data?.error || error.message || 'Failed to start generation'
      setSubmitError(errorMessage)
      setJobStatus({ status: 'failed', progress: 0, error: errorMessage })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleCancel = async () => {
    if (currentJobId) {
      try {
        await dataApi.cancelGeneration(currentJobId)
        setJobStatus(prev => ({ ...prev, status: 'cancelled' }))
        removeJob(currentJobId)
      } catch (error) {
        console.error('Failed to cancel:', error)
      }
    }
  }

  const handleDelete = async (datasetId) => {
    if (confirm('Are you sure you want to delete this dataset?')) {
      try {
        await dataApi.deleteDataset(datasetId)
        refreshDatasets()
      } catch (error) {
        console.error('Failed to delete:', error)
      }
    }
  }

  const isRunning = jobStatus?.status === 'running' || jobStatus?.status === 'starting' || isSubmitting

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Data Generation</h1>
        <p className="text-slate-400 mt-2">Generate synthetic athlete training data for injury prediction</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Configuration */}
        <Card title="Configuration">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Number of Athletes
              </label>
              <input
                type="number"
                min="1"
                max="5000"
                value={config.n_athletes}
                onChange={e => setConfig(prev => ({ ...prev, n_athletes: parseInt(e.target.value) || 1 }))}
                disabled={isRunning}
                className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-slate-800/50 disabled:text-slate-500 transition-all"
              />
              <p className="text-xs text-slate-500 mt-1.5">Between 1 and 5000</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Simulation Year
              </label>
              <input
                type="number"
                min="2000"
                max="2030"
                value={config.simulation_year}
                onChange={e => setConfig(prev => ({ ...prev, simulation_year: parseInt(e.target.value) || 2024 }))}
                disabled={isRunning}
                className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-slate-800/50 disabled:text-slate-500 transition-all"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Random Seed
              </label>
              <input
                type="number"
                value={config.random_seed}
                onChange={e => setConfig(prev => ({ ...prev, random_seed: parseInt(e.target.value) || 42 }))}
                disabled={isRunning}
                className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-slate-800/50 disabled:text-slate-500 transition-all"
              />
              <p className="text-xs text-slate-500 mt-1.5">For reproducibility</p>
            </div>

            <div className="pt-4 flex space-x-3">
              <button
                onClick={handleGenerate}
                disabled={isRunning}
                className="flex-1 bg-gradient-to-r from-blue-600 to-blue-700 text-white py-2.5 px-4 rounded-xl hover:from-blue-500 hover:to-blue-600 disabled:from-slate-700 disabled:to-slate-700 disabled:text-slate-500 disabled:cursor-not-allowed transition-all font-medium shadow-lg shadow-blue-500/25 disabled:shadow-none flex items-center justify-center gap-2"
              >
                {(isSubmitting || isRunning) && (
                  <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                )}
                {isSubmitting ? 'Starting...' : isRunning ? 'Generating...' : 'Generate Dataset'}
              </button>
              {isRunning && (
                <button
                  onClick={handleCancel}
                  className="px-4 py-2.5 border border-red-500/50 text-red-400 rounded-xl hover:bg-red-500/10 transition-all font-medium"
                >
                  Cancel
                </button>
              )}
            </div>
          </div>
        </Card>

        {/* Progress */}
        <Card title="Generation Progress">
          {jobStatus ? (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="font-medium text-slate-300">Status</span>
                <StatusBadge status={jobStatus.status} />
              </div>

              <ProgressBar
                progress={jobStatus.progress}
                status={jobStatus.status}
                label="Progress"
              />

              {jobStatus.current_step && (
                <p className="text-sm text-slate-400">{jobStatus.current_step}</p>
              )}

              {jobStatus.data?.current_athlete && (
                <p className="text-sm text-slate-500">
                  Athlete {jobStatus.data.current_athlete} / {jobStatus.data.total_athletes}
                </p>
              )}

              {jobStatus.status === 'completed' && jobStatus.result?.dataset_id && (
                <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-xl">
                  <p className="text-green-400">
                    Dataset created: <code className="font-mono bg-green-500/20 px-2 py-0.5 rounded">{jobStatus.result.dataset_id}</code>
                  </p>
                </div>
              )}

              {jobStatus.status === 'failed' && (
                <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl space-y-3">
                  <p className="text-red-400">
                    <span className="font-medium">Error:</span> {jobStatus.error || 'Generation failed'}
                  </p>
                  <button
                    onClick={() => {
                      setJobStatus(null)
                      setSubmitError(null)
                      setCurrentJobId(null)
                    }}
                    className="text-sm text-red-400 hover:text-red-300 underline"
                  >
                    Try again
                  </button>
                </div>
              )}

              {(jobStatus.status === 'completed' || jobStatus.status === 'cancelled') && (
                <button
                  onClick={() => {
                    setJobStatus(null)
                    setCurrentJobId(null)
                  }}
                  className="w-full py-2 text-sm text-slate-400 hover:text-slate-300 border border-slate-700 rounded-lg hover:bg-slate-800 transition-colors"
                >
                  Start New Generation
                </button>
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
              </div>
              <p className="text-slate-500">Configure and start generation to see progress here</p>
            </div>
          )}
        </Card>
      </div>

      {/* Datasets List */}
      <Card title="Available Datasets">
        {datasets.length === 0 ? (
          <div className="text-center py-8">
            <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
              </svg>
            </div>
            <p className="text-slate-500">No datasets generated yet</p>
            <p className="text-slate-600 text-sm mt-1">Configure the parameters above and click Generate</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b border-slate-800">
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Dataset ID</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Athletes</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Year</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Injury Rate</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Created</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {datasets.map(dataset => (
                  <tr key={dataset.id} className="hover:bg-slate-800/50 transition-colors">
                    <td className="px-4 py-3 font-mono text-sm text-slate-300">{dataset.id}</td>
                    <td className="px-4 py-3 text-sm text-slate-300">{dataset.n_athletes}</td>
                    <td className="px-4 py-3 text-sm text-slate-300">{dataset.simulation_year}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className="px-2 py-1 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20 text-xs">
                        {dataset.injury_rate ? `${(dataset.injury_rate * 100).toFixed(2)}%` : 'N/A'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-500">
                      {dataset.created_at ? new Date(dataset.created_at).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="px-4 py-3 text-sm space-x-2">
                      <button
                        onClick={() => setCurrentDataset(dataset.id)}
                        className="text-blue-400 hover:text-blue-300 font-medium transition-colors"
                      >
                        Select
                      </button>
                      <button
                        onClick={() => handleDelete(dataset.id)}
                        className="text-red-400 hover:text-red-300 font-medium transition-colors"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}

export default DataGenerationPage
