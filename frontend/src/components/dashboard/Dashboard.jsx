import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { usePipeline } from '../../context/PipelineContext'
import Card from '../common/Card'

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

  // Calculate study progress
  const studyProgress = {
    hasData: datasets.length > 0,
    hasFeatures: splits.length > 0,
    hasModels: models.length > 0,
    bestModel: models.length > 0
      ? models.reduce((best, m) =>
          (m.metrics?.roc_auc || 0) > (best.metrics?.roc_auc || 0) ? m : best
        , models[0])
      : null
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500/20 text-green-400 border-green-500/30'
      case 'ready':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30'
      default:
        return 'bg-slate-700/50 text-slate-500 border-slate-600/30'
    }
  }

  const getStatusLabel = (status) => {
    switch (status) {
      case 'completed':
        return 'Completed'
      case 'ready':
        return 'Ready'
      default:
        return 'Pending'
    }
  }

  const runningJobs = Object.entries(activeJobs).filter(([, j]) => j.status === 'running')

  return (
    <div className="space-y-8">
      {/* Research Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900 to-blue-900/20 border border-slate-800">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2">Study Overview</h1>
            <p className="text-slate-400 max-w-2xl">
              Prospective injury risk prediction in triathletes using training load biomarkers and machine learning.
            </p>
          </div>
          <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-full bg-slate-800 border border-slate-700">
            <div className={`w-2 h-2 rounded-full ${studyProgress.hasModels ? 'bg-green-400' : studyProgress.hasData ? 'bg-amber-400' : 'bg-slate-500'}`} />
            <span className="text-xs text-slate-400">
              {studyProgress.hasModels ? 'Models Trained' : studyProgress.hasFeatures ? 'Ready for Training' : studyProgress.hasData ? 'Data Available' : 'Setup Required'}
            </span>
          </div>
        </div>

        {/* Research Question */}
        <div className="mt-6 p-4 rounded-xl bg-slate-800/50 border border-slate-700/50">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center flex-shrink-0">
              <svg className="w-4 h-4 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-300 mb-1">Research Question</h3>
              <p className="text-sm text-slate-400">
                Can we predict injury risk within a 7-day window using training load metrics (ACWR, CTL/ATL, TSB)
                and physiological biomarkers (HRV, sleep quality, body battery)?
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Running Jobs */}
      {runningJobs.length > 0 && (
        <div className="p-4 rounded-2xl bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20">
          <div className="flex items-center mb-4">
            <div className="relative mr-3">
              <div className="animate-spin h-5 w-5 border-2 border-blue-400 border-t-transparent rounded-full"></div>
            </div>
            <h3 className="text-lg font-semibold text-white">Active Jobs</h3>
          </div>
          <div className="space-y-3">
            {runningJobs.map(([jobId, job]) => (
              <div key={jobId} className="flex items-center justify-between p-4 bg-slate-900/50 rounded-xl border border-slate-800">
                <div>
                  <p className="font-medium text-white">{job.description}</p>
                  <p className="text-sm text-slate-500 font-mono">ID: {jobId}</p>
                </div>
                <div className="flex items-center">
                  <div className="w-32 h-2 bg-slate-800 rounded-full overflow-hidden mr-3">
                    <div
                      className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full transition-all duration-300"
                      style={{ width: `${job.progress}%` }}
                    />
                  </div>
                  <span className="text-lg font-bold text-blue-400">{job.progress}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Key Findings (when models exist) */}
      {studyProgress.bestModel && (
        <div className="p-6 rounded-2xl bg-gradient-to-r from-green-500/5 to-emerald-500/5 border border-green-500/20">
          <div className="flex items-center gap-2 mb-4">
            <svg className="w-5 h-5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h2 className="text-lg font-semibold text-white">Key Findings</h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800">
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Best Model</p>
              <p className="text-lg font-semibold text-white capitalize">{studyProgress.bestModel.model_type?.replace('_', ' ')}</p>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800">
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">ROC-AUC</p>
              <p className="text-lg font-semibold text-green-400">{studyProgress.bestModel.metrics?.roc_auc?.toFixed(3) || 'N/A'}</p>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800">
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">PR-AUC</p>
              <p className="text-lg font-semibold text-blue-400">{studyProgress.bestModel.metrics?.average_precision?.toFixed(3) || 'N/A'}</p>
            </div>
          </div>
          <div className="mt-4 flex gap-3">
            <Link to="/results" className="text-sm text-green-400 hover:text-green-300 flex items-center">
              View detailed results
              <svg className="w-4 h-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
            <Link to="/interpretability" className="text-sm text-blue-400 hover:text-blue-300 flex items-center">
              Explore feature attribution
              <svg className="w-4 h-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>
        </div>
      )}

      {/* Scientific Workflow */}
      <div>
        <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4">Scientific Workflow</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

          {/* Study Design Section */}
          <div className="p-5 rounded-2xl bg-slate-900/50 border border-slate-800">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center">
                <svg className="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
              </div>
              <div>
                <h3 className="text-base font-semibold text-white">Study Design</h3>
                <p className="text-xs text-slate-500">Data collection & validation</p>
              </div>
            </div>
            <div className="space-y-2">
              <Link to="/data-generation" className="flex items-center justify-between p-3 rounded-xl hover:bg-slate-800/50 transition-colors group">
                <div className="flex items-center gap-3">
                  <span className="text-base">🧬</span>
                  <span className="text-sm text-slate-300 group-hover:text-white">Synthetic Cohort</span>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full border ${getStatusColor(datasets.length > 0 ? 'completed' : 'pending')}`}>
                  {datasets.length} datasets
                </span>
              </Link>
              <Link to="/ingestion" className="flex items-center justify-between p-3 rounded-xl hover:bg-slate-800/50 transition-colors group">
                <div className="flex items-center gap-3">
                  <span className="text-base">📤</span>
                  <span className="text-sm text-slate-300 group-hover:text-white">Real Data</span>
                </div>
                <span className="text-xs text-slate-500">Optional</span>
              </Link>
              <Link to="/validation" className="flex items-center justify-between p-3 rounded-xl hover:bg-slate-800/50 transition-colors group">
                <div className="flex items-center gap-3">
                  <span className="text-base">✅</span>
                  <span className="text-sm text-slate-300 group-hover:text-white">Data Quality</span>
                </div>
                <span className="text-xs text-slate-500">Sim2Real</span>
              </Link>
            </div>
          </div>

          {/* Methods Section */}
          <div className="p-5 rounded-2xl bg-slate-900/50 border border-slate-800">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center">
                <svg className="w-5 h-5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <div>
                <h3 className="text-base font-semibold text-white">Methods</h3>
                <p className="text-xs text-slate-500">Feature engineering & modeling</p>
              </div>
            </div>
            <div className="space-y-2">
              <Link to="/preprocessing" className="flex items-center justify-between p-3 rounded-xl hover:bg-slate-800/50 transition-colors group">
                <div className="flex items-center gap-3">
                  <span className="text-base">⚙️</span>
                  <span className="text-sm text-slate-300 group-hover:text-white">Feature Engineering</span>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full border ${getStatusColor(splits.length > 0 ? 'completed' : datasets.length > 0 ? 'ready' : 'pending')}`}>
                  {splits.length} splits
                </span>
              </Link>
              <Link to="/training" className="flex items-center justify-between p-3 rounded-xl hover:bg-slate-800/50 transition-colors group">
                <div className="flex items-center gap-3">
                  <span className="text-base">🤖</span>
                  <span className="text-sm text-slate-300 group-hover:text-white">Model Development</span>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full border ${getStatusColor(models.length > 0 ? 'completed' : splits.length > 0 ? 'ready' : 'pending')}`}>
                  {models.length} models
                </span>
              </Link>
            </div>
          </div>

          {/* Results Section */}
          <div className="p-5 rounded-2xl bg-slate-900/50 border border-slate-800">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-green-500/10 flex items-center justify-center">
                <svg className="w-5 h-5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
                </svg>
              </div>
              <div>
                <h3 className="text-base font-semibold text-white">Results</h3>
                <p className="text-xs text-slate-500">Performance & interpretation</p>
              </div>
            </div>
            <div className="space-y-2">
              <Link to="/results" className="flex items-center justify-between p-3 rounded-xl hover:bg-slate-800/50 transition-colors group">
                <div className="flex items-center gap-3">
                  <span className="text-base">📈</span>
                  <span className="text-sm text-slate-300 group-hover:text-white">Model Performance</span>
                </div>
                <span className="text-xs text-slate-500">ROC, PR curves</span>
              </Link>
              <Link to="/interpretability" className="flex items-center justify-between p-3 rounded-xl hover:bg-slate-800/50 transition-colors group">
                <div className="flex items-center gap-3">
                  <span className="text-base">🔍</span>
                  <span className="text-sm text-slate-300 group-hover:text-white">Feature Attribution</span>
                </div>
                <span className="text-xs text-slate-500">SHAP values</span>
              </Link>
            </div>
          </div>

          {/* Analysis Section */}
          <div className="p-5 rounded-2xl bg-slate-900/50 border border-slate-800">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center">
                <svg className="w-5 h-5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
                </svg>
              </div>
              <div>
                <h3 className="text-base font-semibold text-white">Analysis</h3>
                <p className="text-xs text-slate-500">Population & individual insights</p>
              </div>
            </div>
            <div className="space-y-2">
              <Link to="/analytics" className="flex items-center justify-between p-3 rounded-xl hover:bg-slate-800/50 transition-colors group">
                <div className="flex items-center gap-3">
                  <span className="text-base">🔬</span>
                  <span className="text-sm text-slate-300 group-hover:text-white">Population Analytics</span>
                </div>
                <span className="text-xs text-slate-500">Distributions, correlations</span>
              </Link>
              <Link to="/athletes" className="flex items-center justify-between p-3 rounded-xl hover:bg-slate-800/50 transition-colors group">
                <div className="flex items-center gap-3">
                  <span className="text-base">🏃</span>
                  <span className="text-sm text-slate-300 group-hover:text-white">Individual Profiles</span>
                </div>
                <span className="text-xs text-slate-500">Risk assessment</span>
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div>
        <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4">Study Assets</h2>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Datasets */}
          <Card title="Synthetic Cohorts">
            {loading.datasets ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin h-6 w-6 border-2 border-blue-400 border-t-transparent rounded-full"></div>
              </div>
            ) : datasets.length === 0 ? (
              <div className="text-center py-8">
                <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center mx-auto mb-3">
                  <svg className="w-6 h-6 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
                  </svg>
                </div>
                <p className="text-slate-500 text-sm">No cohorts generated</p>
                <Link to="/data-generation" className="text-blue-400 text-sm hover:text-blue-300 mt-1 inline-block">
                  Generate cohort
                </Link>
              </div>
            ) : (
              <ul className="space-y-2">
                {datasets.slice(0, 5).map(ds => (
                  <li key={ds.id} className="flex justify-between items-center p-3 hover:bg-slate-800/50 rounded-xl transition-colors">
                    <span className="font-mono text-sm text-slate-300 truncate">{ds.id}</span>
                    <span className="text-sm text-slate-500 flex items-center">
                      <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                      {ds.n_athletes}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </Card>

          {/* Feature Sets */}
          <Card title="Feature Sets">
            {loading.splits ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin h-6 w-6 border-2 border-purple-400 border-t-transparent rounded-full"></div>
              </div>
            ) : splits.length === 0 ? (
              <div className="text-center py-8">
                <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center mx-auto mb-3">
                  <svg className="w-6 h-6 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                  </svg>
                </div>
                <p className="text-slate-500 text-sm">No feature sets</p>
                <Link to="/preprocessing" className="text-purple-400 text-sm hover:text-purple-300 mt-1 inline-block">
                  Engineer features
                </Link>
              </div>
            ) : (
              <ul className="space-y-2">
                {splits.slice(0, 5).map(split => (
                  <li key={split.id} className="flex justify-between items-center p-3 hover:bg-slate-800/50 rounded-xl transition-colors">
                    <span className="font-mono text-sm text-slate-300 truncate">{split.id}</span>
                    <span className="text-xs px-2 py-1 rounded-full bg-purple-500/20 text-purple-400 border border-purple-500/30">
                      {split.split_strategy}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </Card>

          {/* Trained Models */}
          <Card title="Trained Models">
            {loading.models ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin h-6 w-6 border-2 border-green-400 border-t-transparent rounded-full"></div>
              </div>
            ) : models.length === 0 ? (
              <div className="text-center py-8">
                <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center mx-auto mb-3">
                  <svg className="w-6 h-6 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3" />
                  </svg>
                </div>
                <p className="text-slate-500 text-sm">No models trained</p>
                <Link to="/training" className="text-green-400 text-sm hover:text-green-300 mt-1 inline-block">
                  Train models
                </Link>
              </div>
            ) : (
              <ul className="space-y-2">
                {models.slice(0, 5).map(model => (
                  <li key={model.id} className="flex justify-between items-center p-3 hover:bg-slate-800/50 rounded-xl transition-colors">
                    <span className="font-medium text-sm text-slate-300 capitalize">{model.model_type?.replace('_', ' ')}</span>
                    <span className="text-sm font-mono text-green-400">
                      {model.metrics?.roc_auc?.toFixed(3) || 'N/A'}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 to-slate-800 border border-slate-800">
        <h2 className="text-lg font-semibold text-white mb-4">Quick Actions</h2>
        <div className="flex flex-wrap gap-3">
          <Link
            to="/data-generation"
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-500 transition-colors flex items-center"
          >
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            New Cohort
          </Link>
          <Link
            to="/athletes"
            className="px-4 py-2 text-sm font-medium text-slate-300 bg-slate-800 border border-slate-700 rounded-lg hover:bg-slate-700 hover:text-white transition-colors flex items-center"
          >
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            Individual Profiles
          </Link>
          <Link
            to="/analytics"
            className="px-4 py-2 text-sm font-medium text-slate-300 bg-slate-800 border border-slate-700 rounded-lg hover:bg-slate-700 hover:text-white transition-colors flex items-center"
          >
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            Population Analytics
          </Link>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
