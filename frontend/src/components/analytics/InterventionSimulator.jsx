import { useState, useEffect, useCallback } from 'react'
import { analyticsApi } from '../../api'
import Card from '../common/Card'

function InterventionSimulator({ modelId, athleteId, date, currentMetrics }) {
  const [overrides, setOverrides] = useState({
    sleep_hours: currentMetrics?.sleep_hours || 7.5,
    duration_minutes: currentMetrics?.duration_minutes || 60,
    intensity_factor: currentMetrics?.intensity_factor || 1.0
  })

  const [results, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  // Reset overrides when currentMetrics change (e.g. new date selected)
  useEffect(() => {
    if (currentMetrics) {
      setOverrides({
        sleep_hours: currentMetrics.sleep_hours || 7.5,
        duration_minutes: currentMetrics.duration_minutes || 60,
        intensity_factor: currentMetrics.intensity_factor || 1.0
      })
      // Clear previous results to avoid confusion
      setResult(null)
    }
  }, [currentMetrics])

  const runSimulation = useCallback(async (currentOverrides) => {
    if (!modelId || !athleteId || !date) return

    setLoading(true)
    try {
      const response = await analyticsApi.simulateIntervention({
        model_id: modelId,
        athlete_id: athleteId,
        date: date,
        overrides: currentOverrides
      })
      setResult(response.data)
    } catch (error) {
      console.error('Simulation failed:', error)
    } finally {
      setLoading(false)
    }
  }, [modelId, athleteId, date])

  // Debounced simulation
  useEffect(() => {
    const timer = setTimeout(() => {
      runSimulation(overrides)
    }, 500)
    return () => clearTimeout(timer)
  }, [overrides, runSimulation])

  const handleSliderChange = (key, value) => {
    setOverrides(prev => ({ ...prev, [key]: parseFloat(value) }))
  }

  const getTip = () => {
    if (!results) return null
    const reduction = results.risk_reduction * 100
    if (reduction > 5) {
      return "This intervention significantly reduces injury risk. Focus on these adjustments today."
    } else if (reduction > 0) {
      return "This shows a slight improvement. Consider combining with other recovery strategies."
    } else if (reduction < -5) {
      return "Warning: This change increases injury risk substantially."
    }
    return "Minimal impact on risk detected with these parameters."
  }

  return (
    <Card title="What-If Intervention Simulator">
      <div className="space-y-6">
        <p className="text-sm text-gray-600">
          Simulate how changes to today's parameters affect the predicted injury risk for <strong>{athleteId}</strong> on <strong>{date}</strong>.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Controls */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Sleep Hours: {overrides.sleep_hours}h
              </label>
              <input
                type="range"
                min="4"
                max="12"
                step="0.5"
                value={overrides.sleep_hours}
                onChange={e => handleSliderChange('sleep_hours', e.target.value)}
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Training Duration: {overrides.duration_minutes}m
              </label>
              <input
                type="range"
                min="0"
                max="180"
                step="5"
                value={overrides.duration_minutes}
                onChange={e => handleSliderChange('duration_minutes', e.target.value)}
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Intensity Factor: {overrides.intensity_factor}x
              </label>
              <input
                type="range"
                min="0.5"
                max="1.5"
                step="0.05"
                value={overrides.intensity_factor}
                onChange={e => handleSliderChange('intensity_factor', e.target.value)}
                className="w-full"
              />
            </div>
          </div>

          {/* Results */}
          <div className="flex flex-col justify-center border-l pl-8 border-gray-100">
            {loading && !results ? (
              <div className="text-center py-4">Calculating...</div>
            ) : results ? (
              <div className="space-y-6">
                <div className="flex justify-between items-end">
                  <div className="text-center">
                    <p className="text-xs text-gray-500 uppercase font-bold mb-1">Current Risk</p>
                    <div className="text-3xl font-bold text-red-600">
                      {(results.original_risk * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="text-3xl font-light text-gray-300 pb-1">→</div>
                  <div className="text-center">
                    <p className="text-xs text-gray-500 uppercase font-bold mb-1">Simulated Risk</p>
                    <div className={`text-3xl font-bold ${results.new_risk < results.original_risk ? 'text-green-600' : 'text-orange-600'}`}>
                      {(results.new_risk * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>

                <div className="bg-gray-100 h-4 rounded-full overflow-hidden flex">
                   <div 
                    className="bg-green-500 h-full transition-all duration-500" 
                    style={{ width: `${Math.max(0, results.risk_reduction * 100)}%` }}
                   ></div>
                </div>
                
                <p className="text-sm font-medium italic text-gray-700">
                  {getTip()}
                </p>
              </div>
            ) : (
              <div className="text-gray-400 italic text-center">Adjust sliders to see impact</div>
            )}
          </div>
        </div>
      </div>
    </Card>
  )
}

export default InterventionSimulator
