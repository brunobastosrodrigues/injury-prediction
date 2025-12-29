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
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Preprocessing</h1>
        <p className="text-gray-600 dark:text-slate-400 mt-2">Feature engineering and train/test splitting</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Configuration */}
        <Card title="Configuration">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
                Select Dataset
              </label>
              <select
                value={config.dataset_id}
                onChange={e => {
                  setConfig(prev => ({ ...prev, dataset_id: e.target.value }))
                  setCurrentDataset(e.target.value)
                }}
                disabled={isRunning}
                className="w-full px-4 py-2.5 bg-gray-100 dark:bg-slate-800 border border-gray-300 dark:border-slate-700 rounded-xl text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 dark:bg-gray-100 dark:bg-slate-800/50 disabled:text-gray-500 dark:text-slate-500 transition-all"
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
              <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
                Split Strategy
              </label>
              <div className="space-y-2">
                <label className={`flex items-center p-3 rounded-xl cursor-pointer transition-all border ${
                  config.split_strategy === 'athlete_based'
                    ? 'border-blue-500/50 bg-blue-500/10'
                    : 'border-gray-300 dark:border-slate-700 hover:border-slate-600'
                }`}>
                  <input
                    type="radio"
                    name="split_strategy"
                    value="athlete_based"
                    checked={config.split_strategy === 'athlete_based'}
                    onChange={e => setConfig(prev => ({ ...prev, split_strategy: e.target.value }))}
                    disabled={isRunning}
                    className="mr-3 accent-blue-500"
                  />
                  <div>
                    <span className="text-sm text-gray-900 dark:text-white font-medium">Athlete-based</span>
                    <p className="text-xs text-gray-500 dark:text-slate-500">Generalize to new athletes</p>
                  </div>
                </label>
                <label className={`flex items-center p-3 rounded-xl cursor-pointer transition-all border ${
                  config.split_strategy === 'time_based'
                    ? 'border-blue-500/50 bg-blue-500/10'
                    : 'border-gray-300 dark:border-slate-700 hover:border-slate-600'
                }`}>
                  <input
                    type="radio"
                    name="split_strategy"
                    value="time_based"
                    checked={config.split_strategy === 'time_based'}
                    onChange={e => setConfig(prev => ({ ...prev, split_strategy: e.target.value }))}
                    disabled={isRunning}
                    className="mr-3 accent-blue-500"
                  />
                  <div>
                    <span className="text-sm text-gray-900 dark:text-white font-medium">Time-based</span>
                    <p className="text-xs text-gray-500 dark:text-slate-500">Predict future for known athletes</p>
                  </div>
                </label>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
                Test Split Ratio: <span className="text-blue-400">{(config.split_ratio * 100).toFixed(0)}%</span>
              </label>
              <input
                type="range"
                min="0.1"
                max="0.4"
                step="0.05"
                value={config.split_ratio}
                onChange={e => setConfig(prev => ({ ...prev, split_ratio: parseFloat(e.target.value) }))}
                disabled={isRunning}
                className="w-full accent-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
                Prediction Window (days)
              </label>
              <input
                type="number"
                min="1"
                max="30"
                value={config.prediction_window}
                onChange={e => setConfig(prev => ({ ...prev, prediction_window: parseInt(e.target.value) || 7 }))}
                disabled={isRunning}
                className="w-full px-4 py-2.5 bg-gray-100 dark:bg-slate-800 border border-gray-300 dark:border-slate-700 rounded-xl text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 dark:bg-gray-100 dark:bg-slate-800/50 disabled:text-gray-500 dark:text-slate-500 transition-all"
              />
              <p className="text-xs text-gray-500 dark:text-slate-500 mt-1.5">Predict injury within this many days</p>
            </div>

            <button
              onClick={handlePreprocess}
              disabled={isRunning || !config.dataset_id}
              className="w-full bg-gradient-to-r from-purple-600 to-purple-700 text-gray-900 dark:text-white py-2.5 px-4 rounded-xl hover:from-purple-500 hover:to-purple-600 disabled:from-slate-700 disabled:to-slate-700 disabled:text-gray-500 dark:text-slate-500 disabled:cursor-not-allowed transition-all font-medium shadow-lg shadow-purple-500/25 disabled:shadow-none"
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
                <span className="font-medium text-gray-700 dark:text-slate-300">Status</span>
                <StatusBadge status={jobStatus.status} />
              </div>

              <ProgressBar
                progress={jobStatus.progress}
                status={jobStatus.status}
                label="Progress"
              />

              {jobStatus.current_step && (
                <p className="text-sm text-gray-600 dark:text-slate-400">{jobStatus.current_step}</p>
              )}

              {jobStatus.status === 'completed' && jobStatus.result?.split_id && (
                <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-xl">
                  <p className="text-green-400">
                    Split created: <code className="font-mono bg-green-500/20 px-2 py-0.5 rounded">{jobStatus.result.split_id}</code>
                  </p>
                </div>
              )}

              {jobStatus.status === 'failed' && jobStatus.error && (
                <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl max-h-40 overflow-y-auto">
                  <p className="text-red-400 text-sm whitespace-pre-wrap">{jobStatus.error}</p>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="w-16 h-16 rounded-full bg-gray-100 dark:bg-slate-800 flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <p className="text-gray-500 dark:text-slate-500">Configure and run preprocessing to see progress</p>
            </div>
          )}
        </Card>
      </div>

      {/* Splits List */}
      <Card title="Available Splits">
        {splits.length === 0 ? (
          <div className="text-center py-8">
            <div className="w-16 h-16 rounded-full bg-gray-100 dark:bg-slate-800 flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
              </svg>
            </div>
            <p className="text-gray-500 dark:text-slate-500">No preprocessed splits yet</p>
            <p className="text-slate-600 text-sm mt-1">Select a dataset and run preprocessing</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b border-gray-200 dark:border-slate-800">
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 dark:text-slate-400 uppercase tracking-wider">Split ID</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 dark:text-slate-400 uppercase tracking-wider">Strategy</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 dark:text-slate-400 uppercase tracking-wider">Train Samples</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 dark:text-slate-400 uppercase tracking-wider">Test Samples</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 dark:text-slate-400 uppercase tracking-wider">Features</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 dark:text-slate-400 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {splits.map(split => (
                  <tr key={split.id} className="hover:bg-gray-100 dark:bg-gray-100 dark:bg-slate-800/50 transition-colors">
                    <td className="px-4 py-3 font-mono text-sm text-gray-700 dark:text-slate-300">{split.id}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className="px-2 py-1 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20 text-xs">
                        {split.split_strategy}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700 dark:text-slate-300">{split.train_samples?.toLocaleString()}</td>
                    <td className="px-4 py-3 text-sm text-gray-700 dark:text-slate-300">{split.test_samples?.toLocaleString()}</td>
                    <td className="px-4 py-3 text-sm text-gray-700 dark:text-slate-300">{split.n_features}</td>
                    <td className="px-4 py-3 text-sm">
                      <button
                        onClick={() => setCurrentSplit(split.id)}
                        className="text-blue-400 hover:text-blue-300 font-medium transition-colors"
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
