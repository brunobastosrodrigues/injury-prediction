import { useState, useEffect, useCallback } from 'react'
import { usePipeline } from '../../context/PipelineContext'
import { trainingApi } from '../../api'
import { usePolling } from '../../hooks/usePolling'
import Card from '../common/Card'
import ProgressBar from '../common/ProgressBar'
import StatusBadge from '../common/StatusBadge'

const MODEL_CONFIGS = {
  lasso: {
    name: 'LASSO Logistic Regression',
    description: 'Linear model with L1 regularization for feature selection',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 6h16M4 12h16M4 18h7" />
      </svg>
    ),
    color: 'blue'
  },
  random_forest: {
    name: 'Random Forest',
    description: 'Ensemble of decision trees for robust predictions',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
      </svg>
    ),
    color: 'green'
  },
  xgboost: {
    name: 'XGBoost',
    description: 'Gradient boosting for high performance',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
      </svg>
    ),
    color: 'amber'
  }
}

const getColorClasses = (color, selected) => {
  const colors = {
    blue: selected ? 'border-blue-500/50 bg-blue-500/10' : 'border-slate-700 hover:border-blue-500/30',
    green: selected ? 'border-green-500/50 bg-green-500/10' : 'border-slate-700 hover:border-green-500/30',
    amber: selected ? 'border-amber-500/50 bg-amber-500/10' : 'border-slate-700 hover:border-amber-500/30'
  }
  return colors[color] || colors.blue
}

const getIconColorClass = (color) => {
  const colors = {
    blue: 'text-blue-400',
    green: 'text-green-400',
    amber: 'text-amber-400'
  }
  return colors[color] || 'text-blue-400'
}

function TrainingPage() {
  const {
    splits, models, currentSplit, setCurrentSplit,
    refreshSplits, refreshModels, addJob, updateJob
  } = usePipeline()

  const [selectedSplit, setSelectedSplit] = useState('')
  const [selectedModels, setSelectedModels] = useState(['random_forest'])
  const [currentJobId, setCurrentJobId] = useState(null)
  const [jobStatus, setJobStatus] = useState(null)

  const { data: statusData } = usePolling(
    useCallback(() => currentJobId ? trainingApi.getStatus(currentJobId).then(r => r.data) : null, [currentJobId]),
    2000,
    !!currentJobId && jobStatus?.status === 'running'
  )

  useEffect(() => {
    if (statusData) {
      setJobStatus(statusData)
      updateJob(currentJobId, { progress: statusData.progress, status: statusData.status })

      if (statusData.status === 'completed' || statusData.status === 'failed') {
        refreshModels()
      }
    }
  }, [statusData, currentJobId, updateJob, refreshModels])

  useEffect(() => {
    refreshSplits()
    refreshModels()
  }, [refreshSplits, refreshModels])

  useEffect(() => {
    if (currentSplit) {
      setSelectedSplit(currentSplit)
    }
  }, [currentSplit])

  const handleModelToggle = (modelType) => {
    setSelectedModels(prev =>
      prev.includes(modelType)
        ? prev.filter(m => m !== modelType)
        : [...prev, modelType]
    )
  }

  const handleTrain = async () => {
    if (!selectedSplit) {
      alert('Please select a split first')
      return
    }
    if (selectedModels.length === 0) {
      alert('Please select at least one model')
      return
    }

    try {
      const response = await trainingApi.train({
        split_id: selectedSplit,
        models: selectedModels
      })
      const jobId = response.data.job_id
      setCurrentJobId(jobId)
      setJobStatus({ status: 'running', progress: 0 })
      addJob(jobId, 'training', `Training ${selectedModels.length} model(s)`)
    } catch (error) {
      console.error('Failed to start training:', error)
    }
  }

  const isRunning = jobStatus?.status === 'running'

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Model Training</h1>
        <p className="text-slate-400 mt-2">Train ML models for injury prediction</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Configuration */}
        <Card title="Configuration">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Select Split
              </label>
              <select
                value={selectedSplit}
                onChange={e => {
                  setSelectedSplit(e.target.value)
                  setCurrentSplit(e.target.value)
                }}
                disabled={isRunning}
                className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-white focus:ring-2 focus:ring-blue-500 disabled:bg-slate-800/50 disabled:text-slate-500 transition-all"
              >
                <option value="">Select a split...</option>
                {splits.map(split => (
                  <option key={split.id} value={split.id}>
                    {split.id} ({split.split_strategy})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Select Models
              </label>
              <div className="space-y-2">
                {Object.entries(MODEL_CONFIGS).map(([key, config]) => (
                  <label
                    key={key}
                    className={`flex items-start p-4 border rounded-xl cursor-pointer transition-all ${getColorClasses(config.color, selectedModels.includes(key))}`}
                  >
                    <input
                      type="checkbox"
                      checked={selectedModels.includes(key)}
                      onChange={() => handleModelToggle(key)}
                      disabled={isRunning}
                      className="mt-1 mr-3 accent-blue-500"
                    />
                    <div className={`mr-3 ${getIconColorClass(config.color)}`}>
                      {config.icon}
                    </div>
                    <div>
                      <p className="font-medium text-white">{config.name}</p>
                      <p className="text-sm text-slate-500">{config.description}</p>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            <button
              onClick={handleTrain}
              disabled={isRunning || !selectedSplit || selectedModels.length === 0}
              className="w-full bg-gradient-to-r from-green-600 to-green-700 text-white py-2.5 px-4 rounded-xl hover:from-green-500 hover:to-green-600 disabled:from-slate-700 disabled:to-slate-700 disabled:text-slate-500 disabled:cursor-not-allowed transition-all font-medium shadow-lg shadow-green-500/25 disabled:shadow-none"
            >
              {isRunning ? 'Training...' : `Train ${selectedModels.length} Model(s)`}
            </button>
          </div>
        </Card>

        {/* Progress */}
        <Card title="Training Progress">
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

              {jobStatus.status === 'completed' && jobStatus.result?.models && (
                <div className="space-y-2">
                  <p className="font-medium text-green-400">Training Complete!</p>
                  {jobStatus.result.models.map(model => (
                    <div key={model.model_id} className="p-3 bg-green-500/10 border border-green-500/20 rounded-xl">
                      <p className="font-mono text-sm text-green-400">{model.model_type}</p>
                      <p className="text-sm text-slate-400 mt-1">
                        AUC: <span className="text-white">{model.metrics?.roc_auc?.toFixed(4)}</span> |
                        AP: <span className="text-white">{model.metrics?.average_precision?.toFixed(4)}</span>
                      </p>
                    </div>
                  ))}
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
              <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
                </svg>
              </div>
              <p className="text-slate-500">Configure and start training to see progress</p>
            </div>
          )}
        </Card>
      </div>

      {/* Models List */}
      <Card title="Trained Models">
        {models.length === 0 ? (
          <div className="text-center py-8">
            <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3" />
              </svg>
            </div>
            <p className="text-slate-500">No models trained yet</p>
            <p className="text-slate-600 text-sm mt-1">Select a split and train some models</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b border-slate-800">
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Model</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Dataset</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">ROC AUC</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Avg Precision</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {models.map(model => (
                  <tr key={model.id} className="hover:bg-slate-800/50 transition-colors">
                    <td className="px-4 py-3 font-mono text-sm text-slate-300">{model.id}</td>
                    <td className="px-4 py-3 text-sm text-slate-500 truncate max-w-[150px]" title={model.dataset_id}>
                      {model.dataset_id || 'N/A'}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <span className="px-2 py-1 rounded-lg bg-green-500/10 text-green-400 border border-green-500/20 text-xs">
                        {model.model_name || model.model_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm font-medium text-white">
                      {model.metrics?.roc_auc?.toFixed(4) || 'N/A'}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-300">
                      {model.metrics?.average_precision?.toFixed(4) || 'N/A'}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-500">
                      {model.created_at ? new Date(model.created_at).toLocaleDateString() : 'N/A'}
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

export default TrainingPage
