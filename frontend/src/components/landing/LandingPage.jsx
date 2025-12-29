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

        {/* Key Results */}
        <section className="mb-12">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide mb-4">Key Results</h2>
          <div className="space-y-6">
            {/* Study Overview */}
            <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-800">
              <p className="text-slate-400 text-sm leading-relaxed">
                Results from reference cohort: <strong className="text-slate-300">1,000 synthetic athletes</strong>,
                <strong className="text-slate-300"> 366,000 daily records</strong>, simulating one year of training
                with physiologically-grounded injury mechanisms.
              </p>
            </div>

            {/* ACWR Risk Asymmetry */}
            <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-800">
              <h3 className="text-sm font-semibold text-slate-300 mb-1">Figure 1: ACWR-Injury Risk Asymmetry</h3>
              <p className="text-xs text-slate-500 mb-4">
                Injury risk per 1,000 TSS units by ACWR zone, demonstrating the "fitness protects" hypothesis.
              </p>
              <div className="space-y-2">
                {/* Undertrained */}
                <div className="flex items-center gap-3">
                  <div className="w-24 text-xs text-slate-400 text-right">Undertrained</div>
                  <div className="flex-1 h-6 bg-slate-800 rounded overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-red-600 to-red-500 flex items-center justify-end pr-2" style={{ width: '100%' }}>
                      <span className="text-xs font-semibold text-white">2.90</span>
                    </div>
                  </div>
                  <div className="w-14 text-xs text-red-400 font-semibold">2.61×</div>
                </div>
                {/* Optimal */}
                <div className="flex items-center gap-3">
                  <div className="w-24 text-xs text-slate-400 text-right">Optimal</div>
                  <div className="flex-1 h-6 bg-slate-800 rounded overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-green-600 to-green-500 flex items-center justify-end pr-2" style={{ width: '38%' }}>
                      <span className="text-xs font-semibold text-white">1.11</span>
                    </div>
                  </div>
                  <div className="w-14 text-xs text-green-400 font-semibold">1.00×</div>
                </div>
                {/* Elevated */}
                <div className="flex items-center gap-3">
                  <div className="w-24 text-xs text-slate-400 text-right">Elevated</div>
                  <div className="flex-1 h-6 bg-slate-800 rounded overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-amber-600 to-amber-500 flex items-center justify-end pr-2" style={{ width: '39%' }}>
                      <span className="text-xs font-semibold text-white">1.14</span>
                    </div>
                  </div>
                  <div className="w-14 text-xs text-amber-400 font-semibold">1.03×</div>
                </div>
                {/* High Risk */}
                <div className="flex items-center gap-3">
                  <div className="w-24 text-xs text-slate-400 text-right">High Risk</div>
                  <div className="flex-1 h-6 bg-slate-800 rounded overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-orange-600 to-orange-500 flex items-center justify-end pr-2" style={{ width: '76%' }}>
                      <span className="text-xs font-semibold text-white">2.19</span>
                    </div>
                  </div>
                  <div className="w-14 text-xs text-orange-400 font-semibold">1.97×</div>
                </div>
              </div>
              <p className="text-xs text-slate-500 mt-3 italic">
                Undertrained athletes (ACWR &lt; 0.8) show 2.6× higher injury risk per unit training load than optimally trained athletes.
              </p>
            </div>

            {/* Model Performance & Validation Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Model Performance */}
              <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-800">
                <h3 className="text-sm font-semibold text-slate-300 mb-1">Figure 2: Model Performance</h3>
                <p className="text-xs text-slate-500 mb-3">7-day injury prediction (AUC-ROC)</p>
                <div className="space-y-2">
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">XGBoost</span>
                      <span className="text-blue-400 font-semibold">0.613</span>
                    </div>
                    <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500 rounded-full" style={{ width: '61.3%' }}></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">Random Forest</span>
                      <span className="text-emerald-400 font-semibold">0.609</span>
                    </div>
                    <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full bg-emerald-500 rounded-full" style={{ width: '60.9%' }}></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">Lasso (L1)</span>
                      <span className="text-purple-400 font-semibold">0.586</span>
                    </div>
                    <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full bg-purple-500 rounded-full" style={{ width: '58.6%' }}></div>
                    </div>
                  </div>
                  <div className="pt-2 border-t border-slate-700">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-500">Random baseline</span>
                      <span className="text-slate-500">0.500</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Validation Three Pillars */}
              <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-800">
                <h3 className="text-sm font-semibold text-slate-300 mb-1">Figure 3: Validation Pillars</h3>
                <p className="text-xs text-slate-500 mb-3">Publication-quality validation</p>
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <div className="w-5 h-5 rounded-full bg-green-500/20 flex items-center justify-center">
                      <span className="text-green-400 text-xs">✓</span>
                    </div>
                    <div className="flex-1">
                      <p className="text-xs text-slate-300">Causal Fidelity</p>
                      <p className="text-xs text-slate-500">ACWR asymmetry confirmed</p>
                    </div>
                    <span className="text-xs text-green-400 font-semibold">0.87</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-5 h-5 rounded-full bg-amber-500/20 flex items-center justify-center">
                      <span className="text-amber-400 text-xs">⚠</span>
                    </div>
                    <div className="flex-1">
                      <p className="text-xs text-slate-300">Statistical Fidelity</p>
                      <p className="text-xs text-slate-500">Synthetic-real distribution gap</p>
                    </div>
                    <span className="text-xs text-amber-400 font-semibold">0.29</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-5 h-5 rounded-full bg-amber-500/20 flex items-center justify-center">
                      <span className="text-amber-400 text-xs">⚠</span>
                    </div>
                    <div className="flex-1">
                      <p className="text-xs text-slate-300">Transferability</p>
                      <p className="text-xs text-slate-500">Sim2Real AUC 0.51</p>
                    </div>
                    <span className="text-xs text-amber-400 font-semibold">0.00</span>
                  </div>
                </div>
                <div className="mt-3 pt-2 border-t border-slate-700 flex justify-between items-center">
                  <span className="text-xs text-slate-400">Overall Score</span>
                  <span className="text-sm font-semibold text-slate-300">0.39 / 1.00</span>
                </div>
              </div>
            </div>

            {/* Key Finding Summary */}
            <div className="p-4 bg-blue-900/20 rounded-lg border border-blue-500/20">
              <p className="text-sm text-slate-300">
                <strong className="text-blue-400">Key Finding:</strong> The causal mechanism validation (0.87) confirms that
                synthetic data accurately captures the ACWR-injury relationship from sports science literature—undertrained
                athletes face disproportionately higher injury risk per training unit, supporting the "fitness protects" hypothesis.
              </p>
            </div>
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
