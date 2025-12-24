import { useState, useEffect, useCallback } from 'react'
import { usePipeline } from '../../context/PipelineContext'
import { preprocessingApi } from '../../api'
import { usePolling } from '../../hooks/usePolling'
import Card from '../common/Card'
import ProgressBar from '../common/ProgressBar'
import StatusBadge from '../common/StatusBadge'

function PreprocessingPage() {
  const {
    datasets, splits, currentDataset, setCurrentDataset, setCurrentSplit,
    refreshDatasets, refreshSplits, addJob, updateJob
  } = usePipeline()

  // Form state
  const [config, setConfig] = useState({
    dataset_id: '',
    split_strategy: 'athlete_based',
    split_ratio: 0.2,
    prediction_window: 7,
    random_seed: 42
  })

  // Job state
  const [currentJobId, setCurrentJobId] = useState(null)
  const [jobStatus, setJobStatus] = useState(null)

  // Polling
  const { data: statusData } = usePolling(
    useCallback(() => currentJobId ? preprocessingApi.getStatus(currentJobId).then(r => r.data) : null, [currentJobId]),
    2000,
    !!currentJobId && jobStatus?.status === 'running'
  )

  useEffect(() => {
    if (statusData) {
      setJobStatus(statusData)
      updateJob(currentJobId, { progress: statusData.progress, status: statusData.status })

      if (statusData.status === 'completed' || statusData.status === 'failed') {
        refreshSplits()
        if (statusData.status === 'completed' && statusData.result?.split_id) {
          setCurrentSplit(statusData.result.split_id)
        }
      }
    }
  }, [statusData, currentJobId, updateJob, refreshSplits, setCurrentSplit])

  useEffect(() => {
    refreshDatasets()
    refreshSplits()
  }, [refreshDatasets, refreshSplits])

  useEffect(() => {
    if (currentDataset) {
      setConfig(prev => ({ ...prev, dataset_id: currentDataset }))
    }
  }, [currentDataset])

  const handlePreprocess = async () => {
    if (!config.dataset_id) {
      alert('Please select a dataset first')
      return
    }

    try {
      const response = await preprocessingApi.run(config)
      const jobId = response.data.job_id
      setCurrentJobId(jobId)
      setJobStatus({ status: 'running', progress: 0 })
      addJob(jobId, 'preprocessing', `Preprocessing ${config.dataset_id}`)
    } catch (error) {
      console.error('Failed to start preprocessing:', error)
    }
  }

  const isRunning = jobStatus?.status === 'running'

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Preprocessing</h1>
        <p className="text-gray-600 mt-1">Feature engineering and train/test splitting</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Configuration */}
        <Card title="Configuration">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Select Dataset
              </label>
              <select
                value={config.dataset_id}
                onChange={e => {
                  setConfig(prev => ({ ...prev, dataset_id: e.target.value }))
                  setCurrentDataset(e.target.value)
                }}
                disabled={isRunning}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              >
                <option value="">Select a dataset...</option>
                {datasets.map(ds => (
                  <option key={ds.id} value={ds.id}>
                    {ds.id} ({ds.n_athletes} athletes)
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Split Strategy
              </label>
              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="split_strategy"
                    value="athlete_based"
                    checked={config.split_strategy === 'athlete_based'}
                    onChange={e => setConfig(prev => ({ ...prev, split_strategy: e.target.value }))}
                    disabled={isRunning}
                    className="mr-2"
                  />
                  <span className="text-sm">Athlete-based (generalize to new athletes)</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="split_strategy"
                    value="time_based"
                    checked={config.split_strategy === 'time_based'}
                    onChange={e => setConfig(prev => ({ ...prev, split_strategy: e.target.value }))}
                    disabled={isRunning}
                    className="mr-2"
                  />
                  <span className="text-sm">Time-based (predict future for known athletes)</span>
                </label>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Test Split Ratio: {(config.split_ratio * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0.1"
                max="0.4"
                step="0.05"
                value={config.split_ratio}
                onChange={e => setConfig(prev => ({ ...prev, split_ratio: parseFloat(e.target.value) }))}
                disabled={isRunning}
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Prediction Window (days)
              </label>
              <input
                type="number"
                min="1"
                max="30"
                value={config.prediction_window}
                onChange={e => setConfig(prev => ({ ...prev, prediction_window: parseInt(e.target.value) || 7 }))}
                disabled={isRunning}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              />
              <p className="text-xs text-gray-500 mt-1">Predict injury within this many days</p>
            </div>

            <button
              onClick={handlePreprocess}
              disabled={isRunning || !config.dataset_id}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {isRunning ? 'Processing...' : 'Run Preprocessing'}
            </button>
          </div>
        </Card>

        {/* Progress */}
        <Card title="Preprocessing Progress">
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

              {jobStatus.status === 'completed' && jobStatus.result?.split_id && (
                <div className="p-3 bg-green-50 rounded-lg">
                  <p className="text-green-800">
                    Split created: <code className="font-mono">{jobStatus.result.split_id}</code>
                  </p>
                </div>
              )}

              {jobStatus.status === 'failed' && jobStatus.error && (
                <div className="p-3 bg-red-50 rounded-lg max-h-40 overflow-y-auto">
                  <p className="text-red-800 text-sm whitespace-pre-wrap">{jobStatus.error}</p>
                </div>
              )}
            </div>
          ) : (
            <p className="text-gray-500">Configure and run preprocessing to see progress.</p>
          )}
        </Card>
      </div>

      {/* Splits List */}
      <Card title="Available Splits">
        {splits.length === 0 ? (
          <p className="text-gray-500">No preprocessed splits yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Split ID</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Strategy</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Train Samples</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Test Samples</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Features</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {splits.map(split => (
                  <tr key={split.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-sm">{split.id}</td>
                    <td className="px-4 py-3 text-sm">{split.split_strategy}</td>
                    <td className="px-4 py-3 text-sm">{split.train_samples?.toLocaleString()}</td>
                    <td className="px-4 py-3 text-sm">{split.test_samples?.toLocaleString()}</td>
                    <td className="px-4 py-3 text-sm">{split.n_features}</td>
                    <td className="px-4 py-3 text-sm">
                      <button
                        onClick={() => setCurrentSplit(split.id)}
                        className="text-blue-600 hover:underline"
                      >
                        Select
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

export default PreprocessingPage
