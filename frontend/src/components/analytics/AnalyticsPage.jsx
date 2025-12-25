import { useState, useEffect } from 'react'
import Plot from 'react-plotly.js'
import { usePipeline } from '../../context/PipelineContext'
import { analyticsApi, trainingApi } from '../../api'
import Card from '../common/Card'
import InterventionSimulator from './InterventionSimulator'

const METRICS = ['hrv', 'resting_hr', 'sleep_hours', 'sleep_quality', 'stress', 'body_battery_morning', 'actual_tss']

function AnalyticsPage() {
  const { datasets, currentDataset, setCurrentDataset, refreshDatasets } = usePipeline()

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
      setAthletes(res.data.athletes)
    } catch (error) {
      console.error('Failed to fetch athletes:', error)
    }
  }

  const fetchModels = async () => {
    try {
      const res = await trainingApi.listModels()
      setModels(res.data.models)
    } catch (error) {
      console.error('Failed to fetch models:', error)
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
          const distPromises = METRICS.map(m =>
            analyticsApi.getDistribution(selectedDataset, m).then(r => ({ metric: m, data: r.data }))
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
    { id: 'distributions', label: 'Distributions' },
    { id: 'correlations', label: 'Correlations' },
    { id: 'preInjury', label: 'Pre-Injury Window' },
    { id: 'acwr', label: 'ACWR Zones' },
    { id: 'stats', label: 'Statistics' },
    { id: 'whatIf', label: 'What-If Analysis' }
  ]

  return (
    <div className="space-y-4 sm:space-y-6">
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Analytics</h1>
        <p className="text-sm sm:text-base text-gray-600 mt-1">Explore and visualize dataset patterns</p>
      </div>

      {/* Dataset Selection */}
      <Card>
        <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
          <label className="text-sm font-medium text-gray-700">Dataset:</label>
          <select
            value={selectedDataset}
            onChange={e => {
              setSelectedDataset(e.target.value)
              setCurrentDataset(e.target.value)
            }}
            className="flex-1 sm:flex-none px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm sm:text-base"
          >
            <option value="">Select a dataset...</option>
            {datasets.map(ds => (
              <option key={ds.id} value={ds.id}>
                {ds.id} ({ds.n_athletes} athletes)
              </option>
            ))}
          </select>
        </div>
      </Card>

      {selectedDataset && (
        <>
          {/* Tabs */}
          <div className="border-b border-gray-200 -mx-4 px-4 sm:mx-0 sm:px-0 overflow-x-auto">
            <nav className="flex space-x-4 sm:space-x-8 min-w-max">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-3 sm:py-4 px-1 border-b-2 font-medium text-xs sm:text-sm whitespace-nowrap ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
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
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                  {Object.entries(distributions).map(([metric, data]) => (
                    <Card key={metric} title={metric.replace('_', ' ').toUpperCase()}>
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
                          xaxis: { title: metric, tickfont: { size: 10 } },
                          yaxis: { title: 'Count', tickfont: { size: 10 } },
                          margin: { t: 10, r: 10, b: 40, l: 40 },
                          autosize: true,
                          annotations: [
                            {
                              x: data.mean,
                              y: Math.max(...data.histogram) * 0.9,
                              text: `Mean: ${data.mean.toFixed(2)}`,
                              showarrow: true,
                              arrowhead: 2,
                              font: { size: 10 }
                            }
                          ]
                        }}
                        useResizeHandler
                        style={{ width: '100%', height: '250px' }}
                        config={{ displayModeBar: false }}
                      />
                    </Card>
                  ))}
                </div>
              )}

              {/* Correlations */}
              {activeTab === 'correlations' && correlations && (
                <Card title="Correlation Heatmap">
                  <div className="-mx-2 sm:mx-0 overflow-x-auto">
                    <Plot
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
                          textfont: { size: 8 },
                          hovertemplate: '%{x} vs %{y}: %{z:.3f}<extra></extra>'
                        }
                      ]}
                      layout={{
                        margin: { t: 30, r: 30, b: 80, l: 80 },
                        autosize: true,
                        xaxis: { tickfont: { size: 9 }, tickangle: 45 },
                        yaxis: { tickfont: { size: 9 } }
                      }}
                      useResizeHandler
                      style={{ width: '100%', minWidth: '350px', height: '400px' }}
                      config={{ displayModeBar: false }}
                    />
                  </div>
                </Card>
              )}

              {/* Pre-Injury Window */}
              {activeTab === 'preInjury' && preInjury && (
                <Card title={`Pre-Injury Window Analysis (${preInjury.n_injuries} injuries)`}>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                    {Object.entries(preInjury.metrics || {}).map(([metric, data]) => (
                      <div key={metric}>
                        <h4 className="font-medium text-sm sm:text-base mb-2">{metric.replace('_', ' ').toUpperCase()}</h4>
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
                            xaxis: { title: 'Days Before Injury', zeroline: true, tickfont: { size: 10 } },
                            yaxis: { title: metric, tickfont: { size: 10 } },
                            margin: { t: 10, r: 10, b: 40, l: 50 },
                            autosize: true,
                            shapes: [
                              {
                                type: 'line',
                                x0: 0, x1: 0,
                                y0: Math.min(...data.average.filter(v => v !== null)),
                                y1: Math.max(...data.average.filter(v => v !== null)),
                                line: { color: 'red', width: 2, dash: 'dash' }
                              }
                            ]
                          }}
                          useResizeHandler
                          style={{ width: '100%', height: '220px' }}
                          config={{ displayModeBar: false }}
                        />
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* ACWR Zones */}
              {activeTab === 'acwr' && acwrZones && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                  <Card title="ACWR Zone Distribution">
                    <Plot
                      data={[
                        {
                          values: Object.values(acwrZones.zone_distribution),
                          labels: Object.keys(acwrZones.zone_distribution),
                          type: 'pie',
                          marker: {
                            colors: ['#fbbf24', '#10b981', '#f97316', '#ef4444']
                          },
                          textfont: { size: 11 }
                        }
                      ]}
                      layout={{
                        margin: { t: 10, r: 10, b: 10, l: 10 },
                        autosize: true,
                        showlegend: true,
                        legend: { font: { size: 10 }, orientation: 'h', y: -0.1 }
                      }}
                      useResizeHandler
                      style={{ width: '100%', height: '280px' }}
                      config={{ displayModeBar: false }}
                    />
                  </Card>

                  <Card title="Injury Rate by ACWR Zone">
                    <Plot
                      data={[
                        {
                          x: acwrZones.zone_order,
                          y: acwrZones.zone_order.map(z => (acwrZones.injury_rate_by_zone[z] || 0) * 100),
                          type: 'bar',
                          marker: {
                            color: ['#fbbf24', '#10b981', '#f97316', '#ef4444']
                          }
                        }
                      ]}
                      layout={{
                        xaxis: { title: 'ACWR Zone', tickfont: { size: 10 } },
                        yaxis: { title: 'Injury Rate (%)', tickfont: { size: 10 } },
                        margin: { t: 10, r: 10, b: 60, l: 50 },
                        autosize: true
                      }}
                      useResizeHandler
                      style={{ width: '100%', height: '280px' }}
                      config={{ displayModeBar: false }}
                    />
                  </Card>
                </div>
              )}

              {/* Statistics */}
              {activeTab === 'stats' && datasetStats && (
                <Card title="Dataset Statistics">
                  <div className="grid grid-cols-2 gap-2 sm:gap-4">
                    <div className="text-center p-3 sm:p-4 bg-blue-50 rounded-lg">
                      <p className="text-xl sm:text-2xl font-bold text-blue-600">{datasetStats.n_athletes}</p>
                      <p className="text-xs sm:text-sm text-gray-500">Athletes</p>
                    </div>
                    <div className="text-center p-3 sm:p-4 bg-green-50 rounded-lg">
                      <p className="text-xl sm:text-2xl font-bold text-green-600">
                        {datasetStats.n_days?.toLocaleString()}
                      </p>
                      <p className="text-xs sm:text-sm text-gray-500">Total Days</p>
                    </div>
                    <div className="text-center p-3 sm:p-4 bg-red-50 rounded-lg">
                      <p className="text-xl sm:text-2xl font-bold text-red-600">
                        {(datasetStats.injury_rate * 100).toFixed(2)}%
                      </p>
                      <p className="text-xs sm:text-sm text-gray-500">Injury Rate</p>
                    </div>
                    <div className="text-center p-3 sm:p-4 bg-purple-50 rounded-lg">
                      <p className="text-xl sm:text-2xl font-bold text-purple-600">
                        {datasetStats.total_injuries?.toLocaleString()}
                      </p>
                      <p className="text-xs sm:text-sm text-gray-500">Total Injuries</p>
                    </div>
                  </div>

                  <div className="mt-4 sm:mt-6">
                    <h4 className="font-medium text-sm sm:text-base mb-3 sm:mb-4">Metric Averages</h4>
                    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2 sm:gap-4">
                      {METRICS.map(m => (
                        <div key={m} className="p-2 sm:p-3 bg-gray-50 rounded-lg">
                          <p className="text-base sm:text-lg font-semibold">
                            {datasetStats[`${m}_mean`]?.toFixed(2) || 'N/A'}
                          </p>
                          <p className="text-xs text-gray-500 truncate">
                            {m.replace('_', ' ')} (±{datasetStats[`${m}_std`]?.toFixed(2) || 'N/A'})
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                </Card>
              )}

              {/* What-If Analysis */}
              {activeTab === 'whatIf' && (
                <div className="space-y-4 sm:space-y-6">
                  <Card title="Individual Athlete Analysis">
                    <div className="grid grid-cols-1 gap-3 sm:gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
                        <select
                          value={selectedModel}
                          onChange={e => setSelectedModel(e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                        >
                          <option value="">Select a model...</option>
                          {models
                            .filter(m => m.dataset_id === selectedDataset)
                            .map(m => (
                              <option key={m.id} value={m.id}>{m.id} ({m.model_name})</option>
                            ))}
                          {models.filter(m => m.dataset_id === selectedDataset).length === 0 && models.map(m => (
                             <option key={m.id} value={m.id}>{m.id} (Dataset Mismatch: {m.dataset_id})</option>
                          ))}
                        </select>
                        {models.filter(m => m.dataset_id === selectedDataset).length === 0 && models.length > 0 && (
                          <p className="text-xs text-orange-600 mt-1">No models found for this dataset.</p>
                        )}
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Athlete</label>
                          <select
                            value={selectedAthlete}
                            onChange={e => handleAthleteChange(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                          >
                            <option value="">Select an athlete...</option>
                            {athletes.map(a => (
                              <option key={a} value={a}>{a}</option>
                            ))}
                          </select>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
                          <select
                            value={selectedDate}
                            onChange={e => setSelectedDate(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
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
                      <div className="p-3 sm:p-4 bg-white border border-gray-200 rounded-xl shadow-sm">
                        <p className="text-xs sm:text-sm text-gray-500">Total Injuries</p>
                        <p className="text-xl sm:text-2xl font-bold text-red-600">{athleteTimeline.injury_days?.length || 0}</p>
                      </div>
                      <div className="p-3 sm:p-4 bg-white border border-gray-200 rounded-xl shadow-sm">
                        <p className="text-xs sm:text-sm text-gray-500">Avg. Stress</p>
                        <p className="text-xl sm:text-2xl font-bold text-orange-600">
                          {(athleteTimeline.metrics?.stress?.reduce((a,b) => a+b, 0) / athleteTimeline.metrics?.stress?.length || 0).toFixed(1)}
                        </p>
                      </div>
                      <div className="p-3 sm:p-4 bg-white border border-gray-200 rounded-xl shadow-sm">
                        <p className="text-xs sm:text-sm text-gray-500">Avg. Sleep</p>
                        <p className="text-xl sm:text-2xl font-bold text-blue-600">
                          {(athleteTimeline.metrics?.sleep_hours?.reduce((a,b) => a+b, 0) / athleteTimeline.metrics?.sleep_hours?.length || 0).toFixed(1)}h
                        </p>
                      </div>
                      <div className="p-3 sm:p-4 bg-white border border-gray-200 rounded-xl shadow-sm">
                        <p className="text-xs sm:text-sm text-gray-500">Avg. TSS</p>
                        <p className="text-xl sm:text-2xl font-bold text-purple-600">
                          {(athleteTimeline.metrics?.actual_tss?.reduce((a,b) => a+b, 0) / athleteTimeline.metrics?.actual_tss?.length || 0).toFixed(1)}
                        </p>
                      </div>
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
                    <div className="p-8 sm:p-12 text-center border-2 border-dashed border-gray-200 rounded-xl text-gray-400 text-sm sm:text-base">
                      Select a Model, Athlete, and Date above to start counterfactual analysis.
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </>
      )}
    </div>
  )
}

export default AnalyticsPage
