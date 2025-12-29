import { Link } from 'react-router-dom'
import { useState, useRef, useEffect, useCallback } from 'react'
import { useTheme } from '../../context/ThemeContext'
import CitationBlock from '../common/CitationBlock'

function LandingPage() {
  const { isDark, toggleTheme, theme } = useTheme()
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
    <div className={`min-h-screen ${isDark ? 'bg-slate-950' : 'bg-gray-50'}`}>
      {/* Simple Header */}
      <header className={`border-b ${isDark ? 'border-slate-800 bg-slate-950' : 'border-gray-200 bg-white'}`}>
        <div className="max-w-4xl mx-auto px-6 py-4 flex justify-end items-center">
          <div className="flex items-center gap-4">
            <button
              onClick={toggleTheme}
              className={`p-2 rounded-lg ${isDark ? 'text-slate-400 hover:text-white hover:bg-slate-800' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'} transition-colors`}
              aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
            >
              {isDark ? (
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
              )}
            </button>
            <Link to="/pipeline" className="text-blue-600 dark:text-blue-400 hover:text-blue-500 dark:hover:text-blue-300 text-sm font-medium">
              Open Platform
            </Link>
          </div>
        </div>
      </header>

      {/* Citation Modal */}
      {showCitation && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="citation-title"
          className={`fixed inset-0 z-50 flex items-center justify-center p-4 ${isDark ? 'bg-black/70' : 'bg-black/50'}`}
          onClick={closeCitationModal}
        >
          <div className={`max-w-lg w-full ${isDark ? 'bg-slate-900 border-slate-700' : 'bg-white border-gray-200'} border rounded-lg shadow-xl p-6`} onClick={e => e.stopPropagation()}>
            <h3 id="citation-title" className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>Citation</h3>
            <CitationBlock />
            <button
              ref={closeButtonRef}
              onClick={closeCitationModal}
              className={`mt-4 w-full py-2 text-sm ${isDark ? 'text-slate-400 hover:text-white border-slate-600' : 'text-gray-500 hover:text-gray-900 border-gray-300'} border rounded`}
            >
              Close
            </button>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-6 py-12">
        {/* Title */}
        <h1 className={`text-3xl font-serif font-bold ${isDark ? 'text-white' : 'text-gray-900'} text-center mb-12 leading-tight`}>
          Prospective Injury Risk Prediction in Triathletes:<br />
          <span className={`font-normal ${isDark ? 'text-slate-300' : 'text-gray-600'}`}>A Synthetic Data Approach Using Machine Learning</span>
        </h1>

        {/* Abstract */}
        <section className="mb-12">
          <h2 className={`text-sm font-semibold ${isDark ? 'text-slate-300' : 'text-gray-700'} uppercase tracking-wide mb-4`}>Abstract</h2>
          <div className={`${isDark ? 'text-slate-400' : 'text-gray-600'} leading-relaxed space-y-4 text-justify`}>
            <p>
              <strong className={isDark ? 'text-slate-300' : 'text-gray-800'}>Background:</strong> Training-related injuries represent a critical challenge in endurance sports,
              with incidence rates of 37-56% reported among triathletes. Despite widespread adoption of wearable sensor
              technology, prospective injury prediction remains constrained by limited access to large-scale, labeled
              datasets and the complex, multifactorial nature of injury etiology.
            </p>
            <p>
              <strong className={isDark ? 'text-slate-300' : 'text-gray-800'}>Methods:</strong> We present a computational framework addressing data scarcity through synthetic
              cohort generation. Our stochastic simulation engine models year-long training trajectories for 100-5000
              athletes, incorporating periodization theory, physiological adaptation dynamics (CTL/ATL via impulse-response
              models), and load-dependent injury mechanisms. Feature engineering implements established sports science
              constructs including Acute:Chronic Workload Ratio (ACWR) and Training Stress Balance (TSB). Three supervised
              learning algorithms (L1-regularized logistic regression, Random Forest, XGBoost) are benchmarked for 7-day
              prospective injury classification.
            </p>
            <p>
              <strong className={isDark ? 'text-slate-300' : 'text-gray-800'}>Results:</strong> The framework enables reproducible model development with comprehensive evaluation
              metrics (ROC-AUC, PR-AUC, calibration), interpretability via SHAP-based feature attribution, and counterfactual
              analysis for intervention validation. Validation demonstrates the asymmetric ACWR-injury relationship:
              undertrained athletes (ACWR &lt; 0.8) exhibit 3.5× higher injury risk per training load unit compared to
              optimally trained athletes, while overloaded athletes show elevated risk primarily through increased exposure.
            </p>
            <p>
              <strong className={isDark ? 'text-slate-300' : 'text-gray-800'}>Conclusion:</strong> This platform demonstrates a methodology for synthetic data-driven research in
              sports medicine, providing infrastructure for algorithm development while preserving athlete privacy. The
              modular architecture supports extension to other endurance disciplines and integration with real-world
              wearable data streams.
            </p>
          </div>
        </section>

        {/* Key Results */}
        <section className="mb-12">
          <h2 className={`text-sm font-semibold ${isDark ? 'text-slate-300' : 'text-gray-700'} uppercase tracking-wide mb-4`}>Key Results</h2>
          <div className="space-y-6">
            {/* Study Overview */}
            <div className={`p-4 rounded-lg border ${isDark ? 'bg-slate-900/50 border-slate-800' : 'bg-white border-gray-200 shadow-sm'}`}>
              <p className={`text-sm leading-relaxed ${isDark ? 'text-slate-400' : 'text-gray-600'}`}>
                Results from reference cohort: <strong className={isDark ? 'text-slate-300' : 'text-gray-800'}>1,000 synthetic athletes</strong>,
                <strong className={isDark ? 'text-slate-300' : 'text-gray-800'}> 366,000 daily records</strong>, simulating one year of training
                with physiologically-grounded injury mechanisms.
              </p>
            </div>

            {/* ACWR Risk Asymmetry */}
            <div className={`p-4 rounded-lg border ${isDark ? 'bg-slate-900/50 border-slate-800' : 'bg-white border-gray-200 shadow-sm'}`}>
              <h3 className={`text-sm font-semibold ${isDark ? 'text-slate-300' : 'text-gray-800'} mb-1`}>Figure 1: ACWR-Injury Risk Asymmetry</h3>
              <p className={`text-xs ${isDark ? 'text-slate-500' : 'text-gray-500'} mb-4`}>
                Injury risk per 1,000 TSS units by ACWR zone, demonstrating the "fitness protects" hypothesis.
              </p>
              <div className="space-y-2">
                {/* Undertrained */}
                <div className="flex items-center gap-3">
                  <div className={`w-24 text-xs ${isDark ? 'text-slate-400' : 'text-gray-600'} text-right`}>Undertrained</div>
                  <div className={`flex-1 h-6 ${isDark ? 'bg-slate-800' : 'bg-gray-200'} rounded overflow-hidden`}>
                    <div className="h-full bg-gradient-to-r from-red-600 to-red-500 flex items-center justify-end pr-2" style={{ width: '100%' }}>
                      <span className="text-xs font-semibold text-white">2.90</span>
                    </div>
                  </div>
                  <div className="w-14 text-xs text-red-500 font-semibold">2.61×</div>
                </div>
                {/* Optimal */}
                <div className="flex items-center gap-3">
                  <div className={`w-24 text-xs ${isDark ? 'text-slate-400' : 'text-gray-600'} text-right`}>Optimal</div>
                  <div className={`flex-1 h-6 ${isDark ? 'bg-slate-800' : 'bg-gray-200'} rounded overflow-hidden`}>
                    <div className="h-full bg-gradient-to-r from-green-600 to-green-500 flex items-center justify-end pr-2" style={{ width: '38%' }}>
                      <span className="text-xs font-semibold text-white">1.11</span>
                    </div>
                  </div>
                  <div className="w-14 text-xs text-green-500 font-semibold">1.00×</div>
                </div>
                {/* Elevated */}
                <div className="flex items-center gap-3">
                  <div className={`w-24 text-xs ${isDark ? 'text-slate-400' : 'text-gray-600'} text-right`}>Elevated</div>
                  <div className={`flex-1 h-6 ${isDark ? 'bg-slate-800' : 'bg-gray-200'} rounded overflow-hidden`}>
                    <div className="h-full bg-gradient-to-r from-amber-600 to-amber-500 flex items-center justify-end pr-2" style={{ width: '39%' }}>
                      <span className="text-xs font-semibold text-white">1.14</span>
                    </div>
                  </div>
                  <div className="w-14 text-xs text-amber-500 font-semibold">1.03×</div>
                </div>
                {/* High Risk */}
                <div className="flex items-center gap-3">
                  <div className={`w-24 text-xs ${isDark ? 'text-slate-400' : 'text-gray-600'} text-right`}>High Risk</div>
                  <div className={`flex-1 h-6 ${isDark ? 'bg-slate-800' : 'bg-gray-200'} rounded overflow-hidden`}>
                    <div className="h-full bg-gradient-to-r from-orange-600 to-orange-500 flex items-center justify-end pr-2" style={{ width: '76%' }}>
                      <span className="text-xs font-semibold text-white">2.19</span>
                    </div>
                  </div>
                  <div className="w-14 text-xs text-orange-500 font-semibold">1.97×</div>
                </div>
              </div>
              <p className={`text-xs ${isDark ? 'text-slate-500' : 'text-gray-500'} mt-3 italic`}>
                Undertrained athletes (ACWR &lt; 0.8) show 2.6× higher injury risk per unit training load than optimally trained athletes.
              </p>
            </div>

            {/* Model Performance & Validation Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Model Performance */}
              <div className={`p-4 rounded-lg border ${isDark ? 'bg-slate-900/50 border-slate-800' : 'bg-white border-gray-200 shadow-sm'}`}>
                <h3 className={`text-sm font-semibold ${isDark ? 'text-slate-300' : 'text-gray-800'} mb-1`}>Figure 2: Model Performance</h3>
                <p className={`text-xs ${isDark ? 'text-slate-500' : 'text-gray-500'} mb-3`}>7-day injury prediction (AUC-ROC)</p>
                <div className="space-y-2">
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className={isDark ? 'text-slate-400' : 'text-gray-600'}>XGBoost</span>
                      <span className="text-blue-500 font-semibold">0.613</span>
                    </div>
                    <div className={`h-2 ${isDark ? 'bg-slate-800' : 'bg-gray-200'} rounded-full overflow-hidden`}>
                      <div className="h-full bg-blue-500 rounded-full" style={{ width: '61.3%' }}></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className={isDark ? 'text-slate-400' : 'text-gray-600'}>Random Forest</span>
                      <span className="text-emerald-500 font-semibold">0.609</span>
                    </div>
                    <div className={`h-2 ${isDark ? 'bg-slate-800' : 'bg-gray-200'} rounded-full overflow-hidden`}>
                      <div className="h-full bg-emerald-500 rounded-full" style={{ width: '60.9%' }}></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className={isDark ? 'text-slate-400' : 'text-gray-600'}>Lasso (L1)</span>
                      <span className="text-purple-500 font-semibold">0.586</span>
                    </div>
                    <div className={`h-2 ${isDark ? 'bg-slate-800' : 'bg-gray-200'} rounded-full overflow-hidden`}>
                      <div className="h-full bg-purple-500 rounded-full" style={{ width: '58.6%' }}></div>
                    </div>
                  </div>
                  <div className={`pt-2 border-t ${isDark ? 'border-slate-700' : 'border-gray-200'}`}>
                    <div className="flex justify-between text-xs">
                      <span className={isDark ? 'text-slate-500' : 'text-gray-500'}>Random baseline</span>
                      <span className={isDark ? 'text-slate-500' : 'text-gray-500'}>0.500</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Validation Three Pillars */}
              <div className={`p-4 rounded-lg border ${isDark ? 'bg-slate-900/50 border-slate-800' : 'bg-white border-gray-200 shadow-sm'}`}>
                <h3 className={`text-sm font-semibold ${isDark ? 'text-slate-300' : 'text-gray-800'} mb-1`}>Figure 3: Validation Pillars</h3>
                <p className={`text-xs ${isDark ? 'text-slate-500' : 'text-gray-500'} mb-3`}>Publication-quality validation</p>
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <div className={`w-5 h-5 rounded-full ${isDark ? 'bg-green-500/20' : 'bg-green-100'} flex items-center justify-center`}>
                      <span className="text-green-500 text-xs">✓</span>
                    </div>
                    <div className="flex-1">
                      <p className={`text-xs ${isDark ? 'text-slate-300' : 'text-gray-800'}`}>Causal Fidelity</p>
                      <p className={`text-xs ${isDark ? 'text-slate-500' : 'text-gray-500'}`}>ACWR asymmetry confirmed</p>
                    </div>
                    <span className="text-xs text-green-500 font-semibold">0.87</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className={`w-5 h-5 rounded-full ${isDark ? 'bg-amber-500/20' : 'bg-amber-100'} flex items-center justify-center`}>
                      <span className="text-amber-500 text-xs">⚠</span>
                    </div>
                    <div className="flex-1">
                      <p className={`text-xs ${isDark ? 'text-slate-300' : 'text-gray-800'}`}>Statistical Fidelity</p>
                      <p className={`text-xs ${isDark ? 'text-slate-500' : 'text-gray-500'}`}>Synthetic-real distribution gap</p>
                    </div>
                    <span className="text-xs text-amber-500 font-semibold">0.29</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className={`w-5 h-5 rounded-full ${isDark ? 'bg-amber-500/20' : 'bg-amber-100'} flex items-center justify-center`}>
                      <span className="text-amber-500 text-xs">⚠</span>
                    </div>
                    <div className="flex-1">
                      <p className={`text-xs ${isDark ? 'text-slate-300' : 'text-gray-800'}`}>Transferability</p>
                      <p className={`text-xs ${isDark ? 'text-slate-500' : 'text-gray-500'}`}>Sim2Real AUC 0.51</p>
                    </div>
                    <span className="text-xs text-amber-500 font-semibold">0.00</span>
                  </div>
                </div>
                <div className={`mt-3 pt-2 border-t ${isDark ? 'border-slate-700' : 'border-gray-200'} flex justify-between items-center`}>
                  <span className={`text-xs ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>Overall Score</span>
                  <span className={`text-sm font-semibold ${isDark ? 'text-slate-300' : 'text-gray-800'}`}>0.39 / 1.00</span>
                </div>
              </div>
            </div>

            {/* Key Finding Summary */}
            <div className={`p-4 rounded-lg border ${isDark ? 'bg-blue-900/20 border-blue-500/20' : 'bg-blue-50 border-blue-200'}`}>
              <p className={`text-sm ${isDark ? 'text-slate-300' : 'text-gray-700'}`}>
                <strong className="text-blue-600 dark:text-blue-400">Key Finding:</strong> The causal mechanism validation (0.87) confirms that
                synthetic data accurately captures the ACWR-injury relationship from sports science literature—undertrained
                athletes face disproportionately higher injury risk per training unit, supporting the "fitness protects" hypothesis.
              </p>
            </div>
          </div>
        </section>

        {/* Keywords */}
        <section className="mb-12">
          <h2 className={`text-sm font-semibold ${isDark ? 'text-slate-300' : 'text-gray-700'} uppercase tracking-wide mb-3`}>Keywords</h2>
          <p className={`text-sm ${isDark ? 'text-slate-500' : 'text-gray-500'}`}>
            Injury prediction · Machine learning · Synthetic data · ACWR · Triathlon · Wearable sensors · XAI
          </p>
        </section>

        {/* Access Platform */}
        <section className={`border-t ${isDark ? 'border-slate-800' : 'border-gray-200'} pt-8`}>
          <h2 className={`text-sm font-semibold ${isDark ? 'text-slate-300' : 'text-gray-700'} uppercase tracking-wide mb-4`}>Access the Platform</h2>
          <div className="flex flex-wrap gap-4">
            <Link
              to="/pipeline"
              className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-500"
            >
              Open Research Platform
            </Link>
            <a
              href="https://github.com/brunobastosrodrigues/injury-prediction"
              target="_blank"
              rel="noopener noreferrer"
              className={`px-4 py-2 border ${isDark ? 'border-slate-600 text-slate-300 hover:bg-slate-800' : 'border-gray-300 text-gray-700 hover:bg-gray-100'} text-sm font-medium rounded inline-flex items-center gap-2`}
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
              </svg>
              View on GitHub
            </a>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className={`border-t ${isDark ? 'border-slate-800' : 'border-gray-200'} mt-16`}>
        <div className="max-w-4xl mx-auto px-6 py-8">
          <div className={`flex flex-col sm:flex-row justify-between items-center gap-4 text-sm ${isDark ? 'text-slate-500' : 'text-gray-500'}`}>
            <div>
              Embedded Sensing Group · University of St. Gallen
            </div>
            <button
              onClick={() => setShowCitation(true)}
              className={`${isDark ? 'text-slate-500 hover:text-slate-300' : 'text-gray-500 hover:text-gray-700'}`}
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
