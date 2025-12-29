import { useState, useEffect, useRef } from 'react'
import Plot from 'react-plotly.js'
import { usePipeline } from '../../context/PipelineContext'
import { useTheme } from '../../context/ThemeContext'
import { analyticsApi, trainingApi } from '../../api'
import Card from '../common/Card'
import InterventionSimulator from './InterventionSimulator'
import MethodologyTooltip, { METHODOLOGY_TERMS } from '../common/MethodologyTooltip'
import ExportButton from '../common/ExportButton'
import StatisticalMetric from '../common/StatisticalMetric'
import ReproducibilityPanel from '../common/ReproducibilityPanel'

const METRICS = ['hrv', 'resting_hr', 'sleep_hours', 'sleep_quality', 'stress', 'body_battery_morning', 'actual_tss']

const METRIC_DESCRIPTIONS = {
  hrv: { label: 'HRV', full: 'Heart Rate Variability', unit: 'ms', methodology: 'HRV' },
  resting_hr: { label: 'RHR', full: 'Resting Heart Rate', unit: 'bpm' },
  sleep_hours: { label: 'Sleep', full: 'Sleep Duration', unit: 'hours' },
  sleep_quality: { label: 'Sleep Quality', full: 'Sleep Quality Index', unit: '%' },
  stress: { label: 'Stress', full: 'Stress Level', unit: 'score' },
  body_battery_morning: { label: 'Body Battery', full: 'Morning Body Battery', unit: '%' },
  actual_tss: { label: 'TSS', full: 'Training Stress Score', unit: 'points' }
}

// Theme layouts for Plotly (will be selected based on theme)
const chartLayout = {
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor: 'rgba(15,23,42,0.5)',
  font: { color: '#94a3b8', size: 11 },
  xaxis: { gridcolor: '#334155', zerolinecolor: '#475569' },
  yaxis: { gridcolor: '#334155', zerolinecolor: '#475569' },
  legend: { bgcolor: 'rgba(0,0,0,0)', font: { color: '#cbd5e1' } }
}

const lightLayout = {
  paper_bgcolor: 'rgba(255,255,255,0)',
  plot_bgcolor: 'rgba(249,250,251,0.8)',
  font: { color: '#374151', size: 11 },
  xaxis: { gridcolor: '#e5e7eb', zerolinecolor: '#d1d5db' },
  yaxis: { gridcolor: '#e5e7eb', zerolinecolor: '#d1d5db' },
  legend: { bgcolor: 'rgba(255,255,255,0)', font: { color: '#1f2937' } }
}

function AnalyticsPage() {
  const { datasets, currentDataset, setCurrentDataset, refreshDatasets } = usePipeline()
  const { isDark } = useTheme()
  const chartLayout = isDark ? chartLayout : lightLayout

  const [selectedDataset, setSelectedDataset] = useState('')
  const [activeTab, setActiveTab] = useState('distributions')
  const [loading, setLoading] = useState(false)

  // Data states
  const [distributions, setDistributions] = useState({})
  const [correlations, setCorrelations] = useState(null)
  const [preInjury, setPreInjury] = useState(null)
  const [acwrZones, setAcwrZones] = useState(null)
  const [datasetStats, setDatasetStats] = useState(null)

  // What-If Analysis states
  const [models, setModels] = useState([])
  const [selectedModel, setSelectedModel] = useState('')
  const [athletes, setAthletes] = useState([])
  const [selectedAthlete, setSelectedAthlete] = useState('')
  const [athleteTimeline, setAthleteTimeline] = useState(null)
  const [selectedDate, setSelectedDate] = useState('')

  // Plot refs for export
  const corrPlotRef = useRef(null)

  useEffect(() => {
    refreshDatasets()
  }, [refreshDatasets])

  useEffect(() => {
    if (currentDataset) {
      setSelectedDataset(currentDataset)
    }
  }, [currentDataset])

  useEffect(() => {
    if (selectedDataset) {
      loadAnalytics()
      if (activeTab === 'whatIf') {
        fetchAthletes(selectedDataset)
        fetchModels()
      }
    }
  }, [selectedDataset, activeTab])

  const fetchAthletes = async (datasetId) => {
    try {
      const res = await analyticsApi.listAthletes(datasetId)
      setAthletes(res.data?.athletes || [])
    } catch (error) {
      console.error('Failed to fetch athletes:', error)
      setAthletes([])
    }
  }

  const fetchModels = async () => {
    try {
      const res = await trainingApi.listModels()
      setModels(res.data?.models || [])
    } catch (error) {
      console.error('Failed to fetch models:', error)
      setModels([])
    }
  }

  const handleAthleteChange = async (athleteId) => {
    setSelectedAthlete(athleteId)
    setSelectedDate('')
    if (athleteId) {
      try {
        const res = await analyticsApi.getAthleteTimeline(selectedDataset, athleteId)
        setAthleteTimeline(res.data)
      } catch (error) {
        console.error('Failed to fetch athlete timeline:', error)
      }
    }
  }

  const loadAnalytics = async () => {
    setLoading(true)
    try {
      switch (activeTab) {
        case 'distributions':
          // Use individual catches to prevent one failure from blocking all distributions
          const distPromises = METRICS.map(m =>
            analyticsApi.getDistribution(selectedDataset, m)
              .then(r => ({ metric: m, data: r.data }))
              .catch(err => {
                console.warn(`Failed to load distribution for ${m}:`, err)
                return { metric: m, data: null }
              })
          )
          const distResults = await Promise.all(distPromises)
          const distMap = {}
          distResults.forEach(r => { if (r.data) distMap[r.metric] = r.data })
          setDistributions(distMap)
          break

        case 'correlations':
          const corrRes = await analyticsApi.getCorrelations(selectedDataset, METRICS)
          setCorrelations(corrRes.data)
          break

        case 'preInjury':
          const piRes = await analyticsApi.getPreInjuryWindow(selectedDataset, 14)
          setPreInjury(piRes.data)
          break

        case 'acwr':
          const acwrRes = await analyticsApi.getAcwrZones(selectedDataset)
          setAcwrZones(acwrRes.data)
          break

        case 'stats':
          const statsRes = await analyticsApi.getDatasetStats(selectedDataset)
          setDatasetStats(statsRes.data)
          break
      }
    } catch (error) {
      console.error('Failed to load analytics:', error)
    } finally {
      setLoading(false)
    }
  }

  const tabs = [
    { id: 'distributions', label: 'Distributions', description: 'Variable histograms with descriptive statistics' },
    { id: 'correlations', label: 'Correlations', description: 'Pearson correlation matrix heatmap' },
    { id: 'preInjury', label: 'Pre-Injury', description: 'Temporal patterns preceding injury events' },
    { id: 'acwr', label: 'ACWR Zones', description: 'Workload ratio distribution and injury rates' },
    { id: 'stats', label: 'Statistics', description: 'Descriptive statistics summary' },
    { id: 'whatIf', label: 'What-If', description: 'Counterfactual intervention analysis' }
  ]

  // Prepare export data for distributions
  const getDistributionExportData = (metric, data) => {
    if (!data) return []
    return data.bin_edges.slice(0, -1).map((edge, i) => ({
      bin_start: edge,
      bin_end: data.bin_edges[i + 1],
      count: data.histogram[i]
    }))
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">Dataset Analytics</h1>
        <p className="text-sm sm:text-base text-gray-600 dark:text-slate-400 mt-1">
          Exploratory data analysis and statistical visualization
        </p>
      </div>

      {/* Dataset Selection */}
      <Card>
        <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4">
          <label className="text-sm font-medium text-gray-700 dark:text-slate-300">Dataset:</label>
          <select
            value={selectedDataset}
            onChange={e => {
              setSelectedDataset(e.target.value)
              setCurrentDataset(e.target.value)
            }}
            className="flex-1 sm:flex-none sm:min-w-64 px-3 py-2 bg-gray-100 dark:bg-slate-800 border border-gray-300 dark:border-slate-700 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 text-sm"
          >
            <option value="">Select a dataset...</option>
            {datasets.map(ds => (
              <option key={ds.id} value={ds.id}>
                {ds.id} (n={ds.n_athletes} athletes)
              </option>
            ))}
          </select>
          {selectedDataset && (
            <span className="text-xs text-gray-500 dark:text-slate-500">
              Selected for analysis
            </span>
          )}
        </div>
      </Card>

      {selectedDataset && (
        <>
          {/* Tabs */}
          <div className="border-b border-gray-200 dark:border-slate-800 -mx-4 px-4 sm:mx-0 sm:px-0 overflow-x-auto">
            <nav className="flex space-x-4 sm:space-x-8 min-w-max">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-3 sm:py-4 px-1 border-b-2 font-medium text-xs sm:text-sm whitespace-nowrap transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-400'
                      : 'border-transparent text-gray-500 dark:text-slate-500 hover:text-gray-700 dark:text-slate-300 hover:border-slate-600'
                  }`}
                  title={tab.description}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Description */}
          <div className="text-xs text-gray-500 dark:text-slate-500 -mt-2">
            {tabs.find(t => t.id === activeTab)?.description}
          </div>

          {loading && activeTab !== 'whatIf' ? (
            <Card>
              <div className="flex justify-center py-8 sm:py-12">
                <div className="animate-spin h-6 w-6 sm:h-8 sm:w-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
              </div>
            </Card>
          ) : (
            <>
              {/* Distributions */}
              {activeTab === 'distributions' && (
                <div className="space-y-6">
                  <div className="p-3 bg-gray-100 dark:bg-gray-100 dark:bg-slate-800/50 rounded-lg border border-gray-300 dark:border-slate-700">
                    <p className="text-xs text-gray-600 dark:text-slate-400">
                      <strong className="text-gray-700 dark:text-slate-300">Methodology:</strong> Histograms display the empirical distribution of each biomarker.
                      Vertical annotations indicate sample means. Consider examining distributions by injury status for comparative analysis.
                    </p>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                    {Object.entries(distributions).map(([metric, data]) => {
                      const metricInfo = METRIC_DESCRIPTIONS[metric] || { label: metric, full: metric, unit: '' }
                      return (
                        <Card
                          key={metric}
                          title={
                            <span className="flex items-center gap-2">
                              {metricInfo.methodology ? (
                                <MethodologyTooltip {...METHODOLOGY_TERMS[metricInfo.methodology]}>
                                  {metricInfo.full}
                                </MethodologyTooltip>
                              ) : metricInfo.full}
                              <span className="text-xs font-normal text-gray-500 dark:text-slate-500">({metricInfo.unit})</span>
                            </span>
                          }
                          actions={
                            <ExportButton
                              data={getDistributionExportData(metric, data)}
                              filename={`distribution_${metric}_${selectedDataset}`}
                              formats={['csv', 'json']}
                            />
                          }
                        >
                          <Plot
                            data={[
                              {
                                x: data.bin_edges.slice(0, -1),
                                y: data.histogram,
                                type: 'bar',
                                marker: { color: '#3b82f6' }
                              }
                            ]}
                            layout={{
                              ...chartLayout,
                              xaxis: { ...chartLayout.xaxis, title: metricInfo.label, tickfont: { size: 10 } },
                              yaxis: { ...chartLayout.yaxis, title: 'Frequency', tickfont: { size: 10 } },
                              margin: { t: 10, r: 10, b: 50, l: 50 },
                              autosize: true,
                              annotations: [
                                {
                                  x: data.mean,
                                  y: Math.max(...data.histogram) * 0.9,
                                  text: `μ = ${data.mean.toFixed(2)}`,
                                  showarrow: true,
                                  arrowhead: 2,
                                  font: { size: 10, color: '#94a3b8' },
                                  arrowcolor: '#64748b'
                                }
                              ]
                            }}
                            useResizeHandler
                            style={{ width: '100%', height: '250px' }}
                            config={{ displayModeBar: false }}
                          />
                          <div className="mt-2 flex justify-between text-xs text-gray-500 dark:text-slate-500 font-mono">
                            <span>μ = {data.mean?.toFixed(2)}</span>
                            <span>σ = {data.std?.toFixed(2)}</span>
                            <span>n = {data.n?.toLocaleString()}</span>
                          </div>
                        </Card>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* Correlations */}
              {activeTab === 'correlations' && correlations && (
                <Card
                  title="Pearson Correlation Matrix"
                  actions={
                    <ExportButton
                      data={correlations.feature_names.map((f, i) => {
                        const row = { feature: f }
                        correlations.feature_names.forEach((f2, j) => {
                          row[f2] = correlations.correlation_matrix[i][j]
                        })
                        return row
                      })}
                      filename={`correlation_matrix_${selectedDataset}`}
                      formats={['csv', 'json', 'svg', 'png']}
                      plotRef={corrPlotRef}
                    />
                  }
                >
                  <div className="mb-4 p-3 bg-gray-100 dark:bg-gray-100 dark:bg-slate-800/50 rounded-lg border border-gray-300 dark:border-slate-700">
                    <p className="text-xs text-gray-600 dark:text-slate-400">
                      <strong className="text-gray-700 dark:text-slate-300">Interpretation:</strong> Pearson correlation coefficients range from -1 (perfect negative)
                      to +1 (perfect positive). Values near 0 indicate weak linear relationship. For non-linear relationships, consider
                      Spearman rank correlation.
                    </p>
                  </div>
                  <div className="-mx-2 sm:mx-0 overflow-x-auto">
                    <Plot
                      ref={corrPlotRef}
                      data={[
                        {
                          z: correlations.correlation_matrix,
                          x: correlations.feature_names,
                          y: correlations.feature_names,
                          type: 'heatmap',
                          colorscale: 'RdBu',
                          zmin: -1,
                          zmax: 1,
                          text: correlations.correlation_matrix.map(row =>
                            row.map(val => val.toFixed(2))
                          ),
                          texttemplate: '%{text}',
                          textfont: { size: 9, color: '#fff' },
                          hovertemplate: '%{x} vs %{y}: r = %{z:.3f}<extra></extra>',
                          colorbar: {
                            title: 'r',
                            titleside: 'right',
                            tickfont: { color: '#94a3b8' },
                            titlefont: { color: '#94a3b8' }
                          }
                        }
                      ]}
                      layout={{
                        ...chartLayout,
                        margin: { t: 30, r: 60, b: 100, l: 100 },
                        autosize: true,
                        xaxis: { ...chartLayout.xaxis, tickfont: { size: 9, color: '#94a3b8' }, tickangle: 45 },
                        yaxis: { ...chartLayout.yaxis, tickfont: { size: 9, color: '#94a3b8' } }
                      }}
                      useResizeHandler
                      style={{ width: '100%', minWidth: '350px', height: '450px' }}
                      config={{ displayModeBar: false }}
                    />
                  </div>
                </Card>
              )}

              {/* Pre-Injury Window */}
              {activeTab === 'preInjury' && preInjury && (
                <Card title={`Pre-Injury Temporal Patterns (n = ${preInjury.n_injuries} injury events)`}>
                  <div className="mb-4 p-3 bg-gray-100 dark:bg-gray-100 dark:bg-slate-800/50 rounded-lg border border-gray-300 dark:border-slate-700">
                    <p className="text-xs text-gray-600 dark:text-slate-400">
                      <strong className="text-gray-700 dark:text-slate-300">Methodology:</strong> Average biomarker values aligned to injury onset (day 0, marked with red dashed line).
                      Negative days represent the period before injury. Useful for identifying prodromal patterns and early warning indicators.
                    </p>
                  </div>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                    {Object.entries(preInjury.metrics || {}).map(([metric, data]) => {
                      const metricInfo = METRIC_DESCRIPTIONS[metric] || { label: metric, full: metric }
                      return (
                        <div key={metric} className="p-4 bg-gray-100 dark:bg-slate-800/30 rounded-lg">
                          <h4 className="font-medium text-sm text-gray-900 dark:text-white mb-3">
                            {metricInfo.methodology ? (
                              <MethodologyTooltip {...METHODOLOGY_TERMS[metricInfo.methodology]}>
                                {metricInfo.full}
                              </MethodologyTooltip>
                            ) : metricInfo.full}
                          </h4>
                          <Plot
                            data={[
                              {
                                x: data.days,
                                y: data.average,
                                type: 'scatter',
                                mode: 'lines+markers',
                                name: metric,
                                line: { color: '#3b82f6', width: 2 },
                                marker: { size: 4 }
                              }
                            ]}
                            layout={{
                              ...chartLayout,
                              xaxis: { ...chartLayout.xaxis, title: 'Days Before Injury', zeroline: true, tickfont: { size: 10 } },
                              yaxis: { ...chartLayout.yaxis, title: metricInfo.label, tickfont: { size: 10 } },
                              margin: { t: 10, r: 10, b: 50, l: 60 },
                              autosize: true,
                              shapes: [
                                {
                                  type: 'line',
                                  x0: 0, x1: 0,
                                  y0: Math.min(...data.average.filter(v => v !== null)),
                                  y1: Math.max(...data.average.filter(v => v !== null)),
                                  line: { color: '#ef4444', width: 2, dash: 'dash' }
                                }
                              ]
                            }}
                            useResizeHandler
                            style={{ width: '100%', height: '220px' }}
                            config={{ displayModeBar: false }}
                          />
                        </div>
                      )
                    })}
                  </div>
                </Card>
              )}

              {/* ACWR Zones */}
              {activeTab === 'acwr' && acwrZones && (
                <div className="space-y-6">
                  <div className="p-4 bg-gray-100 dark:bg-gray-100 dark:bg-slate-800/50 rounded-lg border border-gray-300 dark:border-slate-700">
                    <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                      <MethodologyTooltip {...METHODOLOGY_TERMS.ACWR}>
                        Acute:Chronic Workload Ratio (ACWR) Analysis
                      </MethodologyTooltip>
                    </h4>
                    <p className="text-xs text-gray-600 dark:text-slate-400 mb-3">
                      ACWR compares acute training load (7-day) to chronic load (28-day rolling average).
                      Zone classification follows Gabbett's framework (2016):
                    </p>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                      <div className="p-2 bg-yellow-500/10 border border-yellow-500/20 rounded">
                        <div className="font-medium text-yellow-400">Low</div>
                        <div className="text-gray-500 dark:text-slate-500">ACWR &lt; 0.8</div>
                      </div>
                      <div className="p-2 bg-green-500/10 border border-green-500/20 rounded">
                        <div className="font-medium text-green-400">Optimal</div>
                        <div className="text-gray-500 dark:text-slate-500">0.8 ≤ ACWR ≤ 1.3</div>
                      </div>
                      <div className="p-2 bg-orange-500/10 border border-orange-500/20 rounded">
                        <div className="font-medium text-orange-400">High</div>
                        <div className="text-gray-500 dark:text-slate-500">1.3 &lt; ACWR ≤ 1.5</div>
                      </div>
                      <div className="p-2 bg-red-500/10 border border-red-500/20 rounded">
                        <div className="font-medium text-red-400">Very High</div>
                        <div className="text-gray-500 dark:text-slate-500">ACWR &gt; 1.5</div>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                    <Card
                      title="ACWR Zone Distribution"
                      actions={
                        <ExportButton
                          data={Object.entries(acwrZones.zone_distribution).map(([zone, count]) => ({ zone, count }))}
                          filename={`acwr_distribution_${selectedDataset}`}
                          formats={['csv', 'json']}
                        />
                      }
                    >
                      <Plot
                        data={[
                          {
                            values: Object.values(acwrZones.zone_distribution),
                            labels: Object.keys(acwrZones.zone_distribution),
                            type: 'pie',
                            marker: {
                              colors: ['#fbbf24', '#10b981', '#f97316', '#ef4444']
                            },
                            textfont: { size: 11, color: '#fff' },
                            hovertemplate: '%{label}: %{value} (%{percent})<extra></extra>'
                          }
                        ]}
                        layout={{
                          ...chartLayout,
                          margin: { t: 10, r: 10, b: 40, l: 10 },
                          autosize: true,
                          showlegend: true,
                          legend: { ...chartLayout.legend, font: { size: 10, color: '#cbd5e1' }, orientation: 'h', y: -0.1 }
                        }}
                        useResizeHandler
                        style={{ width: '100%', height: '280px' }}
                        config={{ displayModeBar: false }}
                      />
                    </Card>

                    <Card
                      title="Injury Rate by ACWR Zone"
                      actions={
                        <ExportButton
                          data={acwrZones.zone_order.map(z => ({
                            zone: z,
                            injury_rate: acwrZones.injury_rate_by_zone[z] || 0,
                            injury_rate_percent: ((acwrZones.injury_rate_by_zone[z] || 0) * 100).toFixed(2)
                          }))}
                          filename={`acwr_injury_rates_${selectedDataset}`}
                          formats={['csv', 'json']}
                        />
                      }
                    >
                      <Plot
                        data={[
                          {
                            x: acwrZones.zone_order,
                            y: acwrZones.zone_order.map(z => (acwrZones.injury_rate_by_zone[z] || 0) * 100),
                            type: 'bar',
                            marker: {
                              color: ['#fbbf24', '#10b981', '#f97316', '#ef4444']
                            },
                            text: acwrZones.zone_order.map(z => `${((acwrZones.injury_rate_by_zone[z] || 0) * 100).toFixed(1)}%`),
                            textposition: 'outside',
                            textfont: { size: 10, color: '#94a3b8' }
                          }
                        ]}
                        layout={{
                          ...chartLayout,
                          xaxis: { ...chartLayout.xaxis, title: 'ACWR Zone', tickfont: { size: 10 } },
                          yaxis: { ...chartLayout.yaxis, title: 'Injury Rate (%)', tickfont: { size: 10 } },
                          margin: { t: 30, r: 10, b: 60, l: 60 },
                          autosize: true
                        }}
                        useResizeHandler
                        style={{ width: '100%', height: '280px' }}
                        config={{ displayModeBar: false }}
                      />
                      <p className="mt-2 text-xs text-gray-500 dark:text-slate-500 text-center">
                        Higher ACWR zones show elevated injury risk, supporting load management protocols.
                      </p>
                    </Card>
                  </div>
                </div>
              )}

              {/* Statistics */}
              {activeTab === 'stats' && datasetStats && (
                <Card
                  title="Descriptive Statistics Summary"
                  actions={
                    <ExportButton
                      data={[{
                        n_athletes: datasetStats.n_athletes,
                        n_days: datasetStats.n_days,
                        injury_rate: datasetStats.injury_rate,
                        total_injuries: datasetStats.total_injuries,
                        ...METRICS.reduce((acc, m) => {
                          acc[`${m}_mean`] = datasetStats[`${m}_mean`]
                          acc[`${m}_std`] = datasetStats[`${m}_std`]
                          return acc
                        }, {})
                      }]}
                      filename={`dataset_stats_${selectedDataset}`}
                      formats={['csv', 'json']}
                    />
                  }
                >
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mb-6">
                    <StatisticalMetric
                      label="Athletes"
                      value={datasetStats.n_athletes}
                      format="integer"
                      color="blue"
                    />
                    <StatisticalMetric
                      label="Observation Days"
                      value={datasetStats.n_days}
                      format="integer"
                      color="green"
                    />
                    <StatisticalMetric
                      label="Injury Rate"
                      value={datasetStats.injury_rate}
                      format="percent"
                      precision={4}
                      color="red"
                    />
                    <StatisticalMetric
                      label="Total Injuries"
                      value={datasetStats.total_injuries}
                      format="integer"
                      color="purple"
                    />
                  </div>

                  <div className="border-t border-gray-200 dark:border-slate-800 pt-6">
                    <h4 className="font-medium text-sm text-gray-900 dark:text-white mb-4">Biomarker Summary Statistics</h4>
                    <div className="overflow-x-auto">
                      <table className="academic-table">
                        <thead>
                          <tr>
                            <th>Metric</th>
                            <th>Mean (μ)</th>
                            <th>Std Dev (σ)</th>
                            <th>Unit</th>
                          </tr>
                        </thead>
                        <tbody>
                          {METRICS.map(m => {
                            const info = METRIC_DESCRIPTIONS[m]
                            return (
                              <tr key={m}>
                                <td className="font-medium">
                                  {info.methodology ? (
                                    <MethodologyTooltip {...METHODOLOGY_TERMS[info.methodology]}>
                                      {info.full}
                                    </MethodologyTooltip>
                                  ) : info.full}
                                </td>
                                <td className="font-mono">{datasetStats[`${m}_mean`]?.toFixed(2) || 'N/A'}</td>
                                <td className="font-mono text-gray-500 dark:text-slate-500">±{datasetStats[`${m}_std`]?.toFixed(2) || 'N/A'}</td>
                                <td className="text-gray-500 dark:text-slate-500">{info.unit}</td>
                              </tr>
                            )
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </Card>
              )}

              {/* What-If Analysis */}
              {activeTab === 'whatIf' && (
                <div className="space-y-4 sm:space-y-6">
                  <div className="p-4 bg-gray-100 dark:bg-gray-100 dark:bg-slate-800/50 rounded-lg border border-gray-300 dark:border-slate-700">
                    <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">Counterfactual Analysis</h4>
                    <p className="text-xs text-gray-600 dark:text-slate-400">
                      Explore hypothetical intervention scenarios by modifying input features and observing predicted risk changes.
                      This enables "what-if" reasoning for training load optimization and injury prevention strategies.
                    </p>
                  </div>

                  <Card title="Individual Athlete Selection">
                    <div className="grid grid-cols-1 gap-3 sm:gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Trained Model</label>
                        <select
                          value={selectedModel}
                          onChange={e => setSelectedModel(e.target.value)}
                          className="w-full px-3 py-2 bg-gray-100 dark:bg-slate-800 border border-gray-300 dark:border-slate-700 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 text-sm"
                        >
                          <option value="">Select a model...</option>
                          {models
                            .filter(m => m.dataset_id === selectedDataset)
                            .map(m => (
                              <option key={m.id} value={m.id}>{m.model_name} ({m.id.slice(0, 8)}...)</option>
                            ))}
                          {models.filter(m => m.dataset_id === selectedDataset).length === 0 && models.map(m => (
                            <option key={m.id} value={m.id}>{m.model_name} (Different dataset)</option>
                          ))}
                        </select>
                        {models.filter(m => m.dataset_id === selectedDataset).length === 0 && models.length > 0 && (
                          <p className="text-xs text-orange-400 mt-1">No models trained on this dataset.</p>
                        )}
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Athlete ID</label>
                          <select
                            value={selectedAthlete}
                            onChange={e => handleAthleteChange(e.target.value)}
                            className="w-full px-3 py-2 bg-gray-100 dark:bg-slate-800 border border-gray-300 dark:border-slate-700 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 text-sm"
                          >
                            <option value="">Select an athlete...</option>
                            {athletes.map(a => (
                              <option key={a} value={a}>{a}</option>
                            ))}
                          </select>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Reference Date</label>
                          <select
                            value={selectedDate}
                            onChange={e => setSelectedDate(e.target.value)}
                            className="w-full px-3 py-2 bg-gray-100 dark:bg-slate-800 border border-gray-300 dark:border-slate-700 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 text-sm"
                            disabled={!athleteTimeline}
                          >
                            <option value="">Select a date...</option>
                            {athleteTimeline?.dates.map(d => (
                              <option key={d} value={d}>{new Date(d).toLocaleDateString()}</option>
                            ))}
                          </select>
                        </div>
                      </div>
                    </div>
                  </Card>

                  {/* Athlete Stats */}
                  {selectedAthlete && athleteTimeline && (
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-4">
                      <StatisticalMetric
                        label="Total Injuries"
                        value={athleteTimeline.injury_days?.length || 0}
                        format="integer"
                        color="red"
                        size="small"
                      />
                      <StatisticalMetric
                        label="Avg. Stress"
                        value={athleteTimeline.metrics?.stress?.reduce((a,b) => a+b, 0) / athleteTimeline.metrics?.stress?.length || 0}
                        precision={1}
                        color="orange"
                        size="small"
                      />
                      <StatisticalMetric
                        label="Avg. Sleep"
                        value={athleteTimeline.metrics?.sleep_hours?.reduce((a,b) => a+b, 0) / athleteTimeline.metrics?.sleep_hours?.length || 0}
                        precision={1}
                        color="blue"
                        size="small"
                      />
                      <StatisticalMetric
                        label="Avg. TSS"
                        value={athleteTimeline.metrics?.actual_tss?.reduce((a,b) => a+b, 0) / athleteTimeline.metrics?.actual_tss?.length || 0}
                        precision={1}
                        color="purple"
                        size="small"
                      />
                    </div>
                  )}

                  {selectedModel && selectedAthlete && selectedDate ? (
                    <InterventionSimulator
                      modelId={selectedModel}
                      athleteId={selectedAthlete}
                      date={selectedDate}
                      currentMetrics={{
                        sleep_hours: athleteTimeline?.metrics?.sleep_hours?.[athleteTimeline.dates.indexOf(selectedDate)] || 7.5,
                        duration_minutes: athleteTimeline?.metrics?.duration_minutes?.[athleteTimeline.dates.indexOf(selectedDate)] || 60,
                        intensity_factor: athleteTimeline?.metrics?.intensity_factor?.[athleteTimeline.dates.indexOf(selectedDate)] || 1.0,
                        stress: athleteTimeline?.metrics?.stress?.[athleteTimeline.dates.indexOf(selectedDate)] || 50
                      }}
                    />
                  ) : (
                    <div className="p-8 sm:p-12 text-center border-2 border-dashed border-gray-300 dark:border-slate-700 rounded-xl text-gray-500 dark:text-slate-500 text-sm">
                      <svg className="w-12 h-12 mx-auto mb-4 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Select a Model, Athlete, and Date above to begin counterfactual analysis.
                    </div>
                  )}
                </div>
              )}

            </>
          )}

          {/* Reproducibility Panel */}
          <ReproducibilityPanel
            datasetId={selectedDataset}
            config={{
              analysis_tab: activeTab,
              metrics_analyzed: METRICS
            }}
          />
        </>
      )}
    </div>
  )
}

export default AnalyticsPage
