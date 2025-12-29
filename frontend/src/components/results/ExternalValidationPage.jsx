import { useState, useEffect, useRef, useCallback } from 'react'
import Plot from 'react-plotly.js'
import { usePipeline } from '../../context/PipelineContext'
import { dataApi, validationApi } from '../../api'
import Card from '../common/Card'
import ProgressBar from '../common/ProgressBar'
import ExportButton from '../common/ExportButton'

// Dark theme layout for Plotly (consistent with ResultsPage)
const darkLayout = {
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor: 'rgba(15,23,42,0.5)',
  font: { color: '#94a3b8', size: 11 },
  xaxis: { gridcolor: '#334155', zerolinecolor: '#475569', tickfont: { color: '#94a3b8' } },
  yaxis: { gridcolor: '#334155', zerolinecolor: '#475569', tickfont: { color: '#94a3b8' } },
  legend: { bgcolor: 'rgba(0,0,0,0)', font: { color: '#cbd5e1' } }
}

function ExternalValidationPage() {
  const { datasets, refreshDatasets } = usePipeline()
  const [selectedDataset, setSelectedDataset] = useState(null)
  const [cachedValidations, setCachedValidations] = useState([])
  const [validationResults, setValidationResults] = useState(null)
  const [activeJob, setActiveJob] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const pollingRef = useRef(null)

  // Plot refs for export
  const distributionPlotRef = useRef(null)
  const causalPlotRef = useRef(null)
  const riskLandscapePlotRef = useRef(null)

  // Load datasets and cached validations on mount
  useEffect(() => {
    const loadInitialData = async () => {
      setLoading(true)
      try {
        await refreshDatasets()
        const cachedRes = await validationApi.listCachedValidations()
        setCachedValidations(cachedRes.data.validations || [])
      } catch (err) {
        console.error('Failed to load initial data:', err)
      } finally {
        setLoading(false)
      }
    }
    loadInitialData()
  }, [refreshDatasets])

  // Polling for job status
  const pollJobStatus = useCallback(async (jobId) => {
    try {
      const res = await validationApi.getJobStatus(jobId)
      const job = res.data

      if (job.status === 'completed') {
        setActiveJob(null)
        // Load the cached results
        const resultsRes = await validationApi.getCachedResults(job.result?.dataset_id || selectedDataset)
        setValidationResults(resultsRes.data)
        // Refresh cached validations list
        const cachedRes = await validationApi.listCachedValidations()
        setCachedValidations(cachedRes.data.validations || [])
        if (pollingRef.current) {
          clearInterval(pollingRef.current)
          pollingRef.current = null
        }
      } else if (job.status === 'failed') {
        setActiveJob(null)
        setError(job.error || 'Validation failed')
        if (pollingRef.current) {
          clearInterval(pollingRef.current)
          pollingRef.current = null
        }
      } else {
        setActiveJob(job)
      }
    } catch (err) {
      console.error('Failed to poll job status:', err)
    }
  }, [selectedDataset])

  // Start polling when job is active
  useEffect(() => {
    if (activeJob && activeJob.status !== 'completed' && activeJob.status !== 'failed') {
      pollingRef.current = setInterval(() => {
        pollJobStatus(activeJob.id)
      }, 2000)
    }
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
      }
    }
  }, [activeJob?.id, pollJobStatus])

  // Handle dataset selection
  const handleSelectDataset = async (datasetId) => {
    setSelectedDataset(datasetId)
    setError(null)
    setValidationResults(null)
    setActiveJob(null)

    // Check if we have cached results
    try {
      const cachedRes = await validationApi.getCachedResults(datasetId)
      if (cachedRes.data && cachedRes.data.cached) {
        setValidationResults(cachedRes.data)
      }
    } catch (err) {
      // No cached results, that's fine
      if (err.response?.status !== 404) {
        console.error('Error checking cached results:', err)
      }
    }
  }

  // Start validation
  const handleRunValidation = async () => {
    if (!selectedDataset) return

    setError(null)
    try {
      const res = await validationApi.runValidation(selectedDataset)
      setActiveJob({
        id: res.data.job_id,
        status: 'pending',
        progress: 0,
        current_step: 'Starting validation...'
      })
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to start validation')
    }
  }

  // Recompute validation (delete cache and run again)
  const handleRecompute = async () => {
    if (!selectedDataset) return

    try {
      await validationApi.deleteCachedResults(selectedDataset)
      setValidationResults(null)
      handleRunValidation()
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to recompute')
    }
  }

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'methodology', label: 'Methodology' },
    { id: 'distributions', label: 'Distributions' },
    { id: 'sim2real', label: 'Sim2Real' },
    { id: 'causal', label: 'Causal Mechanism' },
    { id: 'pmdata', label: 'PMData Analysis' }
  ]

  // Methodology validation state
  const [methodologyResults, setMethodologyResults] = useState(null)
  const [methodologyJob, setMethodologyJob] = useState(null)
  const methodologyPollingRef = useRef(null)

  // Load methodology results when dataset changes
  useEffect(() => {
    if (selectedDataset) {
      loadMethodologyResults(selectedDataset)
    }
  }, [selectedDataset])

  const loadMethodologyResults = async (datasetId) => {
    try {
      const res = await validationApi.getMethodologySummary(datasetId)
      setMethodologyResults(res.data)
    } catch (err) {
      console.log('No methodology results cached yet')
      setMethodologyResults(null)
    }
  }

  const handleRunMethodology = async (types = ['loso', 'sensitivity', 'equivalence']) => {
    if (!selectedDataset) return
    try {
      const res = await validationApi.runMethodologyValidation(selectedDataset, types)
      setMethodologyJob({
        id: res.data.job_id,
        status: 'pending',
        progress: 0,
        current_step: 'Starting methodology validation...'
      })
      // Start polling
      methodologyPollingRef.current = setInterval(async () => {
        try {
          const statusRes = await validationApi.getJobStatus(res.data.job_id)
          const job = statusRes.data
          if (job.status === 'completed') {
            clearInterval(methodologyPollingRef.current)
            setMethodologyJob(null)
            loadMethodologyResults(selectedDataset)
          } else if (job.status === 'failed') {
            clearInterval(methodologyPollingRef.current)
            setMethodologyJob(null)
            setError(job.error || 'Methodology validation failed')
          } else {
            setMethodologyJob(job)
          }
        } catch (e) {
          console.error('Polling error:', e)
        }
      }, 2000)
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to start methodology validation')
    }
  }

  // Cleanup methodology polling
  useEffect(() => {
    return () => {
      if (methodologyPollingRef.current) {
        clearInterval(methodologyPollingRef.current)
      }
    }
  }, [])

  const getPillarColor = (status) => {
    if (status === 'pass') return 'bg-green-500/20 text-green-400 border-green-500/30'
    if (status === 'warning') return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
    return 'bg-red-500/20 text-red-400 border-red-500/30'
  }

  const getScoreColor = (score) => {
    if (score >= 0.7) return 'text-green-400'
    if (score >= 0.4) return 'text-yellow-400'
    return 'text-red-400'
  }

  const getStatusBadge = (status) => {
    if (status === 'PASS') return 'bg-green-500/20 text-green-400'
    if (status === 'WARNING') return 'bg-yellow-500/20 text-yellow-400'
    return 'bg-red-500/20 text-red-400'
  }

  // Check if dataset has cached validation
  const hasCachedValidation = (datasetId) => {
    return cachedValidations.some(v => v.dataset_id === datasetId)
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-white">External Validation</h1>
        <p className="text-sm sm:text-base text-slate-400 mt-1">
          Compare synthetic data against real PMData (Sim2Real Transfer)
        </p>
      </div>

      {/* Dataset Selection */}
      <Card title="Select Synthetic Dataset">
        {loading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
          </div>
        ) : datasets.length === 0 ? (
          <div className="text-center py-8">
            <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
              </svg>
            </div>
            <p className="text-slate-400">No synthetic datasets available</p>
            <p className="text-slate-500 text-sm mt-1">Generate a synthetic cohort first</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
            {datasets.map(ds => (
              <button
                key={ds.id}
                onClick={() => handleSelectDataset(ds.id)}
                className={`p-3 sm:p-4 border rounded-xl text-left transition-all ${
                  selectedDataset === ds.id
                    ? 'border-blue-500 bg-blue-500/10 ring-1 ring-blue-500/50'
                    : 'border-slate-700 bg-slate-800/50 hover:border-slate-600 hover:bg-slate-800'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-xs text-slate-400 truncate max-w-[180px]">{ds.id}</span>
                  {hasCachedValidation(ds.id) && (
                    <span className="text-xs px-2 py-0.5 bg-green-500/20 text-green-400 rounded">Cached</span>
                  )}
                </div>
                <div className="flex justify-between text-xs text-slate-500">
                  <span>{ds.n_athletes || '?'} athletes</span>
                  <span>{ds.created_at ? new Date(ds.created_at).toLocaleDateString() : ''}</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </Card>

      {/* Validation Actions */}
      {selectedDataset && !activeJob && (
        <Card>
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <p className="text-slate-300">
                Selected: <span className="font-mono text-blue-400">{selectedDataset}</span>
              </p>
              {validationResults && (
                <p className="text-xs text-slate-500 mt-1">
                  Last computed: {new Date(validationResults.summary?.computed_at).toLocaleString()}
                </p>
              )}
            </div>
            <div className="flex gap-3">
              {!validationResults ? (
                <button
                  onClick={handleRunValidation}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
                >
                  Run Validation
                </button>
              ) : (
                <button
                  onClick={handleRecompute}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Recompute
                </button>
              )}
            </div>
          </div>
        </Card>
      )}

      {/* Job Progress */}
      {activeJob && (
        <Card title="Running Validation">
          <div className="space-y-4">
            <ProgressBar progress={activeJob.progress || 0} />
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-400">{activeJob.current_step || 'Processing...'}</p>
              <span className="text-xs text-slate-500">{activeJob.progress || 0}%</span>
            </div>
          </div>
        </Card>
      )}

      {/* Error Display */}
      {error && (
        <Card>
          <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
            <p className="text-red-400">{error}</p>
          </div>
        </Card>
      )}

      {/* Validation Results */}
      {validationResults && !activeJob && (
        <>
          {/* Tab Navigation */}
          <div className="border-b border-slate-700 overflow-x-auto">
            <nav className="flex space-x-4 sm:space-x-8 min-w-max px-1">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-2 px-1 border-b-2 font-medium text-xs sm:text-sm whitespace-nowrap transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-400'
                      : 'border-transparent text-slate-400 hover:text-slate-300 hover:border-slate-600'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          {/* Overview Tab */}
          {activeTab === 'overview' && validationResults.three_pillars && (
            <div className="space-y-4">
              {/* Three Pillars Summary */}
              <Card title="Three Pillars of Validity">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  {/* Statistical Fidelity */}
                  <div className={`p-4 rounded-lg border ${getPillarColor(validationResults.three_pillars.pillars?.statistical_fidelity?.status)}`}>
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold text-slate-200">Statistical Fidelity</h4>
                      <span className="text-xs uppercase font-bold">
                        {validationResults.three_pillars.pillars?.statistical_fidelity?.status || 'pending'}
                      </span>
                    </div>
                    <p className="text-2xl font-bold mb-1">
                      {((validationResults.three_pillars.pillars?.statistical_fidelity?.score || 0) * 100).toFixed(0)}%
                    </p>
                    <p className="text-xs opacity-75">
                      JS Div: {validationResults.three_pillars.pillars?.statistical_fidelity?.avg_js_divergence?.toFixed(4) || 'N/A'}
                    </p>
                    <p className="text-xs mt-1 opacity-60">Target: JS &lt; 0.1</p>
                  </div>

                  {/* Causal Fidelity */}
                  <div className={`p-4 rounded-lg border ${getPillarColor(validationResults.three_pillars.pillars?.causal_fidelity?.status)}`}>
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold text-slate-200">Causal Fidelity</h4>
                      <span className="text-xs uppercase font-bold">
                        {validationResults.three_pillars.pillars?.causal_fidelity?.status || 'pending'}
                      </span>
                    </div>
                    <p className="text-2xl font-bold mb-1">
                      {validationResults.three_pillars.pillars?.causal_fidelity?.undertrained_risk_ratio?.toFixed(1) || '?'}x
                    </p>
                    <p className="text-xs opacity-75">Undertrained vs Optimal risk ratio</p>
                    <p className="text-xs mt-1 opacity-60">Target: 2-3x higher</p>
                  </div>

                  {/* Transferability */}
                  <div className={`p-4 rounded-lg border ${getPillarColor(validationResults.three_pillars.pillars?.transferability?.status)}`}>
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold text-slate-200">Transferability</h4>
                      <span className="text-xs uppercase font-bold">
                        {validationResults.three_pillars.pillars?.transferability?.status || 'pending'}
                      </span>
                    </div>
                    <p className="text-2xl font-bold mb-1">
                      {validationResults.three_pillars.pillars?.transferability?.sim2real_auc?.toFixed(3) || '?'}
                    </p>
                    <p className="text-xs opacity-75">Sim2Real AUC</p>
                    <p className="text-xs mt-1 opacity-60">Target: AUC &gt; 0.60</p>
                  </div>
                </div>

                {/* Overall Status */}
                <div className={`p-4 rounded-lg ${validationResults.three_pillars.ready_for_publication ? 'bg-green-500/10 border border-green-500/30' : 'bg-amber-500/10 border border-amber-500/30'}`}>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-slate-200">
                        {validationResults.three_pillars.ready_for_publication ? 'Ready for Publication' : 'Needs Improvement'}
                      </p>
                      <p className="text-sm opacity-75 text-slate-400">
                        {validationResults.three_pillars.pillars_passing} pillars passing
                      </p>
                    </div>
                    <span className={`text-3xl font-bold ${getScoreColor(validationResults.three_pillars.overall_score)}`}>
                      {(validationResults.three_pillars.overall_score * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </Card>

              {/* Quick Summary */}
              <Card title="Validation Summary">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  <div className="text-center p-4 bg-slate-800/50 rounded-lg">
                    <p className="text-2xl font-bold text-blue-400">
                      {validationResults.distributions?.synthetic_samples?.toLocaleString() || 'N/A'}
                    </p>
                    <p className="text-xs text-slate-500">Synthetic Samples</p>
                  </div>
                  <div className="text-center p-4 bg-slate-800/50 rounded-lg">
                    <p className="text-2xl font-bold text-purple-400">
                      {validationResults.distributions?.real_samples?.toLocaleString() || 'N/A'}
                    </p>
                    <p className="text-xs text-slate-500">Real PMData Samples</p>
                  </div>
                  <div className="text-center p-4 bg-slate-800/50 rounded-lg">
                    <p className="text-2xl font-bold text-green-400">
                      {validationResults.sim2real?.auc?.toFixed(4) || 'N/A'}
                    </p>
                    <p className="text-xs text-slate-500">Sim2Real AUC</p>
                  </div>
                  <div className="text-center p-4 bg-slate-800/50 rounded-lg">
                    <p className="text-2xl font-bold text-orange-400">
                      {validationResults.summary?.avg_js_divergence?.toFixed(4) || 'N/A'}
                    </p>
                    <p className="text-xs text-slate-500">Avg JS Divergence</p>
                  </div>
                </div>
              </Card>
            </div>
          )}

          {/* Methodology Tab - Publication-Quality Validation */}
          {activeTab === 'methodology' && (
            <div className="space-y-4">
              {/* Methodology Job Progress */}
              {methodologyJob && (
                <Card title="Running Methodology Validation">
                  <div className="space-y-4">
                    <ProgressBar progress={methodologyJob.progress || 0} />
                    <div className="flex items-center justify-between">
                      <p className="text-sm text-slate-400">{methodologyJob.current_step || 'Processing...'}</p>
                      <span className="text-xs text-slate-500">{methodologyJob.progress || 0}%</span>
                    </div>
                  </div>
                </Card>
              )}

              {/* Run Methodology Validation Button */}
              {!methodologyJob && (
                <Card title="Methodology Validation Suite">
                  <div className="p-4 bg-slate-800/50 rounded-lg mb-4">
                    <p className="text-sm text-slate-300 mb-2">
                      <strong>Publication-Quality Rigor:</strong> Run these validations to address common reviewer critiques.
                    </p>
                    <ul className="text-xs text-slate-400 space-y-1">
                      <li>• <strong>LOSO CV</strong>: Leave-One-Subject-Out cross-validation (N=16 folds)</li>
                      <li>• <strong>Sensitivity Analysis</strong>: Parameter perturbation study with Tornado Plot</li>
                      <li>• <strong>Equivalence Check</strong>: Rust vs Python numerical identity (MSE &lt; 1e-6)</li>
                    </ul>
                  </div>
                  <button
                    onClick={() => handleRunMethodology()}
                    className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors"
                  >
                    Run Full Methodology Suite
                  </button>
                </Card>
              )}

              {/* LOSO Cross-Validation Results */}
              {methodologyResults?.loso?.status === 'complete' && (
                <Card title="LOSO Cross-Validation Results">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
                    <div className="text-center p-4 bg-slate-800/50 rounded-lg">
                      <p className="text-2xl font-bold text-blue-400">
                        {methodologyResults.loso.mean_auc?.toFixed(3)}
                      </p>
                      <p className="text-xs text-slate-500">Mean AUC</p>
                    </div>
                    <div className="text-center p-4 bg-slate-800/50 rounded-lg">
                      <p className="text-2xl font-bold text-purple-400">
                        ±{methodologyResults.loso.std_auc?.toFixed(3)}
                      </p>
                      <p className="text-xs text-slate-500">Std Dev</p>
                    </div>
                    <div className="text-center p-4 bg-slate-800/50 rounded-lg">
                      <p className="text-2xl font-bold text-green-400">
                        {methodologyResults.loso.n_folds}
                      </p>
                      <p className="text-xs text-slate-500">Folds</p>
                    </div>
                    <div className="text-center p-4 bg-slate-800/50 rounded-lg">
                      <p className="text-lg font-bold text-orange-400">
                        [{methodologyResults.loso.confidence_interval_95?.[0]?.toFixed(2)}, {methodologyResults.loso.confidence_interval_95?.[1]?.toFixed(2)}]
                      </p>
                      <p className="text-xs text-slate-500">95% CI</p>
                    </div>
                  </div>

                  {/* Per-Fold Results Chart */}
                  {methodologyResults.loso.fold_results && (
                    <Plot
                      data={[{
                        x: methodologyResults.loso.fold_results.map(f => f.test_athlete),
                        y: methodologyResults.loso.fold_results.map(f => f.auc),
                        type: 'bar',
                        marker: {
                          color: methodologyResults.loso.fold_results.map(f =>
                            f.auc >= 0.6 ? '#22c55e' : f.auc >= 0.55 ? '#eab308' : '#ef4444'
                          )
                        },
                        text: methodologyResults.loso.fold_results.map(f => f.auc.toFixed(2)),
                        textposition: 'outside',
                        textfont: { size: 10, color: '#94a3b8' }
                      },
                      // Mean line
                      {
                        x: [methodologyResults.loso.fold_results[0]?.test_athlete, methodologyResults.loso.fold_results.slice(-1)[0]?.test_athlete],
                        y: [methodologyResults.loso.mean_auc, methodologyResults.loso.mean_auc],
                        type: 'scatter',
                        mode: 'lines',
                        name: `Mean: ${methodologyResults.loso.mean_auc?.toFixed(3)}`,
                        line: { color: '#3b82f6', width: 2, dash: 'dash' }
                      }]}
                      layout={{
                        ...darkLayout,
                        height: 300,
                        margin: { t: 40, r: 20, b: 60, l: 50 },
                        xaxis: { ...darkLayout.xaxis, title: 'Athlete (Held-Out)', tickangle: -45 },
                        yaxis: { ...darkLayout.yaxis, title: 'AUC', range: [0.3, 1] },
                        showlegend: true,
                        legend: { ...darkLayout.legend, orientation: 'h', y: 1.15, x: 0.5, xanchor: 'center' }
                      }}
                      config={{ displayModeBar: false, responsive: true }}
                      useResizeHandler
                      style={{ width: '100%' }}
                    />
                  )}

                  <div className={`p-4 rounded-lg mt-4 ${
                    methodologyResults.loso.confidence_interval_95?.[0] > 0.55
                      ? 'bg-green-500/10 border border-green-500/30'
                      : 'bg-yellow-500/10 border border-yellow-500/30'
                  }`}>
                    <p className="text-sm text-slate-300">{methodologyResults.loso.interpretation}</p>
                  </div>
                </Card>
              )}

              {/* Sensitivity Analysis Results */}
              {methodologyResults?.sensitivity?.status === 'complete' && (
                <Card title="Sensitivity Analysis (Tornado Plot)">
                  <div className="mb-4 p-3 bg-slate-800/50 rounded-lg">
                    <p className="text-sm text-slate-400">
                      <strong>Baseline Asymmetry Ratio:</strong>{' '}
                      {methodologyResults.sensitivity.baseline?.undertrained_vs_optimal?.toFixed(1)}x
                      (Undertrained / Optimal risk per load)
                    </p>
                  </div>

                  {/* Tornado Plot */}
                  {methodologyResults.sensitivity.tornado_data && (
                    <Plot
                      data={[
                        // Low impact (left bars)
                        {
                          y: methodologyResults.sensitivity.tornado_data.map(d => d.parameter.replace(/_/g, ' ')),
                          x: methodologyResults.sensitivity.tornado_data.map(d => d.low_impact),
                          type: 'bar',
                          orientation: 'h',
                          name: '-20%',
                          marker: { color: '#3b82f6' }
                        },
                        // High impact (right bars)
                        {
                          y: methodologyResults.sensitivity.tornado_data.map(d => d.parameter.replace(/_/g, ' ')),
                          x: methodologyResults.sensitivity.tornado_data.map(d => d.high_impact),
                          type: 'bar',
                          orientation: 'h',
                          name: '+20%',
                          marker: { color: '#ef4444' }
                        }
                      ]}
                      layout={{
                        ...darkLayout,
                        height: 350,
                        margin: { t: 40, r: 20, b: 50, l: 150 },
                        barmode: 'relative',
                        xaxis: { ...darkLayout.xaxis, title: 'Change in Asymmetry Ratio', zeroline: true, zerolinewidth: 2 },
                        yaxis: { ...darkLayout.yaxis, automargin: true },
                        showlegend: true,
                        legend: { ...darkLayout.legend, orientation: 'h', y: 1.1, x: 0.5, xanchor: 'center' }
                      }}
                      config={{ displayModeBar: false, responsive: true }}
                      useResizeHandler
                      style={{ width: '100%' }}
                    />
                  )}

                  <div className={`p-4 rounded-lg mt-4 ${
                    methodologyResults.sensitivity.robustness_assessment?.all_params_maintain_asymmetry
                      ? 'bg-green-500/10 border border-green-500/30'
                      : 'bg-yellow-500/10 border border-yellow-500/30'
                  }`}>
                    <p className="text-sm text-slate-300">
                      {methodologyResults.sensitivity.robustness_assessment?.conclusion}
                    </p>
                  </div>
                </Card>
              )}

              {/* Rust-Python Equivalence Check */}
              {methodologyResults?.equivalence?.status === 'complete' && (
                <Card title="Rust-Python Equivalence Check">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
                    <div className="text-center p-4 bg-slate-800/50 rounded-lg">
                      <p className={`text-2xl font-bold ${
                        methodologyResults.equivalence.is_equivalent ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {methodologyResults.equivalence.is_equivalent ? 'PASS' : 'FAIL'}
                      </p>
                      <p className="text-xs text-slate-500">Status</p>
                    </div>
                    <div className="text-center p-4 bg-slate-800/50 rounded-lg">
                      <p className="text-lg font-bold text-blue-400 font-mono">
                        {methodologyResults.equivalence.average_mse?.toExponential(2)}
                      </p>
                      <p className="text-xs text-slate-500">Average MSE</p>
                    </div>
                    <div className="text-center p-4 bg-slate-800/50 rounded-lg">
                      <p className="text-lg font-bold text-purple-400 font-mono">
                        {methodologyResults.equivalence.mse_threshold?.toExponential(0)}
                      </p>
                      <p className="text-xs text-slate-500">Threshold</p>
                    </div>
                    <div className="text-center p-4 bg-slate-800/50 rounded-lg">
                      <p className="text-lg font-bold text-orange-400">
                        {methodologyResults.equivalence.n_samples_compared?.toLocaleString()}
                      </p>
                      <p className="text-xs text-slate-500">Samples Compared</p>
                    </div>
                  </div>

                  {/* Per-Column Errors */}
                  {methodologyResults.equivalence.column_errors && (
                    <div className="overflow-x-auto">
                      <table className="min-w-full text-sm">
                        <thead className="bg-slate-800/50">
                          <tr>
                            <th className="px-3 py-2 text-left font-medium text-slate-300">Column</th>
                            <th className="px-3 py-2 text-right font-medium text-slate-300">MSE</th>
                            <th className="px-3 py-2 text-right font-medium text-slate-300">Max Error</th>
                            <th className="px-3 py-2 text-right font-medium text-slate-300">Correlation</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                          {Object.entries(methodologyResults.equivalence.column_errors).map(([col, err]) => (
                            <tr key={col} className="hover:bg-slate-800/30">
                              <td className="px-3 py-2 text-slate-300">{col}</td>
                              <td className="px-3 py-2 text-right font-mono text-xs text-slate-400">
                                {err.mse?.toExponential(2)}
                              </td>
                              <td className="px-3 py-2 text-right font-mono text-xs text-slate-400">
                                {err.max_error?.toExponential(2)}
                              </td>
                              <td className={`px-3 py-2 text-right font-mono text-xs ${
                                err.correlation > 0.99 ? 'text-green-400' : 'text-yellow-400'
                              }`}>
                                {err.correlation?.toFixed(4)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  <div className={`p-4 rounded-lg mt-4 ${
                    methodologyResults.equivalence.is_equivalent
                      ? 'bg-green-500/10 border border-green-500/30'
                      : 'bg-red-500/10 border border-red-500/30'
                  }`}>
                    <p className="text-sm text-slate-300">{methodologyResults.equivalence.interpretation}</p>
                  </div>
                </Card>
              )}

              {/* No Results Yet */}
              {!methodologyJob && methodologyResults?.overall_status === 'incomplete' && (
                <Card>
                  <div className="text-center py-8">
                    <div className="w-16 h-16 rounded-full bg-purple-500/20 flex items-center justify-center mx-auto mb-4">
                      <svg className="w-8 h-8 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                      </svg>
                    </div>
                    <h3 className="text-lg font-semibold text-slate-200 mb-2">No Methodology Validation Yet</h3>
                    <p className="text-slate-400 mb-4">
                      Run the methodology suite to generate publication-quality validation results.
                    </p>
                  </div>
                </Card>
              )}
            </div>
          )}

          {/* Distributions Tab */}
          {activeTab === 'distributions' && validationResults.distributions && (
            <div className="space-y-4">
              {/* Distribution Status Cards */}
              {validationResults.distributions.features && (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {Object.entries(validationResults.distributions.features).map(([feat, data]) => (
                    <Card key={feat}>
                      <div className="text-center py-2">
                        <p className="text-xs text-slate-500 truncate">{feat.replace(/_/g, ' ')}</p>
                        <p className="text-lg font-bold text-slate-200 mt-1">
                          {data.js_divergence?.toFixed(3) || 'N/A'}
                        </p>
                        <span className={`text-xs px-2 py-0.5 rounded ${getStatusBadge(data.status)}`}>
                          {data.status || 'N/A'}
                        </span>
                      </div>
                    </Card>
                  ))}
                </div>
              )}

              {/* Distribution Charts */}
              {validationResults.distributions.features && Object.entries(validationResults.distributions.features).map(([feat, data]) => {
                if (!data.bins || !data.synthetic?.histogram) return null

                const binCenters = data.bins.slice(0, -1).map((b, i) =>
                  (b + data.bins[i + 1]) / 2
                )

                return (
                  <Card
                    key={feat}
                    title={`${feat.replace(/_/g, ' ')} Distribution`}
                    actions={
                      <ExportButton
                        data={binCenters.map((x, i) => ({
                          bin_center: x,
                          synthetic: data.synthetic.histogram[i],
                          real: data.real.histogram[i]
                        }))}
                        filename={`distribution_${feat}`}
                        formats={['csv', 'json']}
                      />
                    }
                  >
                    <Plot
                      ref={distributionPlotRef}
                      data={[
                        {
                          x: binCenters,
                          y: data.synthetic.histogram,
                          type: 'bar',
                          name: 'Synthetic',
                          marker: { color: 'rgba(59, 130, 246, 0.7)' }
                        },
                        {
                          x: binCenters,
                          y: data.real.histogram,
                          type: 'bar',
                          name: 'Real (PMData)',
                          marker: { color: 'rgba(239, 68, 68, 0.7)' }
                        }
                      ]}
                      layout={{
                        ...darkLayout,
                        barmode: 'overlay',
                        height: 280,
                        margin: { t: 30, r: 20, b: 50, l: 50 },
                        xaxis: { ...darkLayout.xaxis, title: feat.replace(/_/g, ' '), range: [0, 1] },
                        yaxis: { ...darkLayout.yaxis, title: 'Density' },
                        legend: {
                          ...darkLayout.legend,
                          orientation: 'h',
                          y: 1.15,
                          x: 0.5,
                          xanchor: 'center'
                        },
                        annotations: [{
                          x: 0.98,
                          y: 0.95,
                          xref: 'paper',
                          yref: 'paper',
                          text: `JS: ${data.js_divergence?.toFixed(3)}`,
                          showarrow: false,
                          bgcolor: data.status === 'PASS' ? 'rgba(34,197,94,0.2)' : 'rgba(234,179,8,0.2)',
                          borderpad: 4,
                          font: { color: '#cbd5e1', size: 11 }
                        }]
                      }}
                      config={{ displayModeBar: false, responsive: true }}
                      useResizeHandler
                      style={{ width: '100%' }}
                    />
                    <div className="grid grid-cols-2 gap-4 mt-3 text-xs">
                      <div className="bg-blue-500/10 p-3 rounded-lg border border-blue-500/20">
                        <p className="font-medium text-blue-400">Synthetic</p>
                        <p className="text-slate-400">Mean: {data.synthetic.mean?.toFixed(3)}, Std: {data.synthetic.std?.toFixed(3)}</p>
                      </div>
                      <div className="bg-red-500/10 p-3 rounded-lg border border-red-500/20">
                        <p className="font-medium text-red-400">Real (PMData)</p>
                        <p className="text-slate-400">Mean: {data.real.mean?.toFixed(3)}, Std: {data.real.std?.toFixed(3)}</p>
                      </div>
                    </div>
                  </Card>
                )
              })}
            </div>
          )}

          {/* Sim2Real Tab */}
          {activeTab === 'sim2real' && validationResults.sim2real && (
            <div className="space-y-4">
              <Card title="Sim2Real Transfer Learning Results">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
                  <div className="text-center p-4 bg-slate-800/50 rounded-lg">
                    <p className="text-2xl font-bold text-blue-400">
                      {validationResults.sim2real.auc?.toFixed(4)}
                    </p>
                    <p className="text-xs text-slate-500">AUC Score</p>
                  </div>
                  <div className="text-center p-4 bg-slate-800/50 rounded-lg">
                    <p className="text-2xl font-bold text-green-400">
                      {validationResults.sim2real.ap?.toFixed(4)}
                    </p>
                    <p className="text-xs text-slate-500">Avg Precision</p>
                  </div>
                  <div className="text-center p-4 bg-slate-800/50 rounded-lg">
                    <p className="text-2xl font-bold text-purple-400">
                      {validationResults.sim2real.n_train?.toLocaleString()}
                    </p>
                    <p className="text-xs text-slate-500">Train Samples</p>
                  </div>
                  <div className="text-center p-4 bg-slate-800/50 rounded-lg">
                    <p className="text-2xl font-bold text-orange-400">
                      {validationResults.sim2real.n_test?.toLocaleString()}
                    </p>
                    <p className="text-xs text-slate-500">Test Samples</p>
                  </div>
                </div>

                <div className={`p-4 rounded-lg ${
                  validationResults.sim2real.status === 'success' ? 'bg-green-500/10 border border-green-500/30' :
                  validationResults.sim2real.status === 'warning' ? 'bg-yellow-500/10 border border-yellow-500/30' :
                  'bg-red-500/10 border border-red-500/30'
                }`}>
                  <p className="font-medium text-slate-200">{validationResults.sim2real.interpretation}</p>
                </div>

                {validationResults.sim2real.features_used && (
                  <div className="mt-4">
                    <p className="text-sm font-medium text-slate-300 mb-2">Features Used:</p>
                    <div className="flex flex-wrap gap-2">
                      {validationResults.sim2real.features_used.map(feat => (
                        <span key={feat} className="px-2 py-1 bg-slate-800 border border-slate-700 rounded text-xs text-slate-400">
                          {feat}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </Card>

              {/* AUC Interpretation Guide */}
              <Card title="AUC Interpretation Guide">
                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-3 p-3 rounded-lg bg-green-500/10 border border-green-500/20">
                    <span className="font-mono font-bold text-green-400 w-12">0.60+</span>
                    <span className="text-slate-300">Good - Synthetic data captures real injury patterns</span>
                  </div>
                  <div className="flex items-center gap-3 p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
                    <span className="font-mono font-bold text-yellow-400 w-12">0.55</span>
                    <span className="text-slate-300">Moderate - Some signal transfers, more tuning needed</span>
                  </div>
                  <div className="flex items-center gap-3 p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                    <span className="font-mono font-bold text-red-400 w-12">0.50</span>
                    <span className="text-slate-300">Poor - No better than random, distributions misaligned</span>
                  </div>
                </div>
              </Card>
            </div>
          )}

          {/* Causal Mechanism Tab */}
          {activeTab === 'causal' && validationResults.causal_mechanism && (
            <div className="space-y-4">
              {/* Causal Asymmetry Chart */}
              {validationResults.causal_mechanism.causal_asymmetry?.zones && (
                <Card
                  title="Causal Asymmetry: Risk per Load Unit by ACWR Zone"
                  actions={
                    <ExportButton
                      data={validationResults.causal_mechanism.causal_asymmetry.zones}
                      filename="causal_asymmetry"
                      formats={['csv', 'json']}
                    />
                  }
                >
                  <Plot
                    ref={causalPlotRef}
                    data={[{
                      x: validationResults.causal_mechanism.causal_asymmetry.zones.map(z => z.zone),
                      y: validationResults.causal_mechanism.causal_asymmetry.zones.map(z => z.risk_per_load),
                      type: 'bar',
                      marker: {
                        color: validationResults.causal_mechanism.causal_asymmetry.zones.map(z =>
                          z.zone === 'Optimal' ? '#22c55e' :
                          z.zone === 'Undertrained' ? '#ef4444' :
                          z.zone === 'High Risk' ? '#f97316' : '#eab308'
                        )
                      },
                      text: validationResults.causal_mechanism.causal_asymmetry.zones.map(z => `${z.relative_risk}x`),
                      textposition: 'outside',
                      textfont: { size: 12, color: '#cbd5e1' }
                    }]}
                    layout={{
                      ...darkLayout,
                      height: 350,
                      margin: { t: 40, r: 20, b: 80, l: 60 },
                      xaxis: { ...darkLayout.xaxis, title: 'ACWR Zone', tickangle: -30 },
                      yaxis: { ...darkLayout.yaxis, title: 'Injuries per 10,000 TSS Units' },
                      showlegend: false,
                      annotations: validationResults.causal_mechanism.causal_asymmetry.summary?.interpretation ? [{
                        x: 0.5,
                        y: -0.25,
                        xref: 'paper',
                        yref: 'paper',
                        text: validationResults.causal_mechanism.causal_asymmetry.summary.interpretation,
                        showarrow: false,
                        font: { size: 10, color: '#94a3b8' },
                        align: 'center'
                      }] : []
                    }}
                    config={{ displayModeBar: false, responsive: true }}
                    useResizeHandler
                    style={{ width: '100%' }}
                  />
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-4">
                    {validationResults.causal_mechanism.causal_asymmetry.zones.map(zone => (
                      <div key={zone.zone} className="text-center p-3 bg-slate-800/50 rounded-lg text-xs">
                        <p className="font-medium text-slate-300">{zone.zone}</p>
                        <p className="text-slate-400">{zone.total_injuries} injuries / {zone.total_days} days</p>
                        <p className="text-slate-500">{zone.injury_rate_pct}% daily rate</p>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* Risk Landscape */}
              {validationResults.causal_mechanism.risk_landscape?.risk_grid && (
                <Card title="Risk Landscape: Acute vs Chronic Load">
                  <Plot
                    ref={riskLandscapePlotRef}
                    data={[{
                      z: validationResults.causal_mechanism.risk_landscape.risk_grid,
                      x: validationResults.causal_mechanism.risk_landscape.chronic_values,
                      y: validationResults.causal_mechanism.risk_landscape.acute_values,
                      type: 'contour',
                      colorscale: 'RdYlGn',
                      reversescale: true,
                      contours: { showlabels: true, labelfont: { size: 10, color: '#fff' } },
                      colorbar: { title: 'Injury Prob', titleside: 'right', tickfont: { color: '#94a3b8' } }
                    },
                    // ACWR reference lines
                    {
                      x: validationResults.causal_mechanism.risk_landscape.acwr_lines?.x || [],
                      y: validationResults.causal_mechanism.risk_landscape.acwr_lines?.['acwr_0.8'] || [],
                      type: 'scatter',
                      mode: 'lines',
                      name: 'ACWR 0.8',
                      line: { dash: 'dash', color: 'white', width: 2 }
                    },
                    {
                      x: validationResults.causal_mechanism.risk_landscape.acwr_lines?.x || [],
                      y: validationResults.causal_mechanism.risk_landscape.acwr_lines?.['acwr_1.3'] || [],
                      type: 'scatter',
                      mode: 'lines',
                      name: 'ACWR 1.3',
                      line: { dash: 'dash', color: 'white', width: 2 }
                    }]}
                    layout={{
                      ...darkLayout,
                      height: 400,
                      margin: { t: 30, r: 120, b: 60, l: 60 },
                      xaxis: { ...darkLayout.xaxis, title: 'Chronic Load (Fitness)' },
                      yaxis: { ...darkLayout.yaxis, title: 'Acute Load (Fatigue)' },
                      showlegend: true,
                      legend: {
                        ...darkLayout.legend,
                        orientation: 'h',
                        y: 1.1,
                        x: 0.5,
                        xanchor: 'center'
                      }
                    }}
                    config={{ displayModeBar: false, responsive: true }}
                    useResizeHandler
                    style={{ width: '100%' }}
                  />
                  <p className="text-xs text-slate-500 mt-2 text-center">
                    The "Sweet Spot" (green) is where ACWR is 0.8-1.3. Red zones indicate elevated risk.
                  </p>
                </Card>
              )}

              {/* No Causal Data Warning */}
              {!validationResults.causal_mechanism.causal_asymmetry?.zones && (
                <Card>
                  <div className="text-center py-8">
                    <div className="w-16 h-16 rounded-full bg-amber-500/20 flex items-center justify-center mx-auto mb-4">
                      <svg className="w-8 h-8 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                    </div>
                    <h3 className="text-lg font-semibold text-slate-200 mb-2">Glass-Box Data Required</h3>
                    <p className="text-slate-400 mb-4">
                      Regenerate synthetic data to include causal mechanism columns (ACWR, injury_type, wellness_vulnerability).
                    </p>
                  </div>
                </Card>
              )}
            </div>
          )}

          {/* PMData Analysis Tab */}
          {activeTab === 'pmdata' && validationResults.pmdata_analysis && (
            <div className="space-y-4">
              {/* PMData Stats */}
              <Card title="PMData Overview">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  <div className="text-center p-4 bg-slate-800/50 rounded-lg">
                    <p className="text-xl font-bold text-slate-200">{validationResults.pmdata_analysis.samples?.toLocaleString()}</p>
                    <p className="text-xs text-slate-500">Total Samples</p>
                  </div>
                  <div className="text-center p-4 bg-slate-800/50 rounded-lg">
                    <p className="text-xl font-bold text-green-400">{validationResults.pmdata_analysis.safe_days?.toLocaleString()}</p>
                    <p className="text-xs text-slate-500">Safe Days</p>
                  </div>
                  <div className="text-center p-4 bg-slate-800/50 rounded-lg">
                    <p className="text-xl font-bold text-orange-400">{validationResults.pmdata_analysis.preinjury_days?.toLocaleString()}</p>
                    <p className="text-xs text-slate-500">Pre-Injury Days</p>
                  </div>
                  <div className="text-center p-4 bg-slate-800/50 rounded-lg">
                    <p className="text-xl font-bold text-red-400">{((validationResults.pmdata_analysis.injury_rate || 0) * 100).toFixed(1)}%</p>
                    <p className="text-xs text-slate-500">Injury Rate</p>
                  </div>
                </div>
              </Card>

              {/* Feature Importance */}
              {validationResults.pmdata_analysis.feature_importance && (
                <Card title="Feature Importance (Real Data)">
                  <Plot
                    data={[{
                      x: validationResults.pmdata_analysis.feature_importance.map(f => f.importance),
                      y: validationResults.pmdata_analysis.feature_importance.map(f => f.feature.replace(/_/g, ' ')),
                      type: 'bar',
                      orientation: 'h',
                      marker: {
                        color: validationResults.pmdata_analysis.feature_importance.map((_, i) =>
                          `rgba(99, 102, 241, ${1 - i * 0.08})`
                        )
                      }
                    }]}
                    layout={{
                      ...darkLayout,
                      height: 300,
                      margin: { t: 20, r: 20, b: 50, l: 140 },
                      xaxis: { ...darkLayout.xaxis, title: 'Importance' },
                      yaxis: { ...darkLayout.yaxis, automargin: true, tickfont: { size: 10, color: '#94a3b8' } }
                    }}
                    config={{ displayModeBar: false, responsive: true }}
                    useResizeHandler
                    style={{ width: '100%' }}
                  />
                  <p className="text-xs text-slate-500 mt-2">
                    Features ranked by Random Forest importance trained on real PMData
                  </p>
                </Card>
              )}

              {/* Correlations */}
              {validationResults.pmdata_analysis.correlations && (
                <Card title="Feature Correlations with Injury">
                  <div className="overflow-x-auto">
                    <table className="min-w-full text-sm">
                      <thead className="bg-slate-800/50">
                        <tr>
                          <th className="px-3 py-2 text-left font-medium text-slate-300">Feature</th>
                          <th className="px-3 py-2 text-right font-medium text-slate-300">Correlation</th>
                          <th className="px-3 py-2 text-center font-medium text-slate-300">Significant</th>
                          <th className="px-3 py-2 text-left font-medium text-slate-300">Direction</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800">
                        {validationResults.pmdata_analysis.correlations.slice(0, 10).map(c => (
                          <tr key={c.feature} className="hover:bg-slate-800/30">
                            <td className="px-3 py-2 text-slate-300">{c.feature.replace(/_/g, ' ')}</td>
                            <td className={`px-3 py-2 text-right font-mono ${
                              c.correlation > 0 ? 'text-red-400' : 'text-green-400'
                            }`}>
                              {c.correlation > 0 ? '+' : ''}{c.correlation?.toFixed(4)}
                            </td>
                            <td className="px-3 py-2 text-center">
                              {c.significant ? (
                                <span className="text-green-400">Yes</span>
                              ) : (
                                <span className="text-slate-500">No</span>
                              )}
                            </td>
                            <td className="px-3 py-2 text-xs text-slate-400">{c.direction}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Card>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default ExternalValidationPage
