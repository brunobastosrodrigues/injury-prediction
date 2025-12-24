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
    try {
      const response = await dataApi.generate(config)
      const jobId = response.data.job_id
      setCurrentJobId(jobId)
      setJobStatus({ status: 'running', progress: 0 })
      addJob(jobId, 'data_generation', `Generating ${config.n_athletes} athletes`)
    } catch (error) {
      console.error('Failed to start generation:', error)
      alert('Failed to start generation. Please check the console for details.')
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

  const isRunning = jobStatus?.status === 'running' || isSubmitting

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Data Generation</h1>
        <p className="text-gray-600 mt-1">Generate synthetic athlete training data</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Configuration */}
        <Card title="Configuration">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Number of Athletes
              </label>
              <input
                type="number"
                min="1"
                max="5000"
                value={config.n_athletes}
                onChange={e => setConfig(prev => ({ ...prev, n_athletes: parseInt(e.target.value) || 1 }))}
                disabled={isRunning}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
              />
              <p className="text-xs text-gray-500 mt-1">Between 1 and 5000</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Simulation Year
              </label>
              <input
                type="number"
                min="2000"
                max="2030"
                value={config.simulation_year}
                onChange={e => setConfig(prev => ({ ...prev, simulation_year: parseInt(e.target.value) || 2024 }))}
                disabled={isRunning}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Random Seed
              </label>
              <input
                type="number"
                value={config.random_seed}
                onChange={e => setConfig(prev => ({ ...prev, random_seed: parseInt(e.target.value) || 42 }))}
                disabled={isRunning}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
              />
              <p className="text-xs text-gray-500 mt-1">For reproducibility</p>
            </div>

            <div className="pt-4 flex space-x-3">
              <button
                onClick={handleGenerate}
                disabled={isRunning}
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {isSubmitting ? 'Starting...' : isRunning ? 'Generating...' : 'Generate Dataset'}
              </button>
              {isRunning && (
                <button
                  onClick={handleCancel}
                  className="px-4 py-2 border border-red-500 text-red-500 rounded-lg hover:bg-red-50"
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
                <span className="font-medium">Status</span>
                <StatusBadge status={jobStatus.status} />
              </div>

              <ProgressBar
                progress={jobStatus.progress}
                status={jobStatus.status}
                label="Progress"
              />

              {jobStatus.current_step && (
                <p className="text-sm text-gray-600">{jobStatus.current_step}</p>
              )}

              {jobStatus.data?.current_athlete && (
                <p className="text-sm text-gray-500">
                  Athlete {jobStatus.data.current_athlete} / {jobStatus.data.total_athletes}
                </p>
              )}

              {jobStatus.status === 'completed' && jobStatus.result?.dataset_id && (
                <div className="p-3 bg-green-50 rounded-lg">
                  <p className="text-green-800">
                    Dataset created: <code className="font-mono">{jobStatus.result.dataset_id}</code>
                  </p>
                </div>
              )}

              {jobStatus.status === 'failed' && jobStatus.error && (
                <div className="p-3 bg-red-50 rounded-lg">
                  <p className="text-red-800">Error: {jobStatus.error}</p>
                </div>
              )}
            </div>
          ) : (
            <p className="text-gray-500">Configure and start generation to see progress here.</p>
          )}
        </Card>
      </div>

      {/* Datasets List */}
      <Card title="Available Datasets">
        {datasets.length === 0 ? (
          <p className="text-gray-500">No datasets generated yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Dataset ID</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Athletes</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Year</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Injury Rate</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {datasets.map(dataset => (
                  <tr key={dataset.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-sm">{dataset.id}</td>
                    <td className="px-4 py-3 text-sm">{dataset.n_athletes}</td>
                    <td className="px-4 py-3 text-sm">{dataset.simulation_year}</td>
                    <td className="px-4 py-3 text-sm">
                      {dataset.injury_rate ? `${(dataset.injury_rate * 100).toFixed(2)}%` : 'N/A'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {dataset.created_at ? new Date(dataset.created_at).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="px-4 py-3 text-sm space-x-2">
                      <button
                        onClick={() => setCurrentDataset(dataset.id)}
                        className="text-blue-600 hover:underline"
                      >
                        Select
                      </button>
                      <button
                        onClick={() => handleDelete(dataset.id)}
                        className="text-red-600 hover:underline"
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
