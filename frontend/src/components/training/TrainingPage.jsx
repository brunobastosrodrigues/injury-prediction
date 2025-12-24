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
    params: { max_iter: 1000 }
  },
  random_forest: {
    name: 'Random Forest',
    description: 'Ensemble of decision trees for robust predictions',
    params: { n_estimators: 200, max_depth: 8 }
  },
  xgboost: {
    name: 'XGBoost',
    description: 'Gradient boosting for high performance',
    params: { n_estimators: 400, max_depth: 2, learning_rate: 0.03 }
  }
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
        <h1 className="text-2xl font-bold text-gray-900">Model Training</h1>
        <p className="text-gray-600 mt-1">Train ML models for injury prediction</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Configuration */}
        <Card title="Configuration">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Select Split
              </label>
              <select
                value={selectedSplit}
                onChange={e => {
                  setSelectedSplit(e.target.value)
                  setCurrentSplit(e.target.value)
                }}
                disabled={isRunning}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
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
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Models
              </label>
              <div className="space-y-2">
                {Object.entries(MODEL_CONFIGS).map(([key, config]) => (
                  <label
                    key={key}
                    className={`flex items-start p-3 border rounded-lg cursor-pointer transition-colors ${
                      selectedModels.includes(key)
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={selectedModels.includes(key)}
                      onChange={() => handleModelToggle(key)}
                      disabled={isRunning}
                      className="mt-1 mr-3"
                    />
                    <div>
                      <p className="font-medium">{config.name}</p>
                      <p className="text-sm text-gray-500">{config.description}</p>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            <button
              onClick={handleTrain}
              disabled={isRunning || !selectedSplit || selectedModels.length === 0}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
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

              {jobStatus.status === 'completed' && jobStatus.result?.models && (
                <div className="space-y-2">
                  <p className="font-medium text-green-800">Training Complete!</p>
                  {jobStatus.result.models.map(model => (
                    <div key={model.model_id} className="p-2 bg-green-50 rounded">
                      <p className="font-mono text-sm">{model.model_type}</p>
                      <p className="text-sm text-gray-600">
                        AUC: {model.metrics?.roc_auc?.toFixed(4)} |
                        AP: {model.metrics?.average_precision?.toFixed(4)}
                      </p>
                    </div>
                  ))}
                </div>
              )}

              {jobStatus.status === 'failed' && jobStatus.error && (
                <div className="p-3 bg-red-50 rounded-lg max-h-40 overflow-y-auto">
                  <p className="text-red-800 text-sm whitespace-pre-wrap">{jobStatus.error}</p>
                </div>
              )}
            </div>
          ) : (
            <p className="text-gray-500">Configure and start training to see progress.</p>
          )}
        </Card>
      </div>

      {/* Models List */}
      <Card title="Trained Models">
        {models.length === 0 ? (
          <p className="text-gray-500">No models trained yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Model</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Dataset</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">ROC AUC</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Avg Precision</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {models.map(model => (
                  <tr key={model.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-sm">{model.id}</td>
                    <td className="px-4 py-3 text-sm truncate max-w-[150px]" title={model.dataset_id}>
                      {model.dataset_id || 'N/A'}
                    </td>
                    <td className="px-4 py-3 text-sm">{model.model_name || model.model_type}</td>
                    <td className="px-4 py-3 text-sm font-medium">
                      {model.metrics?.roc_auc?.toFixed(4) || 'N/A'}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {model.metrics?.average_precision?.toFixed(4) || 'N/A'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
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
