import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { usePipeline } from '../../context/PipelineContext'
import Card from '../common/Card'
import StatusBadge from '../common/StatusBadge'

function Dashboard() {
  const {
    datasets, splits, models,
    refreshDatasets, refreshSplits, refreshModels,
    loading, activeJobs
  } = usePipeline()

  useEffect(() => {
    refreshDatasets()
    refreshSplits()
    refreshModels()
  }, [refreshDatasets, refreshSplits, refreshModels])

  const pipelineSteps = [
    {
      title: 'Data Generation',
      description: 'Generate synthetic athlete data',
      path: '/data-generation',
      count: datasets.length,
      countLabel: 'datasets',
      status: datasets.length > 0 ? 'completed' : 'pending'
    },
    {
      title: 'Preprocessing',
      description: 'Engineer features and split data',
      path: '/preprocessing',
      count: splits.length,
      countLabel: 'splits',
      status: splits.length > 0 ? 'completed' : datasets.length > 0 ? 'pending' : 'pending'
    },
    {
      title: 'Training',
      description: 'Train ML models',
      path: '/training',
      count: models.length,
      countLabel: 'models',
      status: models.length > 0 ? 'completed' : splits.length > 0 ? 'pending' : 'pending'
    },
    {
      title: 'Results & Analytics',
      description: 'View model performance',
      path: '/results',
      count: models.length,
      countLabel: 'models to compare',
      status: models.length > 0 ? 'completed' : 'pending'
    }
  ]

  const runningJobs = Object.entries(activeJobs).filter(([, j]) => j.status === 'running')

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">
          Injury Prediction ML Pipeline - Configure, train, and analyze models
        </p>
      </div>

      {/* Running Jobs */}
      {runningJobs.length > 0 && (
        <Card title="Active Jobs">
          <div className="space-y-3">
            {runningJobs.map(([jobId, job]) => (
              <div key={jobId} className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                <div className="flex items-center">
                  <div className="animate-spin mr-3 h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                  <div>
                    <p className="font-medium">{job.description}</p>
                    <p className="text-sm text-gray-500">Job ID: {jobId}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-blue-600">{job.progress}%</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Pipeline Steps */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {pipelineSteps.map((step, index) => (
          <Link key={step.path} to={step.path}>
            <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full">
              <div className="flex items-start justify-between">
                <div className="flex items-center justify-center w-10 h-10 bg-blue-100 text-blue-600 rounded-full font-bold">
                  {index + 1}
                </div>
                <StatusBadge status={step.status} />
              </div>
              <h3 className="mt-4 text-lg font-semibold">{step.title}</h3>
              <p className="text-sm text-gray-500 mt-1">{step.description}</p>
              <div className="mt-4 pt-4 border-t">
                <span className="text-2xl font-bold text-gray-900">{step.count}</span>
                <span className="text-sm text-gray-500 ml-2">{step.countLabel}</span>
              </div>
            </Card>
          </Link>
        ))}
      </div>

      {/* Recent Items */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Datasets */}
        <Card title="Recent Datasets">
          {loading.datasets ? (
            <p className="text-gray-500">Loading...</p>
          ) : datasets.length === 0 ? (
            <p className="text-gray-500">No datasets yet. Generate some data to get started.</p>
          ) : (
            <ul className="space-y-2">
              {datasets.slice(0, 5).map(ds => (
                <li key={ds.id} className="flex justify-between items-center p-2 hover:bg-gray-50 rounded">
                  <span className="font-mono text-sm truncate">{ds.id}</span>
                  <span className="text-sm text-gray-500">{ds.n_athletes} athletes</span>
                </li>
              ))}
            </ul>
          )}
        </Card>

        {/* Recent Splits */}
        <Card title="Recent Splits">
          {loading.splits ? (
            <p className="text-gray-500">Loading...</p>
          ) : splits.length === 0 ? (
            <p className="text-gray-500">No splits yet. Preprocess a dataset first.</p>
          ) : (
            <ul className="space-y-2">
              {splits.slice(0, 5).map(split => (
                <li key={split.id} className="flex justify-between items-center p-2 hover:bg-gray-50 rounded">
                  <span className="font-mono text-sm truncate">{split.id}</span>
                  <span className="text-sm text-gray-500">{split.split_strategy}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>

        {/* Recent Models */}
        <Card title="Recent Models">
          {loading.models ? (
            <p className="text-gray-500">Loading...</p>
          ) : models.length === 0 ? (
            <p className="text-gray-500">No models yet. Train some models first.</p>
          ) : (
            <ul className="space-y-2">
              {models.slice(0, 5).map(model => (
                <li key={model.id} className="flex justify-between items-center p-2 hover:bg-gray-50 rounded">
                  <span className="font-mono text-sm truncate">{model.model_type}</span>
                  <span className="text-sm text-gray-500">
                    AUC: {model.metrics?.roc_auc?.toFixed(3) || 'N/A'}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  )
}

export default Dashboard
