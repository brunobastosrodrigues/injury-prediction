import { useState } from 'react'
import Plot from 'react-plotly.js'
import Card from '../../common/Card'

const AVAILABLE_METRICS = [
  { id: 'hrv', label: 'HRV', color: '#3b82f6', yaxis: 'y' },
  { id: 'resting_hr', label: 'Resting HR', color: '#ef4444', yaxis: 'y2' },
  { id: 'sleep_hours', label: 'Sleep Hours', color: '#8b5cf6', yaxis: 'y3' },
  { id: 'sleep_quality', label: 'Sleep Quality', color: '#a855f7', yaxis: 'y3' },
  { id: 'stress', label: 'Stress', color: '#f97316', yaxis: 'y4' },
  { id: 'body_battery_morning', label: 'Body Battery', color: '#10b981', yaxis: 'y' },
  { id: 'actual_tss', label: 'TSS', color: '#6366f1', yaxis: 'y4' }
]

function TimelineTab({ athleteTimeline, athleteProfile }) {
  const [selectedMetrics, setSelectedMetrics] = useState(['hrv', 'stress', 'sleep_hours'])
  const [showInjuries, setShowInjuries] = useState(true)

  if (!athleteTimeline) {
    return (
      <Card>
        <div className="text-center py-8 text-gray-400">No timeline data available</div>
      </Card>
    )
  }

  const { dates, metrics, injury_days } = athleteTimeline
  const profile = athleteProfile?.profile || {}

  const toggleMetric = (metricId) => {
    setSelectedMetrics(prev =>
      prev.includes(metricId)
        ? prev.filter(m => m !== metricId)
        : [...prev, metricId]
    )
  }

  // Build traces for selected metrics
  const traces = selectedMetrics.map(metricId => {
    const metricConfig = AVAILABLE_METRICS.find(m => m.id === metricId)
    const values = metrics[metricId] || []

    return {
      x: dates,
      y: values,
      type: 'scatter',
      mode: 'lines',
      name: metricConfig?.label || metricId,
      line: { color: metricConfig?.color || '#888', width: 2 },
      yaxis: metricConfig?.yaxis || 'y'
    }
  })

  // Add baseline reference lines
  if (selectedMetrics.includes('hrv') && profile.hrv_baseline) {
    traces.push({
      x: [dates[0], dates[dates.length - 1]],
      y: [profile.hrv_baseline, profile.hrv_baseline],
      type: 'scatter',
      mode: 'lines',
      name: 'HRV Baseline',
      line: { color: '#3b82f6', width: 1, dash: 'dash' },
      yaxis: 'y'
    })
  }

  // Injury markers as shapes
  const shapes = showInjuries
    ? injury_days.map(day => ({
        type: 'line',
        x0: day,
        x1: day,
        y0: 0,
        y1: 1,
        yref: 'paper',
        line: { color: '#ef4444', width: 2, dash: 'dot' }
      }))
    : []

  // Injury annotations
  const annotations = showInjuries
    ? injury_days.map((day, i) => ({
        x: day,
        y: 1,
        yref: 'paper',
        text: 'Injury',
        showarrow: true,
        arrowhead: 2,
        arrowcolor: '#ef4444',
        font: { color: '#ef4444', size: 10 }
      }))
    : []

  return (
    <div className="space-y-6">
      {/* Controls */}
      <Card title="Timeline Controls">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Metrics to Display</label>
            <div className="flex flex-wrap gap-2">
              {AVAILABLE_METRICS.map(metric => (
                <button
                  key={metric.id}
                  onClick={() => toggleMetric(metric.id)}
                  className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                    selectedMetrics.includes(metric.id)
                      ? 'text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                  style={{
                    backgroundColor: selectedMetrics.includes(metric.id) ? metric.color : undefined
                  }}
                >
                  {metric.label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="showInjuries"
              checked={showInjuries}
              onChange={e => setShowInjuries(e.target.checked)}
              className="mr-2"
            />
            <label htmlFor="showInjuries" className="text-sm text-gray-700">
              Show injury markers ({injury_days.length} injuries)
            </label>
          </div>
        </div>
      </Card>

      {/* Main Timeline Chart */}
      <Card title="Athlete Timeline">
        <Plot
          data={traces}
          layout={{
            xaxis: {
              title: 'Date',
              rangeslider: { visible: true },
              type: 'date'
            },
            yaxis: {
              title: 'HRV / Body Battery',
              side: 'left',
              showgrid: true
            },
            yaxis2: {
              title: 'Heart Rate (bpm)',
              side: 'right',
              overlaying: 'y',
              showgrid: false
            },
            yaxis3: {
              title: 'Sleep',
              side: 'left',
              overlaying: 'y',
              position: 0.05,
              anchor: 'free',
              showgrid: false,
              visible: false
            },
            yaxis4: {
              title: 'Stress / TSS',
              side: 'right',
              overlaying: 'y',
              position: 0.95,
              anchor: 'free',
              showgrid: false,
              visible: false
            },
            shapes,
            annotations,
            legend: {
              orientation: 'h',
              y: -0.2
            },
            margin: { t: 30, r: 80, b: 100, l: 80 },
            autosize: true,
            hovermode: 'x unified'
          }}
          useResizeHandler
          style={{ width: '100%', height: '500px' }}
        />
      </Card>

      {/* Summary Stats by Period */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card title="First Quarter">
          <MetricSummary
            dates={dates.slice(0, Math.floor(dates.length / 4))}
            metrics={metrics}
            injuryDays={injury_days}
          />
        </Card>
        <Card title="Mid Season">
          <MetricSummary
            dates={dates.slice(Math.floor(dates.length / 4), Math.floor(dates.length * 3 / 4))}
            metrics={metrics}
            injuryDays={injury_days}
          />
        </Card>
        <Card title="Last Quarter">
          <MetricSummary
            dates={dates.slice(Math.floor(dates.length * 3 / 4))}
            metrics={metrics}
            injuryDays={injury_days}
          />
        </Card>
      </div>
    </div>
  )
}

function MetricSummary({ dates, metrics, injuryDays }) {
  const startIdx = 0
  const endIdx = dates.length

  const getSliceMean = (arr) => {
    if (!arr || arr.length === 0) return null
    const slice = arr.slice(startIdx, endIdx)
    return slice.reduce((a, b) => a + b, 0) / slice.length
  }

  const injuries = injuryDays.filter(d => dates.includes(d)).length

  return (
    <div className="space-y-2 text-sm">
      <div className="flex justify-between">
        <span className="text-gray-500">Period</span>
        <span className="font-medium">{dates[0]} - {dates[dates.length - 1]}</span>
      </div>
      <div className="flex justify-between">
        <span className="text-gray-500">Injuries</span>
        <span className={`font-medium ${injuries > 0 ? 'text-red-600' : 'text-green-600'}`}>{injuries}</span>
      </div>
      <div className="flex justify-between">
        <span className="text-gray-500">Avg HRV</span>
        <span className="font-medium">{getSliceMean(metrics.hrv)?.toFixed(1) || '-'} ms</span>
      </div>
      <div className="flex justify-between">
        <span className="text-gray-500">Avg Stress</span>
        <span className="font-medium">{getSliceMean(metrics.stress)?.toFixed(0) || '-'}</span>
      </div>
      <div className="flex justify-between">
        <span className="text-gray-500">Avg Sleep</span>
        <span className="font-medium">{getSliceMean(metrics.sleep_hours)?.toFixed(1) || '-'}h</span>
      </div>
    </div>
  )
}

export default TimelineTab
