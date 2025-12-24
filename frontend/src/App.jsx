import { Routes, Route } from 'react-router-dom'
import Layout from './components/common/Layout'
import Dashboard from './components/dashboard/Dashboard'
import DataGenerationPage from './components/dataGeneration/DataGenerationPage'
import IngestionPage from './components/dataGeneration/IngestionPage'
import PreprocessingPage from './components/preprocessing/PreprocessingPage'
import TrainingPage from './components/training/TrainingPage'
import ResultsPage from './components/results/ResultsPage'
import AnalyticsPage from './components/analytics/AnalyticsPage'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/data-generation" element={<DataGenerationPage />} />
        <Route path="/ingestion" element={<IngestionPage />} />
        <Route path="/preprocessing" element={<PreprocessingPage />} />
        <Route path="/training" element={<TrainingPage />} />
        <Route path="/results" element={<ResultsPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
      </Routes>
    </Layout>
  )
}

export default App
