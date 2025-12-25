import { useState, useEffect, useCallback } from 'react'
import { analyticsApi } from '../../api'
import Card from '../common/Card'

function InterventionSimulator({ modelId, athleteId, date, currentMetrics }) {
  const [overrides, setOverrides] = useState({
    sleep_hours: currentMetrics?.sleep_hours || 7.5,
    duration_minutes: currentMetrics?.duration_minutes || 60,
    intensity_factor: currentMetrics?.intensity_factor || 1.0,
    stress: currentMetrics?.stress || 50
  })

  const [results, setResult] = useState(null)
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Reset overrides when currentMetrics change (e.g. new date selected)
  useEffect(() => {
    if (currentMetrics) {
      setOverrides({
        sleep_hours: currentMetrics.sleep_hours || 7.5,
        duration_minutes: currentMetrics.duration_minutes || 60,
        intensity_factor: currentMetrics.intensity_factor || 1.0,
        stress: currentMetrics.stress || 50
      })
      // Clear previous results to avoid confusion
      setResult(null)
      setRecommendations([])
      setError(null)
    }
  }, [currentMetrics])

  const runSimulation = useCallback(async (currentOverrides) => {
    if (!modelId || !athleteId || !date) return

    setLoading(true)
    setError(null)
    try {
      const response = await analyticsApi.simulateIntervention({
        model_id: modelId,
        athlete_id: athleteId,
        date: date,
        overrides: currentOverrides
      })
      setResult(response.data)

      // Generate automated recommendations if risk is high or results present
      if (response.data.new_risk > 0.05) {
        const scenarios = [
          { label: 'Add 2h Sleep', overrides: { ...currentOverrides, sleep_hours: (currentMetrics.sleep_hours || 7.5) + 2 } },
          { label: 'Reduce Intensity by 20%', overrides: { ...currentOverrides, intensity_factor: (currentMetrics.intensity_factor || 1.0) * 0.8 } },
          { label: 'Full Rest Day', overrides: { ...currentOverrides, duration_minutes: 0, intensity_factor: 0 } },
          { label: 'Reduce Stress', overrides: { ...currentOverrides, stress: 20 } }
        ]

        const recPromises = scenarios.map(s => 
          analyticsApi.simulateIntervention({
            model_id: modelId, athlete_id: athleteId, date: date, overrides: s.overrides
          }).then(r => ({ label: s.label, reduction: r.data.risk_reduction }))
        )
        const recResults = await Promise.all(recPromises)
        setRecommendations(recResults.filter(r => r.reduction > 0.001).sort((a,b) => b.reduction - a.reduction))
      }
    } catch (err) {
      console.error('Simulation failed:', err)
      setError(err.response?.data?.error || 'Simulation failed to connect to backend.')
    } finally {
      setLoading(false)
    }
  }, [modelId, athleteId, date, currentMetrics])

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
    } else if (reduction > 0.1) {
      return "This shows a slight improvement. Consider combining with other recovery strategies."
    } else if (reduction < -5) {
      return "Warning: This change increases injury risk substantially."
    }
    return "Minimal impact on risk detected with these parameters."
  }

  return (
    <Card title="What-If Intervention Simulator">
      <div className="space-y-4 sm:space-y-6">
        <p className="text-xs sm:text-sm text-gray-600">
          Simulate how changes to today's parameters affect the predicted injury risk for <strong>{athleteId}</strong> on <strong>{date}</strong>.
        </p>

        {error && (
          <div className="p-2 sm:p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-xs sm:text-sm">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
          {/* Controls */}
          <div className="space-y-4">
            <div>
              <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-1">
                Sleep Hours: {overrides.sleep_hours.toFixed(1)}h
              </label>
              <input
                type="range"
                min="4"
                max="12"
                step="0.1"
                value={overrides.sleep_hours}
                onChange={e => handleSliderChange('sleep_hours', e.target.value)}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
            </div>

            <div>
              <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-1">
                Training Duration: {overrides.duration_minutes}m
              </label>
              <input
                type="range"
                min="0"
                max="180"
                step="5"
                value={overrides.duration_minutes}
                onChange={e => handleSliderChange('duration_minutes', e.target.value)}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
            </div>

            <div>
              <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-1">
                Intensity Factor: {overrides.intensity_factor.toFixed(2)}x
              </label>
              <input
                type="range"
                min="0.5"
                max="1.5"
                step="0.05"
                value={overrides.intensity_factor}
                onChange={e => handleSliderChange('intensity_factor', e.target.value)}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
            </div>

            <div>
              <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-1">
                Stress Level: {overrides.stress.toFixed(0)}
              </label>
              <input
                type="range"
                min="10"
                max="100"
                step="1"
                value={overrides.stress}
                onChange={e => handleSliderChange('stress', e.target.value)}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
            </div>
          </div>

          {/* Results */}
          <div className="flex flex-col justify-start border-t lg:border-t-0 lg:border-l pt-6 lg:pt-0 lg:pl-8 border-gray-100 min-h-[250px] sm:min-h-[300px]">
            {loading && !results ? (
              <div className="flex flex-col items-center justify-center h-full text-gray-400">
                <div className="animate-spin h-6 w-6 sm:h-8 sm:w-8 border-4 border-blue-500 border-t-transparent rounded-full mb-2"></div>
                <p className="text-sm">Calculating risk...</p>
              </div>
            ) : results ? (
              <div className="space-y-4 sm:space-y-6">
                <div className="flex justify-between items-end gap-2">
                  <div className="text-center flex-1">
                    <p className="text-xs text-gray-500 uppercase font-bold mb-1">Current Risk</p>
                    <div className="text-2xl sm:text-3xl font-bold text-red-600">
                      {(results.original_risk * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="text-2xl sm:text-3xl font-light text-gray-300 pb-1">→</div>
                  <div className="text-center flex-1">
                    <p className="text-xs text-gray-500 uppercase font-bold mb-1">Simulated Risk</p>
                    <div className={`text-2xl sm:text-3xl font-bold ${results.new_risk < results.original_risk ? 'text-green-600' : (results.new_risk > results.original_risk ? 'text-red-600' : 'text-gray-600')}`}>
                      {(results.new_risk * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-xs font-medium">
                    <span>Risk Reduction</span>
                    <span>{(results.risk_reduction * 100).toFixed(2)}%</span>
                  </div>
                  <div className="bg-gray-100 h-3 sm:h-4 rounded-full overflow-hidden flex">
                    <div
                      className={`h-full transition-all duration-500 ${results.risk_reduction > 0 ? 'bg-green-500' : 'bg-red-500'}`}
                      style={{ width: `${Math.max(0.1, Math.abs(results.risk_reduction * 100))}%` }}
                    ></div>
                  </div>
                </div>

                <p className="text-xs sm:text-sm font-medium italic text-gray-700">
                  {getTip()}
                </p>

                {recommendations.length > 0 && (
                  <div className="mt-3 sm:mt-4 pt-3 sm:pt-4 border-t border-gray-100">
                    <h4 className="text-xs font-bold uppercase text-gray-500 mb-2">Suggested Actions</h4>
                    <div className="space-y-1.5 sm:space-y-2">
                      {recommendations.map((rec, i) => (
                        <div key={i} className="flex justify-between items-center text-xs sm:text-sm p-2 bg-green-50 text-green-800 rounded">
                          <span>{rec.label}</span>
                          <span className="font-bold whitespace-nowrap ml-2">-{ (rec.reduction * 100).toFixed(1) }%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-gray-400 italic text-center">
                <svg className="w-10 h-10 sm:w-12 sm:h-12 mb-2 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span className="text-sm">Adjust sliders to see impact</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </Card>
  )
}

export default InterventionSimulator