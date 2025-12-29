import { Link } from 'react-router-dom'
import { useState, useRef, useEffect, useCallback } from 'react'
import CitationBlock from '../common/CitationBlock'

function LandingPage() {
  const [showCitation, setShowCitation] = useState(false)
  const citationButtonRef = useRef(null)
  const closeButtonRef = useRef(null)

  useEffect(() => {
    if (showCitation && closeButtonRef.current) {
      closeButtonRef.current.focus()
    }
  }, [showCitation])

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && showCitation) {
        setShowCitation(false)
        citationButtonRef.current?.focus()
      }
    }
    if (showCitation) {
      document.addEventListener('keydown', handleKeyDown)
      return () => document.removeEventListener('keydown', handleKeyDown)
    }
  }, [showCitation])

  const closeCitationModal = useCallback(() => {
    setShowCitation(false)
    citationButtonRef.current?.focus()
  }, [])

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Simple Header */}
      <header className="border-b border-slate-800 bg-slate-950">
        <div className="max-w-4xl mx-auto px-6 py-4 flex justify-between items-center">
          <span className="text-slate-400 text-sm">Research Platform</span>
          <Link to="/pipeline" className="text-blue-400 hover:text-blue-300 text-sm font-medium">
            Open Platform
          </Link>
        </div>
      </header>

      {/* Citation Modal */}
      {showCitation && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="citation-title"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70"
          onClick={closeCitationModal}
        >
          <div className="max-w-lg w-full bg-slate-900 border border-slate-700 rounded-lg shadow-xl p-6" onClick={e => e.stopPropagation()}>
            <h3 id="citation-title" className="text-lg font-semibold text-white mb-4">Citation</h3>
            <CitationBlock />
            <button
              ref={closeButtonRef}
              onClick={closeCitationModal}
              className="mt-4 w-full py-2 text-sm text-slate-400 hover:text-white border border-slate-600 rounded"
            >
              Close
            </button>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-6 py-12">
        {/* Affiliation */}
        <div className="text-center mb-8">
          <p className="text-sm text-slate-500 uppercase tracking-wide">
            Embedded Sensing Group · University of St. Gallen
          </p>
        </div>

        {/* Title */}
        <h1 className="text-3xl font-serif font-bold text-white text-center mb-12 leading-tight">
          Prospective Injury Risk Prediction in Triathletes:<br />
          <span className="font-normal text-slate-300">A Synthetic Data Approach Using Machine Learning</span>
        </h1>

        {/* Abstract */}
        <section className="mb-12">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide mb-4">Abstract</h2>
          <div className="text-slate-400 leading-relaxed space-y-4 text-justify">
            <p>
              <strong className="text-slate-300">Background:</strong> Training-related injuries represent a critical challenge in endurance sports,
              with incidence rates of 37-56% reported among triathletes. Despite widespread adoption of wearable sensor
              technology, prospective injury prediction remains constrained by limited access to large-scale, labeled
              datasets and the complex, multifactorial nature of injury etiology.
            </p>
            <p>
              <strong className="text-slate-300">Methods:</strong> We present a computational framework addressing data scarcity through synthetic
              cohort generation. Our stochastic simulation engine models year-long training trajectories for 100-5000
              athletes, incorporating periodization theory, physiological adaptation dynamics (CTL/ATL via impulse-response
              models), and load-dependent injury mechanisms. Feature engineering implements established sports science
              constructs including Acute:Chronic Workload Ratio (ACWR) and Training Stress Balance (TSB). Three supervised
              learning algorithms (L1-regularized logistic regression, Random Forest, XGBoost) are benchmarked for 7-day
              prospective injury classification.
            </p>
            <p>
              <strong className="text-slate-300">Results:</strong> The framework enables reproducible model development with comprehensive evaluation
              metrics (ROC-AUC, PR-AUC, calibration), interpretability via SHAP-based feature attribution, and counterfactual
              analysis for intervention validation. Validation demonstrates the asymmetric ACWR-injury relationship:
              undertrained athletes (ACWR &lt; 0.8) exhibit 3.5× higher injury risk per training load unit compared to
              optimally trained athletes, while overloaded athletes show elevated risk primarily through increased exposure.
            </p>
            <p>
              <strong className="text-slate-300">Conclusion:</strong> This platform demonstrates a methodology for synthetic data-driven research in
              sports medicine, providing infrastructure for algorithm development while preserving athlete privacy. The
              modular architecture supports extension to other endurance disciplines and integration with real-world
              wearable data streams.
            </p>
          </div>
        </section>

        {/* Keywords */}
        <section className="mb-12">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide mb-3">Keywords</h2>
          <p className="text-slate-500 text-sm">
            Injury prediction · Machine learning · Synthetic data · ACWR · Triathlon · Wearable sensors · XAI
          </p>
        </section>

        {/* Access Platform */}
        <section className="border-t border-slate-800 pt-8">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide mb-4">Access the Platform</h2>
          <div className="flex flex-wrap gap-4">
            <Link
              to="/pipeline"
              className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-500"
            >
              Open Research Platform
            </Link>
            <Link
              to="/data-generation"
              className="px-4 py-2 border border-slate-600 text-slate-300 text-sm font-medium rounded hover:bg-slate-800"
            >
              Generate Synthetic Data
            </Link>
            <Link
              to="/athletes"
              className="px-4 py-2 border border-slate-600 text-slate-300 text-sm font-medium rounded hover:bg-slate-800"
            >
              View Athlete Profiles
            </Link>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 mt-16">
        <div className="max-w-4xl mx-auto px-6 py-8">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4 text-sm text-slate-500">
            <div>
              Embedded Sensing Group · University of St. Gallen
            </div>
            <button
              onClick={() => setShowCitation(true)}
              className="text-slate-500 hover:text-slate-300"
            >
              How to cite this work
            </button>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default LandingPage
