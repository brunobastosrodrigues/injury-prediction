import { createContext, useContext, useState, useCallback } from 'react'
import { dataApi, preprocessingApi, trainingApi } from '../api'

const PipelineContext = createContext(null)

export function PipelineProvider({ children }) {
  // Data state
  const [datasets, setDatasets] = useState([])
  const [currentDataset, setCurrentDataset] = useState(null)
  const [splits, setSplits] = useState([])
  const [currentSplit, setCurrentSplit] = useState(null)
  const [models, setModels] = useState([])

  // Jobs state
  const [activeJobs, setActiveJobs] = useState({})

  // Loading states
  const [loading, setLoading] = useState({
    datasets: false,
    splits: false,
    models: false
  })

  // Refresh datasets
  const refreshDatasets = useCallback(async () => {
    setLoading(prev => ({ ...prev, datasets: true }))
    try {
      const response = await dataApi.listDatasets()
      setDatasets(response.data.datasets || [])
    } catch (error) {
      console.error('Failed to fetch datasets:', error)
    } finally {
      setLoading(prev => ({ ...prev, datasets: false }))
    }
  }, [])

  // Refresh splits
  const refreshSplits = useCallback(async () => {
    setLoading(prev => ({ ...prev, splits: true }))
    try {
      const response = await preprocessingApi.listSplits()
      setSplits(response.data.splits || [])
    } catch (error) {
      console.error('Failed to fetch splits:', error)
    } finally {
      setLoading(prev => ({ ...prev, splits: false }))
    }
  }, [])

  // Refresh models
  const refreshModels = useCallback(async () => {
    setLoading(prev => ({ ...prev, models: true }))
    try {
      const response = await trainingApi.listModels()
      setModels(response.data.models || [])
    } catch (error) {
      console.error('Failed to fetch models:', error)
    } finally {
      setLoading(prev => ({ ...prev, models: false }))
    }
  }, [])

  // Add job to tracking
  const addJob = useCallback((jobId, jobType, description) => {
    setActiveJobs(prev => ({
      ...prev,
      [jobId]: { type: jobType, description, status: 'running', progress: 0 }
    }))
  }, [])

  // Update job status
  const updateJob = useCallback((jobId, updates) => {
    setActiveJobs(prev => ({
      ...prev,
      [jobId]: { ...prev[jobId], ...updates }
    }))
  }, [])

  // Remove job from tracking
  const removeJob = useCallback((jobId) => {
    setActiveJobs(prev => {
      const newJobs = { ...prev }
      delete newJobs[jobId]
      return newJobs
    })
  }, [])

  const value = {
    // Data
    datasets,
    currentDataset,
    setCurrentDataset,
    splits,
    currentSplit,
    setCurrentSplit,
    models,

    // Jobs
    activeJobs,
    addJob,
    updateJob,
    removeJob,

    // Loading
    loading,

    // Refresh functions
    refreshDatasets,
    refreshSplits,
    refreshModels
  }

  return (
    <PipelineContext.Provider value={value}>
      {children}
    </PipelineContext.Provider>
  )
}

export function usePipeline() {
  const context = useContext(PipelineContext)
  if (!context) {
    throw new Error('usePipeline must be used within a PipelineProvider')
  }
  return context
}
