import { useState, useEffect } from 'react'
import Plot from 'react-plotly.js'
import Card from '../common/Card'
import { validationApi } from '../../api'

function ValidationPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [summary, setSummary] = useState(null)
  const [causalData, setCausalData] = useState(null)
  const [threePillars, setThreePillars] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    loadValidationData()
  }, [])

  const loadValidationData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [summaryRes, causalRes, pillarsRes] = await Promise.all([
        validationApi.getSummary(),
        validationApi.getCausalMechanism().catch(() => ({ data: null })),
        validationApi.getThreePillars().catch(() => ({ data: null }))
      ])
      setSummary(summaryRes.data)
      setCausalData(causalRes.data)
      setThreePillars(pillarsRes.data)
    } catch (err) {
      console.error('Failed to load validation data:', err)
      setError(err.response?.data?.error || 'Failed to load validation data')
    } finally {
      setLoading(false)
    }
  }

  const getScoreColor = (score) => {
    if (score >= 0.7) return 'text-green-600'
    if (score >= 0.4) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getStatusColor = (status) => {
    if (status === 'PASS') return 'bg-green-100 text-green-800'
    if (status === 'WARNING') return 'bg-yellow-100 text-yellow-800'
    return 'bg-red-100 text-red-800'
  }

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'causal', label: 'Causal Mechanism' },
    { id: 'distributions', label: 'Distributions' },
    { id: 'sim2real', label: 'Sim2Real' },
    { id: 'pmdata', label: 'PMData Analysis' }
  ]

  const getPillarColor = (status) => {
    if (status === 'pass') return 'bg-green-100 text-green-800 border-green-200'
    if (status === 'warning') return 'bg-yellow-100 text-yellow-800 border-yellow-200'
    return 'bg-red-100 text-red-800 border-red-200'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading validation data...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-4">
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Data Validation</h1>
        <Card>
          <div className="text-center py-8">
            <p className="text-red-600 mb-4">{error}</p>
            <p className="text-gray-500 text-sm">
              Make sure you have both synthetic data and PMData available.
            </p>
            <button
              onClick={loadValidationData}
              className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Retry
            </button>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Data Validation</h1>
        <p className="text-sm sm:text-base text-gray-600 mt-1">
          Compare synthetic data against real PMData (Sim2Real Transfer)
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 overflow-x-auto">
        <nav className="flex space-x-4 sm:space-x-8 min-w-max px-1">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-xs sm:text-sm whitespace-nowrap ${
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

      {/* Overview Tab */}
      {activeTab === 'overview' && summary && (
        <div className="space-y-4">
          {/* Score Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card>
              <div className="text-center py-4">
                <p className={`text-3xl sm:text-4xl font-bold ${getScoreColor(summary.overall_score)}`}>
                  {(summary.overall_score * 100).toFixed(0)}%
                </p>
                <p className="text-sm text-gray-500 mt-1">Overall Score</p>
              </div>
            </Card>
            <Card>
              <div className="text-center py-4">
                <p className={`text-3xl sm:text-4xl font-bold ${getScoreColor(summary.alignment_score)}`}>
                  {(summary.alignment_score * 100).toFixed(0)}%
                </p>
                <p className="text-sm text-gray-500 mt-1">Distribution Alignment</p>
                <p className="text-xs text-gray-400">JS Div: {summary.avg_js_divergence?.toFixed(3)}</p>
              </div>
            </Card>
            <Card>
              <div className="text-center py-4">
                <p className={`text-3xl sm:text-4xl font-bold ${getScoreColor(summary.transfer_score)}`}>
                  {summary.sim2real_auc?.toFixed(3)}
                </p>
                <p className="text-sm text-gray-500 mt-1">Sim2Real AUC</p>
                <p className="text-xs text-gray-400">
                  {summary.sim2real_auc > 0.55 ? 'Good Transfer' : 'Needs Improvement'}
                </p>
              </div>
            </Card>
          </div>

          {/* Quick Summary */}
          <Card title="Validation Summary">
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <span className="text-sm font-medium">Synthetic Samples</span>
                <span className="text-sm text-gray-600">
                  {summary.distributions?.synthetic_samples?.toLocaleString() || 'N/A'}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <span className="text-sm font-medium">Real PMData Samples</span>
                <span className="text-sm text-gray-600">
                  {summary.distributions?.real_samples?.toLocaleString() || 'N/A'}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <span className="text-sm font-medium">PMData Injury Rate</span>
                <span className="text-sm text-gray-600">
                  {((summary.pmdata_analysis?.injury_rate || 0) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <span className="text-sm font-medium">Transfer Status</span>
                <span className={`text-sm px-2 py-1 rounded ${
                  summary.sim2real?.status === 'success' ? 'bg-green-100 text-green-800' :
                  summary.sim2real?.status === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {summary.sim2real?.interpretation || 'Unknown'}
                </span>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Causal Mechanism Tab */}
      {activeTab === 'causal' && (
        <div className="space-y-4">
          {/* Three Pillars Summary */}
          {threePillars && (
            <Card title="Three Pillars of Validity">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                {/* Statistical Fidelity */}
                <div className={`p-4 rounded-lg border ${getPillarColor(threePillars.pillars?.statistical_fidelity?.status)}`}>
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold">Statistical Fidelity</h4>
                    <span className="text-xs uppercase font-bold">
                      {threePillars.pillars?.statistical_fidelity?.status || 'pending'}
                    </span>
                  </div>
                  <p className="text-2xl font-bold mb-1">
                    {((threePillars.pillars?.statistical_fidelity?.score || 0) * 100).toFixed(0)}%
                  </p>
                  <p className="text-xs opacity-75">
                    JS Div: {threePillars.pillars?.statistical_fidelity?.avg_js_divergence?.toFixed(4) || 'N/A'}
                  </p>
                  <p className="text-xs mt-1 opacity-60">Target: JS &lt; 0.1</p>
                </div>

                {/* Causal Fidelity */}
                <div className={`p-4 rounded-lg border ${getPillarColor(threePillars.pillars?.causal_fidelity?.status)}`}>
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold">Causal Fidelity</h4>
                    <span className="text-xs uppercase font-bold">
                      {threePillars.pillars?.causal_fidelity?.status || 'pending'}
                    </span>
                  </div>
                  <p className="text-2xl font-bold mb-1">
                    {threePillars.pillars?.causal_fidelity?.undertrained_risk_ratio?.toFixed(1) || '?'}x
                  </p>
                  <p className="text-xs opacity-75">
                    Undertrained vs Optimal risk ratio
                  </p>
                  <p className="text-xs mt-1 opacity-60">Target: 2-3x higher</p>
                </div>

                {/* Transferability */}
                <div className={`p-4 rounded-lg border ${getPillarColor(threePillars.pillars?.transferability?.status)}`}>
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold">Transferability</h4>
                    <span className="text-xs uppercase font-bold">
                      {threePillars.pillars?.transferability?.status || 'pending'}
                    </span>
                  </div>
                  <p className="text-2xl font-bold mb-1">
                    {threePillars.pillars?.transferability?.sim2real_auc?.toFixed(3) || '?'}
                  </p>
                  <p className="text-xs opacity-75">Sim2Real AUC</p>
                  <p className="text-xs mt-1 opacity-60">Target: AUC &gt; 0.60</p>
                </div>
              </div>

              {/* Overall Status */}
              <div className={`p-4 rounded-lg ${threePillars.ready_for_publication ? 'bg-green-50 border border-green-200' : 'bg-amber-50 border border-amber-200'}`}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold">
                      {threePillars.ready_for_publication ? 'Ready for Publication' : 'Needs Improvement'}
                    </p>
                    <p className="text-sm opacity-75">
                      {threePillars.pillars_passing} pillars passing
                    </p>
                  </div>
                  <span className="text-3xl font-bold">
                    {(threePillars.overall_score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </Card>
          )}

          {/* Causal Asymmetry Chart (The Paper's Main Finding) */}
          {causalData?.causal_asymmetry?.zones && (
            <Card title="Causal Asymmetry: Risk per Load Unit by ACWR Zone">
              <Plot
                data={[{
                  x: causalData.causal_asymmetry.zones.map(z => z.zone),
                  y: causalData.causal_asymmetry.zones.map(z => z.risk_per_load),
                  type: 'bar',
                  marker: {
                    color: causalData.causal_asymmetry.zones.map(z =>
                      z.zone === 'Optimal' ? '#22c55e' :
                      z.zone === 'Undertrained' ? '#ef4444' :
                      z.zone === 'High Risk' ? '#f97316' : '#eab308'
                    )
                  },
                  text: causalData.causal_asymmetry.zones.map(z => `${z.relative_risk}x`),
                  textposition: 'outside',
                  textfont: { size: 14, color: '#374151' }
                }]}
                layout={{
                  height: 350,
                  margin: { t: 40, r: 20, b: 60, l: 60 },
                  xaxis: { title: 'ACWR Zone' },
                  yaxis: { title: 'Injuries per 10,000 TSS Units' },
                  showlegend: false,
                  annotations: [{
                    x: 0.5,
                    y: -0.15,
                    xref: 'paper',
                    yref: 'paper',
                    text: causalData.causal_asymmetry.summary?.interpretation || '',
                    showarrow: false,
                    font: { size: 11, color: '#6b7280' },
                    align: 'center'
                  }]
                }}
                config={{ displayModeBar: false, responsive: true }}
                style={{ width: '100%' }}
              />
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-4">
                {causalData.causal_asymmetry.zones.map(zone => (
                  <div key={zone.zone} className="text-center p-2 bg-gray-50 rounded text-xs">
                    <p className="font-medium">{zone.zone}</p>
                    <p>{zone.total_injuries} injuries / {zone.total_days} days</p>
                    <p className="text-gray-500">{zone.injury_rate_pct}% daily rate</p>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Risk Landscape Contour */}
          {causalData?.risk_landscape?.risk_grid && (
            <Card title="Risk Landscape: Acute vs Chronic Load">
              <Plot
                data={[{
                  z: causalData.risk_landscape.risk_grid,
                  x: causalData.risk_landscape.chronic_values,
                  y: causalData.risk_landscape.acute_values,
                  type: 'contour',
                  colorscale: 'RdYlGn',
                  reversescale: true,
                  contours: { showlabels: true, labelfont: { size: 10 } },
                  colorbar: { title: 'Injury Prob', titleside: 'right' }
                },
                // ACWR reference lines
                {
                  x: causalData.risk_landscape.acwr_lines?.x || [],
                  y: causalData.risk_landscape.acwr_lines?.['acwr_0.8'] || [],
                  type: 'scatter',
                  mode: 'lines',
                  name: 'ACWR 0.8',
                  line: { dash: 'dash', color: 'white', width: 2 }
                },
                {
                  x: causalData.risk_landscape.acwr_lines?.x || [],
                  y: causalData.risk_landscape.acwr_lines?.['acwr_1.3'] || [],
                  type: 'scatter',
                  mode: 'lines',
                  name: 'ACWR 1.3',
                  line: { dash: 'dash', color: 'white', width: 2 }
                }]}
                layout={{
                  height: 400,
                  margin: { t: 30, r: 100, b: 60, l: 60 },
                  xaxis: { title: 'Chronic Load (Fitness)' },
                  yaxis: { title: 'Acute Load (Fatigue)' },
                  showlegend: true,
                  legend: { x: 0, y: 1.1, orientation: 'h' }
                }}
                config={{ displayModeBar: false, responsive: true }}
                style={{ width: '100%' }}
              />
              <p className="text-xs text-gray-500 mt-2 text-center">
                The "Sweet Spot" (green) is where ACWR is 0.8-1.3. Red zones indicate elevated risk.
              </p>
            </Card>
          )}

          {/* Load Scenario Analysis */}
          {causalData?.load_scenarios?.scenarios && (
            <Card title="Injury Risk by Training Scenario">
              <Plot
                data={[{
                  x: causalData.load_scenarios.scenarios.map(s => s.scenario),
                  y: causalData.load_scenarios.scenarios.map(s => s.injury_rate * 100),
                  type: 'bar',
                  marker: {
                    color: causalData.load_scenarios.scenarios.map(s =>
                      s.scenario === causalData.load_scenarios.highest_risk_scenario ? '#ef4444' :
                      s.scenario === causalData.load_scenarios.lowest_risk_scenario ? '#22c55e' : '#3b82f6'
                    )
                  }
                }]}
                layout={{
                  height: 280,
                  margin: { t: 20, r: 20, b: 80, l: 50 },
                  xaxis: { title: 'Training Scenario', tickangle: -45 },
                  yaxis: { title: 'Injury Rate (%)' },
                  showlegend: false
                }}
                config={{ displayModeBar: false, responsive: true }}
                style={{ width: '100%' }}
              />
              <div className="flex justify-center gap-4 mt-2 text-xs">
                <span className="flex items-center gap-1">
                  <span className="w-3 h-3 bg-red-500 rounded"></span>
                  Highest Risk: {causalData.load_scenarios.highest_risk_scenario}
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-3 h-3 bg-green-500 rounded"></span>
                  Lowest Risk: {causalData.load_scenarios.lowest_risk_scenario}
                </span>
              </div>
            </Card>
          )}

          {/* Injury Type Breakdown */}
          {causalData?.injury_types?.breakdown && (
            <Card title="Injury Mechanism Breakdown">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Plot
                  data={[{
                    labels: causalData.injury_types.breakdown.map(t => t.type),
                    values: causalData.injury_types.breakdown.map(t => t.count),
                    type: 'pie',
                    marker: {
                      colors: ['#ef4444', '#f97316', '#3b82f6', '#8b5cf6']
                    },
                    textinfo: 'label+percent',
                    hole: 0.4
                  }]}
                  layout={{
                    height: 250,
                    margin: { t: 20, r: 20, b: 20, l: 20 },
                    showlegend: false
                  }}
                  config={{ displayModeBar: false, responsive: true }}
                  style={{ width: '100%' }}
                />
                <div className="space-y-2">
                  {causalData.injury_types.breakdown.map(type => (
                    <div key={type.type} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                      <div>
                        <span className="font-medium capitalize">{type.type}</span>
                        <span className="text-xs text-gray-500 ml-2">({type.percentage}%)</span>
                      </div>
                      <span className="text-lg font-bold">{type.count}</span>
                    </div>
                  ))}
                  <div className="pt-2 border-t">
                    <div className="flex justify-between text-sm">
                      <span className="font-medium">Total Injuries</span>
                      <span className="font-bold">{causalData.injury_types.total_injuries}</span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      Dominant mechanism: <span className="font-medium">{causalData.injury_types.dominant_mechanism}</span>
                    </p>
                  </div>
                </div>
              </div>
            </Card>
          )}

          {/* No Data Warning */}
          {!causalData?.causal_asymmetry?.zones && (
            <Card>
              <div className="text-center py-8">
                <div className="w-16 h-16 rounded-full bg-amber-100 flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Glass-Box Data Required</h3>
                <p className="text-gray-600 mb-4">
                  Regenerate synthetic data to include causal mechanism columns (ACWR, injury_type, wellness_vulnerability).
                </p>
                <a
                  href="/data-generation"
                  className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  Regenerate Synthetic Cohort
                </a>
              </div>
            </Card>
          )}
        </div>
      )}

      {/* Distributions Tab */}
      {activeTab === 'distributions' && (
        <div className="space-y-4">
          {/* Show message if no synthetic data */}
          {(!summary?.distributions?.features || summary?.distributions?.error) && (
            <Card>
              <div className="text-center py-8">
                <div className="w-16 h-16 rounded-full bg-amber-100 flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">No Synthetic Data Available</h3>
                <p className="text-gray-600 mb-4">
                  Generate a synthetic cohort to compare distributions with real PMData.
                </p>
                <a
                  href="/data-generation"
                  className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  Generate Synthetic Cohort
                </a>
              </div>
            </Card>
          )}

          {/* Show distributions if available */}
          {summary?.distributions?.features && !summary?.distributions?.error && (
            <>
              {/* Distribution Status Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {Object.entries(summary.distributions.features).map(([feat, data]) => (
                  <Card key={feat}>
                    <div className="text-center py-2">
                      <p className="text-xs text-gray-500 truncate">{feat.replace('_', ' ')}</p>
                      <p className="text-lg font-bold mt-1">
                        {data.js_divergence?.toFixed(3) || 'N/A'}
                      </p>
                      <span className={`text-xs px-2 py-0.5 rounded ${getStatusColor(data.status)}`}>
                        {data.status || 'N/A'}
                      </span>
                    </div>
                  </Card>
                ))}
              </div>

              {/* Distribution Charts */}
              {Object.entries(summary.distributions.features).map(([feat, data]) => {
                if (!data.bins || !data.synthetic?.histogram) return null

                const binCenters = data.bins.slice(0, -1).map((b, i) =>
                  (b + data.bins[i + 1]) / 2
                )

                return (
                  <Card key={feat} title={`${feat.replace(/_/g, ' ')} Distribution`}>
                    <Plot
                      data={[
                        {
                          x: binCenters,
                          y: data.synthetic.histogram,
                          type: 'bar',
                          name: 'Synthetic',
                          marker: { color: 'rgba(59, 130, 246, 0.7)' },
                          width: 0.02
                        },
                        {
                          x: binCenters,
                          y: data.real.histogram,
                          type: 'bar',
                          name: 'Real (PMData)',
                          marker: { color: 'rgba(239, 68, 68, 0.7)' },
                          width: 0.02
                        }
                      ]}
                      layout={{
                        barmode: 'overlay',
                        height: 250,
                        margin: { t: 30, r: 20, b: 40, l: 50 },
                        xaxis: { title: feat.replace(/_/g, ' '), range: [0, 1] },
                        yaxis: { title: 'Density' },
                        legend: { orientation: 'h', y: 1.1 },
                        annotations: [{
                          x: 0.95,
                          y: 0.95,
                          xref: 'paper',
                          yref: 'paper',
                          text: `JS: ${data.js_divergence?.toFixed(3)}`,
                          showarrow: false,
                          bgcolor: data.status === 'PASS' ? '#dcfce7' : '#fef3c7',
                          borderpad: 4
                        }]
                      }}
                      config={{ displayModeBar: false, responsive: true }}
                      style={{ width: '100%' }}
                    />
                    <div className="grid grid-cols-2 gap-4 mt-2 text-xs">
                      <div className="bg-blue-50 p-2 rounded">
                        <p className="font-medium text-blue-800">Synthetic</p>
                        <p>Mean: {data.synthetic.mean?.toFixed(3)}, Std: {data.synthetic.std?.toFixed(3)}</p>
                      </div>
                      <div className="bg-red-50 p-2 rounded">
                        <p className="font-medium text-red-800">Real (PMData)</p>
                        <p>Mean: {data.real.mean?.toFixed(3)}, Std: {data.real.std?.toFixed(3)}</p>
                      </div>
                    </div>
                  </Card>
                )
              })}
            </>
          )}
        </div>
      )}

      {/* Sim2Real Tab */}
      {activeTab === 'sim2real' && (
        <div className="space-y-4">
          {/* Show message if no synthetic data */}
          {summary?.sim2real?.error && (
            <Card>
              <div className="text-center py-8">
                <div className="w-16 h-16 rounded-full bg-amber-100 flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Sim2Real Requires Synthetic Data</h3>
                <p className="text-gray-600 mb-4">
                  Generate a synthetic cohort first, then this tab will train on synthetic data and evaluate on real PMData.
                </p>
                <a
                  href="/data-generation"
                  className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  Generate Synthetic Cohort
                </a>
              </div>
            </Card>
          )}

          {/* Show Sim2Real results if available */}
          {summary?.sim2real && !summary?.sim2real?.error && (
            <>
              <Card title="Sim2Real Transfer Learning Results">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
                  <div className="text-center p-4 bg-gray-50 rounded">
                    <p className="text-2xl font-bold text-blue-600">
                      {summary.sim2real.auc?.toFixed(4)}
                    </p>
                    <p className="text-sm text-gray-500">AUC Score</p>
                  </div>
                  <div className="text-center p-4 bg-gray-50 rounded">
                    <p className="text-2xl font-bold text-green-600">
                      {summary.sim2real.ap?.toFixed(4)}
                    </p>
                    <p className="text-sm text-gray-500">Avg Precision</p>
                  </div>
                  <div className="text-center p-4 bg-gray-50 rounded">
                    <p className="text-2xl font-bold text-purple-600">
                      {summary.sim2real.n_train?.toLocaleString()}
                    </p>
                    <p className="text-sm text-gray-500">Train Samples</p>
                  </div>
                  <div className="text-center p-4 bg-gray-50 rounded">
                    <p className="text-2xl font-bold text-orange-600">
                      {summary.sim2real.n_test?.toLocaleString()}
                    </p>
                    <p className="text-sm text-gray-500">Test Samples</p>
                  </div>
                </div>

                <div className={`p-4 rounded ${
                  summary.sim2real.status === 'success' ? 'bg-green-50 border border-green-200' :
                  summary.sim2real.status === 'warning' ? 'bg-yellow-50 border border-yellow-200' :
                  'bg-red-50 border border-red-200'
                }`}>
                  <p className="font-medium">{summary.sim2real.interpretation}</p>
                </div>

                {summary.sim2real.features_used && (
                  <div className="mt-4">
                    <p className="text-sm font-medium text-gray-700 mb-2">Features Used:</p>
                    <div className="flex flex-wrap gap-2">
                      {summary.sim2real.features_used.map(feat => (
                        <span key={feat} className="px-2 py-1 bg-gray-100 rounded text-sm">
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
                  <div className="flex items-center gap-3 p-2 rounded bg-green-50">
                    <span className="font-mono font-bold text-green-700">0.60+</span>
                    <span className="text-green-800">Good - Synthetic data captures real injury patterns</span>
                  </div>
                  <div className="flex items-center gap-3 p-2 rounded bg-yellow-50">
                    <span className="font-mono font-bold text-yellow-700">0.55</span>
                    <span className="text-yellow-800">Moderate - Some signal transfers, more tuning needed</span>
                  </div>
                  <div className="flex items-center gap-3 p-2 rounded bg-red-50">
                    <span className="font-mono font-bold text-red-700">0.50</span>
                    <span className="text-red-800">Poor - No better than random, distributions/signals misaligned</span>
                  </div>
                </div>
              </Card>
            </>
          )}
        </div>
      )}

      {/* PMData Analysis Tab */}
      {activeTab === 'pmdata' && summary?.pmdata_analysis && (
        <div className="space-y-4">
          {/* PMData Stats */}
          <Card title="PMData Overview">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="text-center p-3 bg-gray-50 rounded">
                <p className="text-xl font-bold">{summary.pmdata_analysis.samples?.toLocaleString()}</p>
                <p className="text-xs text-gray-500">Total Samples</p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded">
                <p className="text-xl font-bold">{summary.pmdata_analysis.safe_days?.toLocaleString()}</p>
                <p className="text-xs text-gray-500">Safe Days</p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded">
                <p className="text-xl font-bold">{summary.pmdata_analysis.preinjury_days?.toLocaleString()}</p>
                <p className="text-xs text-gray-500">Pre-Injury Days</p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded">
                <p className="text-xl font-bold">{((summary.pmdata_analysis.injury_rate || 0) * 100).toFixed(1)}%</p>
                <p className="text-xs text-gray-500">Injury Rate</p>
              </div>
            </div>
          </Card>

          {/* Feature Importance */}
          {summary.pmdata_analysis.feature_importance && (
            <Card title="Feature Importance (Real Data)">
              <Plot
                data={[{
                  x: summary.pmdata_analysis.feature_importance.map(f => f.importance),
                  y: summary.pmdata_analysis.feature_importance.map(f => f.feature.replace(/_/g, ' ')),
                  type: 'bar',
                  orientation: 'h',
                  marker: { color: 'rgba(59, 130, 246, 0.8)' }
                }]}
                layout={{
                  height: 250,
                  margin: { t: 20, r: 20, b: 40, l: 120 },
                  xaxis: { title: 'Importance' },
                  yaxis: { automargin: true }
                }}
                config={{ displayModeBar: false, responsive: true }}
                style={{ width: '100%' }}
              />
              <p className="text-xs text-gray-500 mt-2">
                Features ranked by Random Forest importance trained on real PMData
              </p>
            </Card>
          )}

          {/* Correlations */}
          {summary.pmdata_analysis.correlations && (
            <Card title="Feature Correlations with Injury">
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-3 py-2 text-left font-medium text-gray-700">Feature</th>
                      <th className="px-3 py-2 text-right font-medium text-gray-700">Correlation</th>
                      <th className="px-3 py-2 text-center font-medium text-gray-700">Significant</th>
                      <th className="px-3 py-2 text-left font-medium text-gray-700">Direction</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {summary.pmdata_analysis.correlations.map(c => (
                      <tr key={c.feature}>
                        <td className="px-3 py-2">{c.feature.replace(/_/g, ' ')}</td>
                        <td className={`px-3 py-2 text-right font-mono ${
                          c.correlation > 0 ? 'text-red-600' : 'text-green-600'
                        }`}>
                          {c.correlation > 0 ? '+' : ''}{c.correlation?.toFixed(4)}
                        </td>
                        <td className="px-3 py-2 text-center">
                          {c.significant ? (
                            <span className="text-green-600">Yes</span>
                          ) : (
                            <span className="text-gray-400">No</span>
                          )}
                        </td>
                        <td className="px-3 py-2 text-xs text-gray-600">{c.direction}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {/* Injury Signature */}
          {summary.pmdata_analysis.injury_signature && (
            <Card title="Injury Signature (Pre-Injury vs Safe Days)">
              <Plot
                data={[{
                  x: summary.pmdata_analysis.injury_signature.map(s => s.feature.replace(/_/g, ' ')),
                  y: summary.pmdata_analysis.injury_signature.map(s => s.delta_percent),
                  type: 'bar',
                  marker: {
                    color: summary.pmdata_analysis.injury_signature.map(s =>
                      s.delta_percent > 0 ? 'rgba(239, 68, 68, 0.7)' : 'rgba(34, 197, 94, 0.7)'
                    )
                  }
                }]}
                layout={{
                  height: 250,
                  margin: { t: 20, r: 20, b: 80, l: 50 },
                  xaxis: { tickangle: -45 },
                  yaxis: { title: 'Change (%)' },
                  shapes: [{
                    type: 'line',
                    x0: 0,
                    x1: 1,
                    xref: 'paper',
                    y0: 0,
                    y1: 0,
                    line: { color: 'gray', width: 1, dash: 'dash' }
                  }]
                }}
                config={{ displayModeBar: false, responsive: true }}
                style={{ width: '100%' }}
              />
              <p className="text-xs text-gray-500 mt-2">
                Percentage change in feature values between safe days and pre-injury days
              </p>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}

export default ValidationPage
