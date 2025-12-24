import { useState, useEffect, useCallback } from 'react'
import Plot from 'react-plotly.js'
import { analyticsApi } from '../../../api'
import Card from '../../common/Card'

function WhatIfTab({ datasetId, athleteId, modelId, athleteTimeline, athleteProfile }) {
  const [selectedDate, setSelectedDate] = useState('')
  const [recommendations, setRecommendations] = useState(null)
  const [simulationResult, setSimulationResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [simulating, setSimulating] = useState(false)

  // Override values for simulation
  const [overrides, setOverrides] = useState({
    sleep_hours: 7.5,
    duration_minutes: 60,
    intensity_factor: 1.0,
    stress: 50
  })

  const profile = athleteProfile?.profile || {}

  useEffect(() => {
    if (datasetId && athleteId && modelId) {
      loadRecommendations()
    }
  }, [datasetId, athleteId, modelId])

  useEffect(() => {
    if (athleteTimeline?.dates?.length > 0 && !selectedDate) {
      const lastDate = athleteTimeline.dates[athleteTimeline.dates.length - 1]
      setSelectedDate(lastDate)
      initializeOverrides(lastDate)
    }
  }, [athleteTimeline])

  useEffect(() => {
    if (selectedDate && athleteTimeline) {
      initializeOverrides(selectedDate)
    }
  }, [selectedDate])

  const loadRecommendations = async () => {
    setLoading(true)
    try {
      const res = await analyticsApi.getAthleteRecommendations(datasetId, athleteId, modelId)
      setRecommendations(res.data)
    } catch (err) {
      console.error('Failed to load recommendations:', err)
    } finally {
      setLoading(false)
    }
  }

  const initializeOverrides = (date) => {
    if (!athleteTimeline?.metrics) return

    const idx = athleteTimeline.dates.indexOf(date)
    if (idx === -1) return

    setOverrides({
      sleep_hours: athleteTimeline.metrics.sleep_hours?.[idx] || 7.5,
      duration_minutes: 60,
      intensity_factor: 1.0,
      stress: athleteTimeline.metrics.stress?.[idx] || 50
    })
  }

  const runSimulation = useCallback(async () => {
    if (!modelId || !athleteId || !selectedDate) return

    setSimulating(true)
    try {
      const res = await analyticsApi.simulateIntervention({
        model_id: modelId,
        athlete_id: athleteId,
        date: selectedDate,
        overrides
      })
      setSimulationResult(res.data)
    } catch (err) {
      console.error('Simulation failed:', err)
    } finally {
      setSimulating(false)
    }
  }, [modelId, athleteId, selectedDate, overrides])

  // Debounced simulation
  useEffect(() => {
    if (!modelId || !selectedDate) return

    const timer = setTimeout(() => {
      runSimulation()
    }, 500)

    return () => clearTimeout(timer)
  }, [overrides, selectedDate, runSimulation])

  const handleOverrideChange = (key, value) => {
    setOverrides(prev => ({ ...prev, [key]: value }))
  }

  if (!modelId) {
    return (
      <Card>
        <div className="text-center py-12 text-gray-400">
          <p className="text-lg">Please select a model to use the What-If simulator</p>
          <p className="text-sm mt-2">Simulations require a trained model to predict outcomes</p>
        </div>
      </Card>
    )
  }

  const currentDateIdx = athleteTimeline?.dates?.indexOf(selectedDate) ?? -1
  const currentMetrics = currentDateIdx >= 0 ? {
    sleep_hours: athleteTimeline.metrics.sleep_hours?.[currentDateIdx],
    stress: athleteTimeline.metrics.stress?.[currentDateIdx],
    hrv: athleteTimeline.metrics.hrv?.[currentDateIdx],
    actual_tss: athleteTimeline.metrics.actual_tss?.[currentDateIdx]
  } : {}

  return (
    <div className="space-y-6">
      {/* Date Selection & Current Context */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Select Date for Simulation">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
              <select
                value={selectedDate}
                onChange={e => setSelectedDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="">Select a date...</option>
                {athleteTimeline?.dates?.map(d => (
                  <option key={d} value={d}>
                    {new Date(d).toLocaleDateString()}
                    {athleteTimeline.injury_days?.includes(d) ? ' (INJURY DAY)' : ''}
                  </option>
                ))}
              </select>
            </div>

            {currentDateIdx >= 0 && (
              <div className="p-3 bg-blue-50 rounded-lg">
                <p className="text-sm font-medium text-blue-800 mb-2">Current Metrics on {selectedDate}</p>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-blue-600">Sleep:</span>
                    <span className="font-medium">{currentMetrics.sleep_hours?.toFixed(1)}h</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-blue-600">Stress:</span>
                    <span className="font-medium">{currentMetrics.stress?.toFixed(0)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-blue-600">HRV:</span>
                    <span className="font-medium">{currentMetrics.hrv?.toFixed(0)} ms</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-blue-600">TSS:</span>
                    <span className="font-medium">{currentMetrics.actual_tss?.toFixed(0)}</span>
                  </div>
                </div>

                {/* Comparison to baseline */}
                {profile.hrv_baseline && currentMetrics.hrv && (
                  <div className={`mt-2 text-sm ${
                    currentMetrics.hrv < profile.hrv_baseline * 0.85 ? 'text-red-600' : 'text-green-600'
                  }`}>
                    HRV is {((currentMetrics.hrv / profile.hrv_baseline - 1) * 100).toFixed(0)}%{' '}
                    {currentMetrics.hrv >= profile.hrv_baseline ? 'above' : 'below'} baseline
                  </div>
                )}
              </div>
            )}
          </div>
        </Card>

        {/* Simulation Result */}
        <Card title="Simulation Result">
          {simulating ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin h-6 w-6 border-4 border-blue-500 border-t-transparent rounded-full"></div>
            </div>
          ) : simulationResult ? (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-500">Original Risk</p>
                  <p className="text-2xl font-bold text-gray-700">
                    {(simulationResult.original_risk * 100).toFixed(1)}%
                  </p>
                </div>
                <div className="p-3 bg-blue-50 rounded-lg">
                  <p className="text-sm text-gray-500">New Risk</p>
                  <p className={`text-2xl font-bold ${
                    simulationResult.new_risk < simulationResult.original_risk
                      ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {(simulationResult.new_risk * 100).toFixed(1)}%
                  </p>
                </div>
                <div className={`p-3 rounded-lg ${
                  simulationResult.risk_reduction > 0 ? 'bg-green-50' : 'bg-red-50'
                }`}>
                  <p className="text-sm text-gray-500">Change</p>
                  <p className={`text-2xl font-bold ${
                    simulationResult.risk_reduction > 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {simulationResult.risk_reduction > 0 ? '-' : '+'}
                    {Math.abs(simulationResult.risk_reduction * 100).toFixed(1)}%
                  </p>
                </div>
              </div>

              {/* Visual comparison */}
              <div className="space-y-2">
                <div className="flex items-center">
                  <span className="w-20 text-sm text-gray-500">Original</span>
                  <div className="flex-1 bg-gray-200 rounded-full h-4">
                    <div
                      className="bg-gray-500 h-4 rounded-full"
                      style={{ width: `${Math.min(simulationResult.original_risk * 100 * 2, 100)}%` }}
                    ></div>
                  </div>
                </div>
                <div className="flex items-center">
                  <span className="w-20 text-sm text-gray-500">Simulated</span>
                  <div className="flex-1 bg-gray-200 rounded-full h-4">
                    <div
                      className={`h-4 rounded-full ${
                        simulationResult.new_risk < simulationResult.original_risk
                          ? 'bg-green-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${Math.min(simulationResult.new_risk * 100 * 2, 100)}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-gray-400 text-center py-8">Adjust parameters to see simulation results</p>
          )}
        </Card>
      </div>

      {/* Intervention Sliders */}
      <Card title="Adjust Parameters">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Sleep Hours */}
          <div>
            <div className="flex justify-between mb-2">
              <label className="text-sm font-medium text-gray-700">Sleep Hours</label>
              <span className="text-sm font-bold text-blue-600">{overrides.sleep_hours.toFixed(1)}h</span>
            </div>
            <input
              type="range"
              min="4"
              max="12"
              step="0.5"
              value={overrides.sleep_hours}
              onChange={e => handleOverrideChange('sleep_hours', parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>4h</span>
              <span className="text-green-600">Baseline: {profile.sleep_time_norm?.toFixed(1)}h</span>
              <span>12h</span>
            </div>
          </div>

          {/* Duration */}
          <div>
            <div className="flex justify-between mb-2">
              <label className="text-sm font-medium text-gray-700">Training Duration</label>
              <span className="text-sm font-bold text-blue-600">{overrides.duration_minutes} min</span>
            </div>
            <input
              type="range"
              min="0"
              max="180"
              step="15"
              value={overrides.duration_minutes}
              onChange={e => handleOverrideChange('duration_minutes', parseInt(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>Rest</span>
              <span>3h</span>
            </div>
          </div>

          {/* Intensity */}
          <div>
            <div className="flex justify-between mb-2">
              <label className="text-sm font-medium text-gray-700">Intensity Factor</label>
              <span className="text-sm font-bold text-blue-600">{overrides.intensity_factor.toFixed(2)}x</span>
            </div>
            <input
              type="range"
              min="0.5"
              max="1.5"
              step="0.05"
              value={overrides.intensity_factor}
              onChange={e => handleOverrideChange('intensity_factor', parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>Easy</span>
              <span>Hard</span>
            </div>
          </div>

          {/* Stress */}
          <div>
            <div className="flex justify-between mb-2">
              <label className="text-sm font-medium text-gray-700">Stress Level</label>
              <span className="text-sm font-bold text-blue-600">{overrides.stress.toFixed(0)}</span>
            </div>
            <input
              type="range"
              min="10"
              max="100"
              step="5"
              value={overrides.stress}
              onChange={e => handleOverrideChange('stress', parseInt(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>Low</span>
              <span>High</span>
            </div>
          </div>
        </div>

        {/* Estimated TSS */}
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600">
            Estimated TSS: <span className="font-bold">
              {((overrides.duration_minutes / 60) * Math.pow(overrides.intensity_factor, 2) * 100).toFixed(0)}
            </span>
            {' '}(based on duration and intensity)
          </p>
        </div>
      </Card>

      {/* Personalized Recommendations */}
      <Card title="Personalized Recommendations">
        {loading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin h-6 w-6 border-4 border-blue-500 border-t-transparent rounded-full"></div>
          </div>
        ) : recommendations?.recommendations?.length > 0 ? (
          <div className="space-y-4">
            {recommendations.recommendations.map((rec, i) => (
              <div
                key={i}
                className={`p-4 rounded-lg border-l-4 ${
                  rec.priority === 'high'
                    ? 'bg-red-50 border-red-500'
                    : rec.priority === 'medium'
                    ? 'bg-orange-50 border-orange-500'
                    : 'bg-green-50 border-green-500'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-medium text-gray-900">{rec.title}</h4>
                    <p className="text-sm text-gray-600 mt-1">{rec.description}</p>
                  </div>
                  <span className={`text-sm font-medium px-2 py-1 rounded ${
                    rec.priority === 'high' ? 'bg-red-100 text-red-700' :
                    rec.priority === 'medium' ? 'bg-orange-100 text-orange-700' :
                    'bg-green-100 text-green-700'
                  }`}>
                    {rec.priority} priority
                  </span>
                </div>

                <div className="mt-3 flex items-center justify-between text-sm">
                  <div className="text-gray-500">
                    Current: <span className="font-medium">{rec.current_value?.toFixed(1)}</span>
                    {' | '}
                    Optimal: <span className="font-medium">
                      {rec.optimal_range?.[0]?.toFixed(1)} - {rec.optimal_range?.[1]?.toFixed(1)}
                    </span>
                  </div>
                  <div className="text-green-600 font-medium">
                    Potential -{(rec.expected_risk_reduction * 100).toFixed(1)}% risk
                  </div>
                </div>

                {/* Quick action button */}
                <button
                  onClick={() => {
                    if (rec.category === 'sleep') {
                      handleOverrideChange('sleep_hours', rec.optimal_range[0])
                    } else if (rec.category === 'stress') {
                      handleOverrideChange('stress', rec.optimal_range[0])
                    } else if (rec.category === 'training') {
                      handleOverrideChange('duration_minutes', 45)
                      handleOverrideChange('intensity_factor', 0.7)
                    }
                  }}
                  className="mt-2 text-sm text-blue-600 hover:text-blue-800"
                >
                  Apply to simulator
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-400">
            <p>No specific recommendations at this time.</p>
            <p className="text-sm mt-1">Your current metrics are within optimal ranges!</p>
          </div>
        )}

        {/* Lifestyle Context */}
        {recommendations?.lifestyle_context && (
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h4 className="font-medium text-blue-800 mb-2">
              Your Lifestyle Profile: {recommendations.lifestyle_context.profile}
            </h4>
            <p className="text-sm text-blue-700">
              {recommendations.lifestyle_context.description}
            </p>

            {recommendations.lifestyle_context.key_risk_areas?.length > 0 && (
              <div className="mt-3">
                <p className="text-sm font-medium text-blue-800">Key Risk Areas:</p>
                <ul className="text-sm text-blue-600 list-disc list-inside mt-1">
                  {recommendations.lifestyle_context.key_risk_areas.map((area, i) => (
                    <li key={i}>{area}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </Card>
    </div>
  )
}

export default WhatIfTab
