import { useState, useEffect } from 'react'
import Plot from 'react-plotly.js'
import { analyticsApi } from '../../../api'
import Card from '../../common/Card'

const METRIC_COLORS = {
  hrv: '#3b82f6',
  resting_hr: '#ef4444',
  sleep_quality: '#8b5cf6',
  stress: '#f97316',
  body_battery_morning: '#10b981',
  sleep_hours: '#6366f1'
}

const METRIC_LABELS = {
  hrv: 'HRV (ms)',
  resting_hr: 'Resting HR (bpm)',
  sleep_quality: 'Sleep Quality',
  stress: 'Stress',
  body_battery_morning: 'Body Battery',
  sleep_hours: 'Sleep Hours'
}

function PreInjuryPatternsTab({ datasetId, athleteId, athleteProfile }) {
  const [patterns, setPatterns] = useState(null)
  const [loading, setLoading] = useState(false)
  const [lookbackDays, setLookbackDays] = useState(14)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (datasetId && athleteId) {
      loadPatterns()
    }
  }, [datasetId, athleteId, lookbackDays])

  const loadPatterns = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await analyticsApi.getAthletePreInjuryPatterns(datasetId, athleteId, lookbackDays)
      setPatterns(res.data)
    } catch (err) {
      console.error('Failed to load pre-injury patterns:', err)
      setError('Failed to load patterns')
    } finally {
      setLoading(false)
    }
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

  if (!patterns) {
    return (
      <Card>
        <div className="text-center py-8 text-gray-400">No pattern data available</div>
      </Card>
    )
  }

  if (patterns.n_injuries === 0) {
    return (
      <Card title="Pre-Injury Pattern Analysis">
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🎉</div>
          <h3 className="text-xl font-bold text-green-600">No Injuries Recorded</h3>
          <p className="text-gray-500 mt-2">
            This athlete has no recorded injuries in the dataset.
          </p>
        </div>
      </Card>
    )
  }

  const { pattern_summary } = patterns
  const availableMetrics = Object.keys(patterns.patterns)

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Controls & Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        <Card title="Analysis Settings">
          <div className="space-y-3 sm:space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Lookback Days</label>
              <select
                value={lookbackDays}
                onChange={e => setLookbackDays(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              >
                <option value={7}>7 days</option>
                <option value={14}>14 days</option>
                <option value={21}>21 days</option>
                <option value={28}>28 days</option>
              </select>
            </div>
            <div className="p-2 sm:p-3 bg-blue-50 rounded-lg">
              <p className="text-xs sm:text-sm text-blue-800">
                Analyzing <strong>{patterns.n_injuries}</strong> injury events
              </p>
            </div>
          </div>
        </Card>

        <Card title="Pattern Summary" className="lg:col-span-2">
          <div className="space-y-3 sm:space-y-4">
            {pattern_summary.message && (
              <div className="p-3 sm:p-4 bg-amber-50 border border-amber-200 rounded-lg">
                <p className="text-xs sm:text-sm text-amber-800 font-medium">{pattern_summary.message}</p>
              </div>
            )}

            <div className="grid grid-cols-3 gap-2 sm:gap-4">
              <div className="text-center p-2 sm:p-3 bg-red-50 rounded-lg">
                <p className="text-xs text-gray-500">Primary Indicator</p>
                <p className="text-sm sm:text-lg font-bold text-red-600 truncate">
                  {METRIC_LABELS[pattern_summary.primary_indicator] || pattern_summary.primary_indicator || '-'}
                </p>
              </div>
              <div className="text-center p-2 sm:p-3 bg-orange-50 rounded-lg">
                <p className="text-xs text-gray-500">Warning</p>
                <p className="text-sm sm:text-lg font-bold text-orange-600">
                  {pattern_summary.typical_warning_window || '-'} days
                </p>
              </div>
              <div className="text-center p-2 sm:p-3 bg-blue-50 rounded-lg">
                <p className="text-xs text-gray-500">HRV Base</p>
                <p className="text-sm sm:text-lg font-bold text-blue-600">
                  {patterns.hrv_baseline?.toFixed(0) || '-'} ms
                </p>
              </div>
            </div>

            {pattern_summary.secondary_indicators?.length > 0 && (
              <div>
                <p className="text-sm text-gray-500 mb-1">Secondary Indicators</p>
                <div className="flex gap-2">
                  {pattern_summary.secondary_indicators.map(ind => (
                    <span key={ind} className="px-2 py-1 bg-gray-100 rounded-full text-sm">
                      {METRIC_LABELS[ind] || ind}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* Pattern Charts */}
      <Card title="Pre-Injury Metric Trends">
        <p className="text-xs sm:text-sm text-gray-500 mb-3 sm:mb-4">
          Average metric values in the {lookbackDays} days leading up to each injury. Day 0 = injury onset.
        </p>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
          {availableMetrics.map(metric => {
            const data = patterns.patterns[metric]
            const change = data.change_percentage

            return (
              <div key={metric} className="border rounded-lg p-3 sm:p-4">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-medium text-sm sm:text-base">{METRIC_LABELS[metric] || metric}</h4>
                  {change !== null && (
                    <span className={`text-xs sm:text-sm font-medium px-2 py-0.5 sm:py-1 rounded ${
                      Math.abs(change) > 5
                        ? change > 0
                          ? 'bg-red-100 text-red-700'
                          : 'bg-green-100 text-green-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}>
                      {change > 0 ? '+' : ''}{change.toFixed(1)}%
                    </span>
                  )}
                </div>

                <Plot
                  data={[
                    ...data.values_by_injury.map((values, i) => ({
                      x: data.days,
                      y: values,
                      type: 'scatter',
                      mode: 'lines',
                      name: `Injury ${i + 1}`,
                      line: { color: METRIC_COLORS[metric] || '#888', width: 1, opacity: 0.3 },
                      showlegend: false
                    })),
                    {
                      x: data.days,
                      y: data.average,
                      type: 'scatter',
                      mode: 'lines+markers',
                      name: 'Average',
                      line: { color: METRIC_COLORS[metric] || '#888', width: 3 },
                      marker: { size: 4 }
                    },
                    {
                      x: [data.days[0], data.days[data.days.length - 1]],
                      y: [data.baseline_avg, data.baseline_avg],
                      type: 'scatter',
                      mode: 'lines',
                      name: 'Baseline',
                      line: { color: '#888', width: 1, dash: 'dash' }
                    }
                  ]}
                  layout={{
                    xaxis: { title: 'Days Before Injury', zeroline: true, zerolinecolor: '#ef4444', zerolinewidth: 2, tickfont: { size: 9 } },
                    yaxis: { title: metric, tickfont: { size: 9 } },
                    margin: { t: 10, r: 10, b: 40, l: 45 },
                    autosize: true,
                    showlegend: false,
                    shapes: [{ type: 'line', x0: 0, x1: 0, y0: 0, y1: 1, yref: 'paper', line: { color: '#ef4444', width: 2 } }],
                    annotations: [{ x: 0, y: 1, yref: 'paper', text: 'Injury', showarrow: false, font: { color: '#ef4444', size: 9 } }]
                  }}
                  useResizeHandler
                  style={{ width: '100%', height: '180px' }}
                  config={{ displayModeBar: false }}
                />
              </div>
            )
          })}
        </div>
      </Card>

      {/* Interpretation Guide */}
      <Card title="Interpretation Guide">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
          <div>
            <h4 className="font-medium text-gray-900 text-sm sm:text-base mb-2">What to Look For</h4>
            <ul className="text-xs sm:text-sm text-gray-600 space-y-1.5 sm:space-y-2">
              <li className="flex items-start">
                <span className="text-red-500 mr-2">•</span>
                <span><strong>HRV Decline:</strong> Accumulated fatigue</span>
              </li>
              <li className="flex items-start">
                <span className="text-red-500 mr-2">•</span>
                <span><strong>RHR Elevation:</strong> Inadequate recovery</span>
              </li>
              <li className="flex items-start">
                <span className="text-red-500 mr-2">•</span>
                <span><strong>Sleep Quality Drop:</strong> Compounds stress</span>
              </li>
              <li className="flex items-start">
                <span className="text-red-500 mr-2">•</span>
                <span><strong>Stress Increase:</strong> Added load</span>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-gray-900 text-sm sm:text-base mb-2">Your Personal Patterns</h4>
            <p className="text-xs sm:text-sm text-gray-600">
              Primary warning sign: <strong className="text-red-600">{METRIC_LABELS[pattern_summary.primary_indicator] || 'not yet determined'}</strong>.
              Monitor when it deviates more than 10% from baseline.
            </p>
            {pattern_summary.typical_warning_window && (
              <p className="text-xs sm:text-sm text-gray-600 mt-2">
                Warning signs typically appear <strong>{pattern_summary.typical_warning_window} days</strong> before injury.
              </p>
            )}
          </div>
        </div>
      </Card>
    </div>
  )
}

export default PreInjuryPatternsTab
