import { Routes, Route } from 'react-router-dom'
import Layout from './components/common/Layout'
import LandingPage from './components/landing/LandingPage'
import Dashboard from './components/dashboard/Dashboard'
import DataGenerationPage from './components/dataGeneration/DataGenerationPage'
import IngestionPage from './components/dataGeneration/IngestionPage'
import PreprocessingPage from './components/preprocessing/PreprocessingPage'
import TrainingPage from './components/training/TrainingPage'
import ResultsPage from './components/results/ResultsPage'
import AnalyticsPage from './components/analytics/AnalyticsPage'
import AthleteDashboardPage from './components/athleteDashboard/AthleteDashboardPage'
import ModelInterpretability from './pages/ModelInterpretability'
import ValidationPage from './components/validation/ValidationPage'

function App() {
  return (
    <Routes>
      {/* Landing page - no sidebar/header */}
      <Route path="/" element={<LandingPage />} />

      {/* Pipeline pages - with sidebar/header */}
      <Route path="/pipeline" element={<Layout><Dashboard /></Layout>} />
      <Route path="/data-generation" element={<Layout><DataGenerationPage /></Layout>} />
      <Route path="/ingestion" element={<Layout><IngestionPage /></Layout>} />
      <Route path="/preprocessing" element={<Layout><PreprocessingPage /></Layout>} />
      <Route path="/training" element={<Layout><TrainingPage /></Layout>} />
      <Route path="/results" element={<Layout><ResultsPage /></Layout>} />
      <Route path="/validation" element={<Layout><ValidationPage /></Layout>} />
      <Route path="/analytics" element={<Layout><AnalyticsPage /></Layout>} />
      <Route path="/interpretability" element={<Layout><ModelInterpretability /></Layout>} />
      <Route path="/athletes" element={<Layout><AthleteDashboardPage /></Layout>} />
      <Route path="/athletes/:athleteId" element={<Layout><AthleteDashboardPage /></Layout>} />
    </Routes>
  )
}

export default App
