import { useState, useEffect } from 'react'
import Plot from 'react-plotly.js'
import { useTheme } from '../../../context/ThemeContext'
import { analyticsApi } from '../../../api'
import Card from '../../common/Card'

function RiskAnalysisTab({ datasetId, athleteId, modelId, athleteProfile, athleteTimeline }) {
  const { isDark } = useTheme()
  const [riskTimeline, setRiskTimeline] = useState(null)
  const [riskFactors, setRiskFactors] = useState(null)
  const [selectedDate, setSelectedDate] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (datasetId && athleteId && modelId) {
      loadRiskData()
    }
  }, [datasetId, athleteId, modelId])

  useEffect(() => {
    if (datasetId && athleteId && modelId && selectedDate) {
      loadRiskFactors()
    }
  }, [selectedDate])

  const loadRiskData = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await analyticsApi.getAthleteRiskTimeline(datasetId, athleteId, modelId)
      setRiskTimeline(res.data)
      // Auto-select latest date
      if (res.data.dates?.length > 0) {
        setSelectedDate(res.data.dates[res.data.dates.length - 1])
      }
    } catch (err) {
      console.error('Failed to load risk timeline:', err)
      setError('Failed to load risk data. Make sure a model is selected.')
    } finally {
      setLoading(false)
    }
  }

  const loadRiskFactors = async () => {
    try {
      const res = await analyticsApi.getAthleteRiskFactors(datasetId, athleteId, modelId, selectedDate)
      setRiskFactors(res.data)
    } catch (err) {
      console.error('Failed to load risk factors:', err)
    }
  }

  if (!modelId) {
    return (
      <Card>
        <div className="text-center py-12 text-gray-400">
          <p className="text-lg">Please select a model to view risk analysis</p>
          <p className="text-sm mt-2">Risk predictions require a trained model</p>
        </div>
      </Card>
    )
  }

  if (loading) {
    return (
      <Card>
        <div className="flex justify-center py-12">
          <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
        </div>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <div className="text-center py-8 text-red-600">{error}</div>
      </Card>
    )
  }

  if (!riskTimeline) {
    return (
      <Card>
        <div className="text-center py-8 text-gray-400">No risk data available</div>
      </Card>
    )
  }

  const { dates, risk_scores, injury_days, risk_thresholds } = riskTimeline

  // Build risk timeline chart
  const riskTraces = [
    {
      x: dates,
      y: risk_scores.map(r => r * 100),
      type: 'scatter',
      mode: 'lines',
      name: 'Injury Risk',
      fill: 'tozeroy',
      line: { color: '#3b82f6', width: 2 },
      fillcolor: 'rgba(59, 130, 246, 0.2)'
    }
  ]

  // Risk threshold bands
  const riskShapes = [
    // Low risk zone
    {
      type: 'rect',
      x0: dates[0],
      x1: dates[dates.length - 1],
      y0: 0,
      y1: risk_thresholds.low * 100,
      fillcolor: 'rgba(16, 185, 129, 0.1)',
      line: { width: 0 }
    },
    // Moderate risk zone
    {
      type: 'rect',
      x0: dates[0],
      x1: dates[dates.length - 1],
      y0: risk_thresholds.low * 100,
      y1: risk_thresholds.moderate * 100,
      fillcolor: 'rgba(251, 191, 36, 0.1)',
      line: { width: 0 }
    },
    // Elevated risk zone
    {
      type: 'rect',
      x0: dates[0],
      x1: dates[dates.length - 1],
      y0: risk_thresholds.moderate * 100,
      y1: risk_thresholds.high * 100,
      fillcolor: 'rgba(249, 115, 22, 0.1)',
      line: { width: 0 }
    },
    // High risk zone
    {
      type: 'rect',
      x0: dates[0],
      x1: dates[dates.length - 1],
      y0: risk_thresholds.high * 100,
      y1: 100,
      fillcolor: 'rgba(239, 68, 68, 0.1)',
      line: { width: 0 }
    },
    // Injury markers
    ...injury_days.map(day => ({
      type: 'line',
      x0: day,
      x1: day,
      y0: 0,
      y1: 100,
      line: { color: '#ef4444', width: 2, dash: 'dot' }
    }))
  ]

  // Factor breakdown chart
  const factorData = riskFactors?.factor_contributions || []
  const topFactors = factorData.slice(0, 10)

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Risk Timeline */}
      <Card title="Injury Risk Over Time">
        <div className="mb-3 sm:mb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div className="flex flex-wrap gap-2 sm:gap-4 text-xs sm:text-sm">
            <span className="flex items-center">
              <span className="w-2 h-2 sm:w-3 sm:h-3 rounded-full bg-green-500 mr-1"></span> Low
            </span>
            <span className="flex items-center">
              <span className="w-2 h-2 sm:w-3 sm:h-3 rounded-full bg-yellow-500 mr-1"></span> Moderate
            </span>
            <span className="flex items-center">
              <span className="w-2 h-2 sm:w-3 sm:h-3 rounded-full bg-orange-500 mr-1"></span> Elevated
            </span>
            <span className="flex items-center">
              <span className="w-2 h-2 sm:w-3 sm:h-3 rounded-full bg-red-500 mr-1"></span> High
            </span>
          </div>
          <div className="text-xs text-gray-500">
            Red dashed = injuries
          </div>
        </div>

        <div className="-mx-2 sm:mx-0 overflow-x-auto">
          <Plot
            data={riskTraces}
            layout={{
              paper_bgcolor: 'rgba(0,0,0,0)',
              plot_bgcolor: isDark ? 'rgba(15,23,42,0.5)' : 'rgba(249,250,251,0.8)',
              font: { color: isDark ? '#94a3b8' : '#374151' },
              xaxis: { title: 'Date', type: 'date', rangeslider: { visible: true }, tickfont: { size: 10, color: isDark ? '#94a3b8' : '#374151' }, gridcolor: isDark ? '#334155' : '#e5e7eb' },
              yaxis: { title: 'Injury Risk (%)', range: [0, Math.max(...risk_scores) * 100 * 1.2, 50], tickfont: { size: 10, color: isDark ? '#94a3b8' : '#374151' }, gridcolor: isDark ? '#334155' : '#e5e7eb' },
              shapes: riskShapes,
              margin: { t: 20, r: 20, b: 80, l: 45 },
              autosize: true,
              hovermode: 'x'
            }}
            useResizeHandler
            style={{ width: '100%', minWidth: '320px', height: '350px' }}
            config={{ displayModeBar: false }}
            onClick={(data) => {
              if (data.points?.[0]?.x) {
                setSelectedDate(data.points[0].x)
              }
            }}
          />
        </div>
      </Card>

      {/* Risk Statistics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-4">
        <Card>
          <div className="text-center p-1 sm:p-2">
            <p className="text-xl sm:text-3xl font-bold text-blue-600">
              {(riskTimeline.avg_risk * 100).toFixed(1)}%
            </p>
            <p className="text-xs sm:text-sm text-gray-500">Avg Risk</p>
          </div>
        </Card>
        <Card>
          <div className="text-center p-1 sm:p-2">
            <p className="text-xl sm:text-3xl font-bold text-red-600">
              {(riskTimeline.max_risk * 100).toFixed(1)}%
            </p>
            <p className="text-xs sm:text-sm text-gray-500">Max Risk</p>
          </div>
        </Card>
        <Card>
          <div className="text-center p-1 sm:p-2">
            <p className="text-xl sm:text-3xl font-bold text-orange-600">
              {riskTimeline.days_above_moderate}
            </p>
            <p className="text-xs sm:text-sm text-gray-500">Days Elevated</p>
          </div>
        </Card>
        <Card>
          <div className="text-center p-1 sm:p-2">
            <p className="text-xl sm:text-3xl font-bold text-purple-600">
              {injury_days.length}
            </p>
            <p className="text-xs sm:text-sm text-gray-500">Injuries</p>
          </div>
        </Card>
      </div>

      {/* Date Selector & Factor Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        {/* Date Selection */}
        <Card title="Analyze Specific Date">
          <div className="space-y-3 sm:space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Select Date</label>
              <select
                value={selectedDate || ''}
                onChange={e => setSelectedDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              >
                {dates.map((d, i) => (
                  <option key={d} value={d}>
                    {new Date(d).toLocaleDateString()} - {(risk_scores[i] * 100).toFixed(1)}%
                    {injury_days.includes(d) ? ' (INJURY)' : ''}
                  </option>
                ))}
              </select>
            </div>

            {riskFactors && (
              <div className="p-3 sm:p-4 bg-gray-50 rounded-lg">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs sm:text-sm text-gray-500">Risk on {selectedDate}</span>
                  <span className={`text-xl sm:text-2xl font-bold ${
                    riskFactors.current_risk < 0.05 ? 'text-green-600' :
                    riskFactors.current_risk < 0.15 ? 'text-yellow-600' :
                    riskFactors.current_risk < 0.30 ? 'text-orange-600' : 'text-red-600'
                  }`}>
                    {(riskFactors.current_risk * 100).toFixed(1)}%
                  </span>
                </div>
                <p className="text-xs text-gray-500">Model: {riskFactors.model_type}</p>
              </div>
            )}
          </div>
        </Card>

        {/* Lifestyle Impact */}
        <Card title="Lifestyle Category Impact">
          {riskFactors?.lifestyle_impact ? (
            <div className="space-y-3">
              {Object.entries(riskFactors.lifestyle_impact).map(([category, data]) => (
                <div key={category} className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex justify-between items-center">
                    <span className="font-medium capitalize">{category}</span>
                    <span className={`text-sm px-2 py-1 rounded ${
                      data.assessment === 'elevated' ? 'bg-red-100 text-red-700' :
                      data.assessment === 'below_optimal' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-green-100 text-green-700'
                    }`}>
                      {data.assessment.replace('_', ' ')}
                    </span>
                  </div>
                  <div className="mt-1 text-sm text-gray-500">
                    Contribution: {data.contribution > 0 ? '+' : ''}{(data.contribution * 100).toFixed(2)}%
                  </div>
                  {data.top_factors?.length > 0 && (
                    <div className="mt-1 text-xs text-gray-400">
                      Key factors: {data.top_factors.join(', ')}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-center py-4">Select a date to see lifestyle impact</p>
          )}
        </Card>
      </div>

      {/* Factor Breakdown Chart */}
      {riskFactors && topFactors.length > 0 && (
        <Card title={`Risk Factor Breakdown (${selectedDate})`}>
          <p className="text-sm text-gray-500 mb-4">
            These factors show how much each metric contributes to your injury risk.
            Positive values (red) increase risk, negative values (green) decrease it.
          </p>
          <Plot
            data={[
              {
                type: 'bar',
                orientation: 'h',
                x: topFactors.map(f => f.contribution * 100),
                y: topFactors.map(f => f.feature.replace(/_/g, ' ')),
                marker: {
                  color: topFactors.map(f =>
                    f.direction === 'positive' ? '#ef4444' : '#10b981'
                  )
                },
                text: topFactors.map(f =>
                  `${f.contribution > 0 ? '+' : ''}${(f.contribution * 100).toFixed(2)}%`
                ),
                textposition: 'outside',
                hovertemplate: '%{y}: %{x:.2f}% contribution<br>Value: %{customdata}<extra></extra>',
                customdata: topFactors.map(f => f.value?.toFixed(2))
              }
            ]}
            layout={{
              paper_bgcolor: 'rgba(0,0,0,0)',
              plot_bgcolor: isDark ? 'rgba(15,23,42,0.5)' : 'rgba(249,250,251,0.8)',
              font: { color: isDark ? '#94a3b8' : '#374151' },
              xaxis: {
                title: 'Contribution to Risk (%)',
                zeroline: true,
                zerolinecolor: isDark ? '#888' : '#9ca3af',
                zerolinewidth: 2,
                tickfont: { color: isDark ? '#94a3b8' : '#374151' },
                gridcolor: isDark ? '#334155' : '#e5e7eb'
              },
              yaxis: {
                automargin: true,
                tickfont: { color: isDark ? '#94a3b8' : '#374151' }
              },
              margin: { t: 20, r: 80, b: 50, l: 150 },
              autosize: true
            }}
            useResizeHandler
            style={{ width: '100%', height: '400px' }}
          />
        </Card>
      )}

      {/* Interpretation */}
      <Card title="Understanding Your Risk Factors">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
          <div>
            <h4 className="font-medium text-gray-900 mb-2">How to Read This</h4>
            <ul className="space-y-2 text-gray-600">
              <li>• <strong>Red bars</strong> indicate factors that are currently INCREASING your injury risk</li>
              <li>• <strong>Green bars</strong> indicate factors that are PROTECTING you from injury</li>
              <li>• Longer bars mean stronger influence on your risk</li>
              <li>• Focus on the top 3-5 factors for the biggest impact</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-gray-900 mb-2">Actionable Insights</h4>
            <ul className="space-y-2 text-gray-600">
              <li>• If HRV-related factors are red, prioritize recovery</li>
              <li>• If stress factors are red, consider stress management</li>
              <li>• If sleep factors are red, improve sleep hygiene</li>
              <li>• If training load factors are red, reduce intensity</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  )
}

export default RiskAnalysisTab
