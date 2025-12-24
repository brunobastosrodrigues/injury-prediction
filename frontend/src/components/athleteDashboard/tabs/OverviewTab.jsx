import { useState, useEffect } from 'react'
import Plot from 'react-plotly.js'
import { analyticsApi } from '../../../api'
import Card from '../../common/Card'

function OverviewTab({ athleteProfile, athleteTimeline, selectedModel, datasetId }) {
  const [riskData, setRiskData] = useState(null)
  const [loading, setLoading] = useState(false)

  const profile = athleteProfile?.profile || {}
  const lifestyleInfo = athleteProfile?.lifestyle_info || {}
  const lifestyleFactors = athleteProfile?.lifestyle_factors || {}
  const summaryStats = athleteProfile?.summary_stats || {}

  useEffect(() => {
    if (selectedModel && datasetId && athleteProfile?.athlete_id) {
      loadRiskData()
    }
  }, [selectedModel, datasetId, athleteProfile?.athlete_id])

  const loadRiskData = async () => {
    setLoading(true)
    try {
      const res = await analyticsApi.getAthleteRiskTimeline(
        datasetId,
        athleteProfile.athlete_id,
        selectedModel
      )
      setRiskData(res.data)
    } catch (err) {
      console.error('Failed to load risk data:', err)
    } finally {
      setLoading(false)
    }
  }

  // Prepare lifestyle radar data
  const lifestyleCategories = ['Sleep', 'Sleep Quality', 'Nutrition', 'Low Stress', 'Low Drinking', 'Low Smoking']
  const lifestyleValues = [
    (lifestyleFactors.sleep_time_norm || 7) / 9, // Normalize to 0-1
    lifestyleFactors.sleep_quality || 0.7,
    lifestyleFactors.nutrition_factor || 0.7,
    1 - (lifestyleFactors.stress_factor || 0.3), // Invert: low stress is good
    1 - (lifestyleFactors.drinking_factor || 0.1), // Invert: low drinking is good
    1 - (lifestyleFactors.smoking_factor || 0) // Invert: no smoking is good
  ]

  // Current risk from latest score
  const currentRisk = riskData?.risk_scores?.slice(-1)[0] || null

  const getRiskColor = (risk) => {
    if (risk < 0.05) return 'text-green-600'
    if (risk < 0.15) return 'text-yellow-600'
    if (risk < 0.30) return 'text-orange-600'
    return 'text-red-600'
  }

  const getRiskLabel = (risk) => {
    if (risk < 0.05) return 'Low'
    if (risk < 0.15) return 'Moderate'
    if (risk < 0.30) return 'Elevated'
    return 'High'
  }

  return (
    <div className="space-y-6">
      {/* Athlete Profile Card */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Info */}
        <Card title="Athlete Profile">
          <div className="space-y-4">
            <div className="flex items-center space-x-4">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center text-2xl">
                {profile.gender === 'female' ? '🚴‍♀️' : '🚴'}
              </div>
              <div>
                <h3 className="font-bold text-lg">{athleteProfile?.athlete_id}</h3>
                <p className="text-sm text-gray-500">
                  {profile.age} years old, {profile.gender}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="p-2 bg-gray-50 rounded">
                <p className="text-gray-500">VO2max</p>
                <p className="font-semibold">{profile.vo2max?.toFixed(1)} ml/kg/min</p>
              </div>
              <div className="p-2 bg-gray-50 rounded">
                <p className="text-gray-500">FTP</p>
                <p className="font-semibold">{profile.ftp?.toFixed(0)} W</p>
              </div>
              <div className="p-2 bg-gray-50 rounded">
                <p className="text-gray-500">Resting HR</p>
                <p className="font-semibold">{profile.resting_hr?.toFixed(0)} bpm</p>
              </div>
              <div className="p-2 bg-gray-50 rounded">
                <p className="text-gray-500">HRV Baseline</p>
                <p className="font-semibold">{profile.hrv_baseline?.toFixed(0)} ms</p>
              </div>
              <div className="p-2 bg-gray-50 rounded">
                <p className="text-gray-500">Training</p>
                <p className="font-semibold">{profile.weekly_training_hours?.toFixed(1)} h/week</p>
              </div>
              <div className="p-2 bg-gray-50 rounded">
                <p className="text-gray-500">Experience</p>
                <p className="font-semibold">{profile.training_experience} years</p>
              </div>
            </div>
          </div>
        </Card>

        {/* Lifestyle Profile */}
        <Card title={`Lifestyle: ${profile.lifestyle || 'Unknown'}`}>
          <div className="space-y-4">
            <p className="text-sm text-gray-600">{lifestyleInfo.description}</p>

            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
              <p className="text-sm font-medium text-amber-800">Risk Implications</p>
              <p className="text-sm text-amber-700 mt-1">{lifestyleInfo.risk_implications}</p>
            </div>

            {lifestyleInfo.strengths?.length > 0 && (
              <div>
                <p className="text-sm font-medium text-green-700">Strengths</p>
                <ul className="text-sm text-green-600 list-disc list-inside mt-1">
                  {lifestyleInfo.strengths.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </div>
            )}

            {lifestyleInfo.watch_areas?.length > 0 && (
              <div>
                <p className="text-sm font-medium text-orange-700">Watch Areas</p>
                <ul className="text-sm text-orange-600 list-disc list-inside mt-1">
                  {lifestyleInfo.watch_areas.map((w, i) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </Card>

        {/* Current Risk */}
        <Card title="Current Risk Status">
          {selectedModel ? (
            loading ? (
              <div className="flex justify-center py-8">
                <div className="animate-spin h-6 w-6 border-4 border-blue-500 border-t-transparent rounded-full"></div>
              </div>
            ) : riskData ? (
              <div className="space-y-4">
                <div className="text-center">
                  <p className={`text-5xl font-bold ${getRiskColor(currentRisk)}`}>
                    {(currentRisk * 100).toFixed(1)}%
                  </p>
                  <p className={`text-lg font-medium ${getRiskColor(currentRisk)}`}>
                    {getRiskLabel(currentRisk)} Risk
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="p-2 bg-gray-50 rounded text-center">
                    <p className="text-gray-500">Avg Risk</p>
                    <p className="font-semibold">{(riskData.avg_risk * 100).toFixed(1)}%</p>
                  </div>
                  <div className="p-2 bg-gray-50 rounded text-center">
                    <p className="text-gray-500">Max Risk</p>
                    <p className="font-semibold">{(riskData.max_risk * 100).toFixed(1)}%</p>
                  </div>
                  <div className="p-2 bg-gray-50 rounded text-center col-span-2">
                    <p className="text-gray-500">Days Above Moderate Risk</p>
                    <p className="font-semibold">{riskData.days_above_moderate}</p>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-gray-500 text-center py-4">No risk data available</p>
            )
          ) : (
            <p className="text-gray-400 text-center py-8">Select a model to view risk predictions</p>
          )}
        </Card>
      </div>

      {/* Lifestyle Radar & Summary Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Lifestyle Radar */}
        <Card title="Lifestyle Factor Profile">
          <Plot
            data={[
              {
                type: 'scatterpolar',
                r: [...lifestyleValues, lifestyleValues[0]], // Close the polygon
                theta: [...lifestyleCategories, lifestyleCategories[0]],
                fill: 'toself',
                fillcolor: 'rgba(59, 130, 246, 0.3)',
                line: { color: '#3b82f6', width: 2 },
                name: 'Current'
              },
              {
                type: 'scatterpolar',
                r: [1, 1, 1, 1, 1, 1, 1], // Optimal is all 1s
                theta: [...lifestyleCategories, lifestyleCategories[0]],
                fill: 'none',
                line: { color: '#10b981', width: 2, dash: 'dash' },
                name: 'Optimal'
              }
            ]}
            layout={{
              polar: {
                radialaxis: {
                  visible: true,
                  range: [0, 1]
                }
              },
              showlegend: true,
              legend: { x: 0, y: -0.1, orientation: 'h' },
              margin: { t: 30, r: 30, b: 50, l: 30 },
              autosize: true
            }}
            useResizeHandler
            style={{ width: '100%', height: '350px' }}
          />
        </Card>

        {/* Summary Statistics */}
        <Card title="Performance Summary">
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-red-50 rounded-lg text-center">
              <p className="text-3xl font-bold text-red-600">{summaryStats.total_injuries || 0}</p>
              <p className="text-sm text-gray-500">Total Injuries</p>
            </div>
            <div className="p-4 bg-blue-50 rounded-lg text-center">
              <p className="text-3xl font-bold text-blue-600">{summaryStats.avg_hrv?.toFixed(0) || '-'}</p>
              <p className="text-sm text-gray-500">Avg HRV (ms)</p>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg text-center">
              <p className="text-3xl font-bold text-purple-600">{summaryStats.avg_sleep_hours?.toFixed(1) || '-'}h</p>
              <p className="text-sm text-gray-500">Avg Sleep</p>
            </div>
            <div className="p-4 bg-orange-50 rounded-lg text-center">
              <p className="text-3xl font-bold text-orange-600">{summaryStats.avg_stress?.toFixed(0) || '-'}</p>
              <p className="text-sm text-gray-500">Avg Stress</p>
            </div>
            <div className="p-4 bg-green-50 rounded-lg text-center">
              <p className="text-3xl font-bold text-green-600">{summaryStats.avg_tss?.toFixed(0) || '-'}</p>
              <p className="text-sm text-gray-500">Avg TSS</p>
            </div>
            <div className="p-4 bg-teal-50 rounded-lg text-center">
              <p className="text-3xl font-bold text-teal-600">{summaryStats.avg_body_battery_morning?.toFixed(0) || '-'}</p>
              <p className="text-sm text-gray-500">Avg Body Battery</p>
            </div>
          </div>

          {/* Injury Rate */}
          <div className="mt-4 p-3 bg-gray-50 rounded-lg">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Injury Rate</span>
              <span className="font-semibold">
                {((summaryStats.injury_rate || 0) * 100).toFixed(2)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
              <div
                className="bg-red-500 h-2 rounded-full"
                style={{ width: `${Math.min((summaryStats.injury_rate || 0) * 100 * 10, 100)}%` }}
              ></div>
            </div>
          </div>
        </Card>
      </div>

      {/* Menstrual Cycle Info (if applicable) */}
      {profile.gender === 'female' && profile.menstrual_cycle_config && (
        <Card title="Menstrual Cycle Information">
          <div className="p-4 bg-pink-50 rounded-lg">
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <p className="text-pink-600 font-medium">Cycle Length</p>
                <p className="text-lg font-semibold">{profile.menstrual_cycle_config.cycle_length} days</p>
              </div>
              <div>
                <p className="text-pink-600 font-medium">Luteal Phase</p>
                <p className="text-lg font-semibold">{profile.menstrual_cycle_config.luteal_phase_length} days</p>
              </div>
              <div>
                <p className="text-pink-600 font-medium">Regularity</p>
                <p className="text-lg font-semibold">{(profile.menstrual_cycle_config.regularity * 100).toFixed(0)}%</p>
              </div>
            </div>
            <p className="text-sm text-pink-700 mt-3">
              Note: Injury risk is elevated by ~20% during ovulation phase. Consider lighter training during this period.
            </p>
          </div>
        </Card>
      )}
    </div>
  )
}

export default OverviewTab
