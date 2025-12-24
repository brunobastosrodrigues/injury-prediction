import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { usePipeline } from '../../context/PipelineContext'
import { analyticsApi, trainingApi } from '../../api'
import Card from '../common/Card'
import OverviewTab from './tabs/OverviewTab'
import TimelineTab from './tabs/TimelineTab'
import PreInjuryPatternsTab from './tabs/PreInjuryPatternsTab'
import RiskAnalysisTab from './tabs/RiskAnalysisTab'
import WhatIfTab from './tabs/WhatIfTab'

function AthleteDashboardPage() {
  const { athleteId: urlAthleteId } = useParams()
  const navigate = useNavigate()
  const { datasets, currentDataset, setCurrentDataset, refreshDatasets } = usePipeline()

  // Selection states
  const [selectedDataset, setSelectedDataset] = useState('')
  const [athletes, setAthletes] = useState([])
  const [selectedAthlete, setSelectedAthlete] = useState(urlAthleteId || '')
  const [models, setModels] = useState([])
  const [selectedModel, setSelectedModel] = useState('')
  const [activeTab, setActiveTab] = useState('overview')

  // Data states
  const [athleteProfile, setAthleteProfile] = useState(null)
  const [athleteTimeline, setAthleteTimeline] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'timeline', label: 'Timeline' },
    { id: 'patterns', label: 'Pre-Injury Patterns' },
    { id: 'risk', label: 'Risk Analysis' },
    { id: 'whatif', label: 'What-If Simulator' }
  ]

  useEffect(() => {
    refreshDatasets()
    fetchModels()
  }, [refreshDatasets])

  useEffect(() => {
    if (currentDataset) {
      setSelectedDataset(currentDataset)
    }
  }, [currentDataset])

  useEffect(() => {
    if (selectedDataset) {
      fetchAthletes(selectedDataset)
    }
  }, [selectedDataset])

  useEffect(() => {
    if (selectedDataset && selectedAthlete) {
      loadAthleteData()
    }
  }, [selectedDataset, selectedAthlete])

  // Sync URL with selected athlete
  useEffect(() => {
    if (selectedAthlete && selectedAthlete !== urlAthleteId) {
      navigate(`/athletes/${selectedAthlete}`, { replace: true })
    }
  }, [selectedAthlete, urlAthleteId, navigate])

  const fetchAthletes = async (datasetId) => {
    try {
      const res = await analyticsApi.listAthletes(datasetId)
      setAthletes(res.data.athletes || [])
      // Auto-select first athlete if URL had one
      if (urlAthleteId && res.data.athletes?.includes(urlAthleteId)) {
        setSelectedAthlete(urlAthleteId)
      }
    } catch (err) {
      console.error('Failed to fetch athletes:', err)
      setAthletes([])
    }
  }

  const fetchModels = async () => {
    try {
      const res = await trainingApi.listModels()
      setModels(res.data.models || [])
    } catch (err) {
      console.error('Failed to fetch models:', err)
    }
  }

  const loadAthleteData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [profileRes, timelineRes] = await Promise.all([
        analyticsApi.getAthleteProfile(selectedDataset, selectedAthlete),
        analyticsApi.getAthleteTimeline(selectedDataset, selectedAthlete)
      ])
      setAthleteProfile(profileRes.data)
      setAthleteTimeline(timelineRes.data)
    } catch (err) {
      console.error('Failed to load athlete data:', err)
      setError('Failed to load athlete data. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleAthleteChange = (athleteId) => {
    setSelectedAthlete(athleteId)
    setAthleteProfile(null)
    setAthleteTimeline(null)
  }

  const handleDatasetChange = (datasetId) => {
    setSelectedDataset(datasetId)
    setCurrentDataset(datasetId)
    setSelectedAthlete('')
    setAthleteProfile(null)
    setAthleteTimeline(null)
  }

  // Filter models for current dataset
  const datasetModels = models.filter(m => m.dataset_id === selectedDataset)
  const displayModels = datasetModels.length > 0 ? datasetModels : models

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Athlete Dashboard</h1>
        <p className="text-gray-600 mt-1">
          Individual athlete analysis with personalized insights and recommendations
        </p>
      </div>

      {/* Selection Controls */}
      <Card>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Dataset</label>
            <select
              value={selectedDataset}
              onChange={e => handleDatasetChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select a dataset...</option>
              {datasets.map(ds => (
                <option key={ds.id} value={ds.id}>
                  {ds.id} ({ds.n_athletes} athletes)
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Athlete</label>
            <select
              value={selectedAthlete}
              onChange={e => handleAthleteChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              disabled={!selectedDataset}
            >
              <option value="">Select an athlete...</option>
              {athletes.map(a => (
                <option key={a} value={a}>{a}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Model (for predictions)</label>
            <select
              value={selectedModel}
              onChange={e => setSelectedModel(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              disabled={!selectedDataset}
            >
              <option value="">Select a model...</option>
              {displayModels.map(m => (
                <option key={m.id} value={m.id}>
                  {m.id} ({m.model_name})
                  {m.dataset_id !== selectedDataset ? ' - Different Dataset' : ''}
                </option>
              ))}
            </select>
            {datasetModels.length === 0 && models.length > 0 && selectedDataset && (
              <p className="text-xs text-orange-600 mt-1">No models for this dataset. Train a model first.</p>
            )}
          </div>
        </div>
      </Card>

      {/* Loading State */}
      {loading && (
        <Card>
          <div className="flex justify-center py-12">
            <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
          </div>
        </Card>
      )}

      {/* Error State */}
      {error && (
        <Card>
          <div className="text-center py-8 text-red-600">{error}</div>
        </Card>
      )}

      {/* Main Content */}
      {selectedDataset && selectedAthlete && athleteProfile && !loading && (
        <>
          {/* Tabs Navigation */}
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
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

          {/* Tab Content */}
          {activeTab === 'overview' && (
            <OverviewTab
              athleteProfile={athleteProfile}
              athleteTimeline={athleteTimeline}
              selectedModel={selectedModel}
              datasetId={selectedDataset}
            />
          )}

          {activeTab === 'timeline' && (
            <TimelineTab
              athleteTimeline={athleteTimeline}
              athleteProfile={athleteProfile}
            />
          )}

          {activeTab === 'patterns' && (
            <PreInjuryPatternsTab
              datasetId={selectedDataset}
              athleteId={selectedAthlete}
              athleteProfile={athleteProfile}
            />
          )}

          {activeTab === 'risk' && (
            <RiskAnalysisTab
              datasetId={selectedDataset}
              athleteId={selectedAthlete}
              modelId={selectedModel}
              athleteProfile={athleteProfile}
              athleteTimeline={athleteTimeline}
            />
          )}

          {activeTab === 'whatif' && (
            <WhatIfTab
              datasetId={selectedDataset}
              athleteId={selectedAthlete}
              modelId={selectedModel}
              athleteTimeline={athleteTimeline}
              athleteProfile={athleteProfile}
            />
          )}
        </>
      )}

      {/* Empty State */}
      {(!selectedDataset || !selectedAthlete) && !loading && (
        <Card>
          <div className="text-center py-12 text-gray-400">
            <p className="text-lg">Select a dataset and athlete to view their personalized dashboard</p>
            <p className="text-sm mt-2">
              The dashboard provides historical analysis, injury pattern detection, and personalized recommendations
            </p>
          </div>
        </Card>
      )}
    </div>
  )
}

export default AthleteDashboardPage
