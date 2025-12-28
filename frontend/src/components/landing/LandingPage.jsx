import { Link } from 'react-router-dom'
import { usePipeline } from '../../context/PipelineContext'
import { useEffect, useState } from 'react'
import CitationBlock from '../common/CitationBlock'
import MethodologyTooltip, { METHODOLOGY_TERMS } from '../common/MethodologyTooltip'

function LandingPage() {
  const { datasets, splits, models, refreshDatasets, refreshSplits, refreshModels } = usePipeline()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [showCitation, setShowCitation] = useState(false)

  useEffect(() => {
    refreshDatasets()
    refreshSplits()
    refreshModels()
  }, [refreshDatasets, refreshSplits, refreshModels])

  const pipelineSteps = [
    {
      number: '01',
      title: 'Data Synthesis',
      description: 'Stochastic simulation framework generating year-long training trajectories. Models periodization phases, physiological adaptation (CTL/ATL dynamics), and injury emergence using validated biomechanical principles.',
      icon: (
        <svg className="w-6 h-6 sm:w-8 sm:h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
        </svg>
      ),
      metrics: [
        { label: 'Sample Size', value: 'n=100-5000' },
        { label: 'Duration', value: '365 days' },
        { label: 'Features', value: '50+' }
      ],
      methodology: 'Addresses data scarcity in sports medicine research through controlled synthetic cohort generation.'
    },
    {
      number: '02',
      title: 'Feature Engineering',
      description: 'Temporal aggregation of training load biomarkers using established sports science constructs: rolling window statistics, exponentially weighted moving averages, and load ratio computations.',
      icon: (
        <svg className="w-6 h-6 sm:w-8 sm:h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      ),
      metrics: [
        { label: 'ACWR', value: '7d/28d ratio' },
        { label: 'CTL/ATL', value: 'EWMA' },
        { label: 'TSB', value: 'CTL-ATL' }
      ],
      methodology: 'Implements Banister impulse-response model and Gabbett workload ratio framework.'
    },
    {
      number: '03',
      title: 'Model Development',
      description: 'Supervised classification for 7-day prospective injury prediction. Compares L1-regularized logistic regression, ensemble methods (Random Forest), and gradient boosting (XGBoost).',
      icon: (
        <svg className="w-6 h-6 sm:w-8 sm:h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
        </svg>
      ),
      metrics: [
        { label: 'Lasso', value: 'L1 reg.' },
        { label: 'RF', value: 'n=200' },
        { label: 'XGBoost', value: 'n=400' }
      ],
      methodology: 'Athlete-based train/test split prevents data leakage from temporal autocorrelation.'
    },
    {
      number: '04',
      title: 'Model Evaluation',
      description: 'Comprehensive performance assessment: discrimination (ROC-AUC, PR-AUC), calibration, feature attribution (SHAP), and counterfactual analysis for intervention validation.',
      icon: (
        <svg className="w-6 h-6 sm:w-8 sm:h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
        </svg>
      ),
      metrics: [
        { label: 'ROC-AUC', value: 'Disc.' },
        { label: 'SHAP', value: 'XAI' },
        { label: 'What-If', value: 'Causal' }
      ],
      methodology: 'PR-AUC prioritized for imbalanced injury prediction (class ratio ~2-5%).'
    }
  ]

  const researchComponents = [
    {
      title: 'Synthetic Cohort Generation',
      description: 'Stochastic simulation incorporating periodization theory, training load dynamics, and injury risk mechanisms. Validated against empirical athlete distributions.',
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
        </svg>
      ),
      references: ['Banister et al. (1975)', 'Busso (2003)']
    },
    {
      title: 'Comparative Model Benchmarking',
      description: 'Standardized evaluation of sparse linear models (Lasso), bagged decision trees (Random Forest), and gradient boosting (XGBoost) under cross-validation protocols.',
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      references: ['Tibshirani (1996)', 'Chen & Guestrin (2016)']
    },
    {
      title: 'Individual-Level Risk Analysis',
      description: 'Athlete-specific risk stratification, temporal pattern extraction, and longitudinal trajectory visualization for mechanistic hypothesis generation.',
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      ),
      references: ['Borg (1998)', 'Foster (1998)']
    },
    {
      title: 'Counterfactual Simulation',
      description: 'Intervention effect estimation through perturbation-based analysis. Enables exploration of training load modification scenarios on predicted injury risk.',
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      references: ['Pearl (2009)', 'Mothilal et al. (2020)']
    },
    {
      title: 'Load Monitoring Framework',
      description: 'Implementation of established sports science metrics including ACWR, CTL/ATL/TSB with configurable rolling window aggregation and threshold-based classification.',
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
      references: ['Gabbett (2016)', 'Hulin et al. (2016)']
    },
    {
      title: 'Model Interpretability (XAI)',
      description: 'SHAP-based feature attribution, global and local explanations, and recommendation generation for transparent, actionable predictions.',
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" />
        </svg>
      ),
      references: ['Lundberg & Lee (2017)', 'Ribeiro et al. (2016)']
    }
  ]

  const stats = [
    { label: 'Generated Datasets', value: datasets.length, suffix: '' },
    { label: 'Processed Splits', value: splits.length, suffix: '' },
    { label: 'Trained Models', value: models.length, suffix: '' },
    { label: 'Prediction Horizon', value: 7, suffix: ' days' }
  ]

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-slate-950/95 backdrop-blur-sm border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center flex-shrink-0">
                <svg className="w-5 h-5 sm:w-6 sm:h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div className="hidden sm:block">
                <span className="text-white font-bold text-lg">Injury Risk Prediction</span>
                <span className="text-slate-500 text-sm ml-2 hidden md:inline">Research Platform</span>
              </div>
            </div>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-4">
              <button
                onClick={() => setShowCitation(!showCitation)}
                className="px-3 py-2 text-sm text-slate-300 hover:text-white transition-colors flex items-center gap-1.5"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                Cite
              </button>
              <Link
                to="/pipeline"
                className="px-4 py-2 text-sm text-slate-300 hover:text-white transition-colors"
              >
                ML Pipeline
              </Link>
              <Link
                to="/pipeline"
                className="px-5 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-500 transition-colors"
              >
                Open Platform
              </Link>
            </div>

            {/* Mobile Menu Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              {mobileMenuOpen ? (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              )}
            </button>
          </div>

          {/* Mobile Menu */}
          {mobileMenuOpen && (
            <div className="md:hidden py-4 border-t border-slate-800">
              <div className="space-y-2">
                <button
                  onClick={() => { setShowCitation(!showCitation); setMobileMenuOpen(false) }}
                  className="block w-full text-left px-4 py-3 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                >
                  Cite This Work
                </button>
                <Link
                  to="/pipeline"
                  onClick={() => setMobileMenuOpen(false)}
                  className="block px-4 py-3 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                >
                  ML Pipeline
                </Link>
                <Link
                  to="/athletes"
                  onClick={() => setMobileMenuOpen(false)}
                  className="block px-4 py-3 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                >
                  Cohort Analysis
                </Link>
                <Link
                  to="/pipeline"
                  onClick={() => setMobileMenuOpen(false)}
                  className="block px-4 py-3 mt-2 text-center font-medium text-white bg-blue-600 rounded-lg"
                >
                  Open Platform
                </Link>
              </div>
            </div>
          )}
        </div>
      </nav>

      {/* Citation Modal */}
      {showCitation && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm" onClick={() => setShowCitation(false)}>
          <div className="max-w-lg w-full" onClick={e => e.stopPropagation()}>
            <CitationBlock />
            <button
              onClick={() => setShowCitation(false)}
              className="mt-4 w-full py-2 text-sm text-slate-400 hover:text-white transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}

      {/* Hero Section */}
      <section className="relative pt-24 sm:pt-32 pb-16 sm:pb-20 overflow-hidden">
        {/* Subtle Background */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -right-40 w-60 sm:w-80 h-60 sm:h-80 bg-blue-500/10 rounded-full blur-[100px]" />
          <div className="absolute top-20 -left-40 w-60 sm:w-80 h-60 sm:h-80 bg-blue-600/10 rounded-full blur-[100px]" />
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-full h-px bg-gradient-to-r from-transparent via-slate-700 to-transparent" />
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-4xl mx-auto">
            {/* Academic Badge */}
            <div className="inline-flex flex-col sm:flex-row items-center gap-2 sm:gap-3 px-4 py-2 rounded-full bg-slate-900 border border-slate-800 mb-6 sm:mb-8">
              <div className="flex items-center">
                <svg className="w-5 h-5 text-green-400 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l9-5-9-5-9 5 9 5z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
                </svg>
                <span className="text-sm text-slate-300">Embedded Sensing Group</span>
              </div>
              <span className="hidden sm:inline text-slate-600">|</span>
              <span className="text-sm text-slate-400">University of St. Gallen</span>
            </div>

            <h1 className="text-3xl sm:text-4xl lg:text-6xl font-bold text-white mb-4 sm:mb-6 leading-tight tracking-tight">
              Prospective Injury Risk
              <span className="block text-blue-400">
                Prediction in Triathletes
              </span>
            </h1>

            <p className="text-base sm:text-lg text-slate-400 mb-8 sm:mb-10 max-w-2xl mx-auto leading-relaxed px-4">
              A computational framework integrating synthetic cohort generation, domain-informed feature engineering,
              and supervised machine learning for 7-day prospective injury risk stratification in endurance athletes.
            </p>

            {/* Key Methodology Terms */}
            <div className="flex flex-wrap items-center justify-center gap-2 mb-8 text-xs sm:text-sm">
              <span className="px-3 py-1.5 bg-slate-800/50 border border-slate-700 rounded-full text-slate-300">
                <MethodologyTooltip {...METHODOLOGY_TERMS.ACWR}>ACWR Monitoring</MethodologyTooltip>
              </span>
              <span className="px-3 py-1.5 bg-slate-800/50 border border-slate-700 rounded-full text-slate-300">
                <MethodologyTooltip {...METHODOLOGY_TERMS.CTL}>CTL/ATL Dynamics</MethodologyTooltip>
              </span>
              <span className="px-3 py-1.5 bg-slate-800/50 border border-slate-700 rounded-full text-slate-300">
                <MethodologyTooltip {...METHODOLOGY_TERMS.SHAP}>SHAP Explanations</MethodologyTooltip>
              </span>
              <span className="px-3 py-1.5 bg-slate-800/50 border border-slate-700 rounded-full text-slate-300">
                Counterfactual Analysis
              </span>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4 mb-12 sm:mb-16 px-4">
              <Link
                to="/pipeline"
                className="w-full sm:w-auto group px-6 sm:px-8 py-3 sm:py-4 text-base font-semibold text-white bg-blue-600 rounded-xl hover:bg-blue-500 transition-colors flex items-center justify-center"
              >
                Explore ML Pipeline
                <svg className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </Link>
              <Link
                to="/athletes"
                className="w-full sm:w-auto px-6 sm:px-8 py-3 sm:py-4 text-base font-semibold text-slate-300 bg-slate-800 border border-slate-700 rounded-xl hover:bg-slate-700 hover:text-white transition-colors flex items-center justify-center"
              >
                <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                Cohort Analysis
              </Link>
            </div>

            {/* Platform Stats */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 px-4 sm:px-0">
              {stats.map((stat, index) => (
                <div key={index} className="p-4 sm:p-5 rounded-xl bg-slate-900/50 border border-slate-800">
                  <div className="text-2xl sm:text-3xl font-bold text-white mb-1 font-mono">
                    {stat.value}{stat.suffix}
                  </div>
                  <div className="text-xs sm:text-sm text-slate-500">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Methodology Pipeline Section */}
      <section className="py-16 sm:py-24 relative">
        <div className="absolute inset-0 bg-gradient-to-b from-slate-950 via-slate-900/50 to-slate-950" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-10 sm:mb-16">
            <h2 className="text-sm font-semibold text-blue-400 uppercase tracking-wider mb-3">
              Methodology
            </h2>
            <h3 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-white mb-4">
              Computational Pipeline Architecture
            </h3>
            <p className="text-base sm:text-lg text-slate-400 max-w-2xl mx-auto">
              Four-stage workflow from synthetic cohort generation through model evaluation
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
            {pipelineSteps.map((step, index) => (
              <div
                key={index}
                className="group relative p-5 sm:p-6 rounded-xl bg-slate-900/50 border border-slate-800 hover:border-slate-700 transition-colors"
              >
                {/* Step number */}
                <div className="absolute -top-3 -right-3 w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs sm:text-sm font-bold">
                  {step.number}
                </div>

                {/* Icon */}
                <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-slate-800 flex items-center justify-center text-blue-400 mb-4 group-hover:bg-blue-600/20 transition-colors">
                  {step.icon}
                </div>

                <h4 className="text-base sm:text-lg font-semibold text-white mb-2">{step.title}</h4>
                <p className="text-xs sm:text-sm text-slate-400 mb-3 leading-relaxed">{step.description}</p>

                {/* Methodology note */}
                <p className="text-xs text-slate-500 italic mb-4 leading-relaxed">{step.methodology}</p>

                {/* Metrics */}
                <div className="flex flex-wrap gap-1.5 sm:gap-2">
                  {step.metrics.map((metric, i) => (
                    <div key={i} className="px-2 sm:px-3 py-1 sm:py-1.5 rounded-lg bg-slate-800 text-xs">
                      <span className="text-slate-500">{metric.label}:</span>
                      <span className="text-slate-300 ml-1 font-medium">{metric.value}</span>
                    </div>
                  ))}
                </div>

                {/* Arrow connector */}
                {index < pipelineSteps.length - 1 && (
                  <div className="hidden lg:block absolute top-1/2 -right-3 w-6 h-6 text-slate-700">
                    <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Research Components Section */}
      <section className="py-16 sm:py-24 relative">
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-10 sm:mb-16">
            <h2 className="text-sm font-semibold text-blue-400 uppercase tracking-wider mb-3">
              Technical Components
            </h2>
            <h3 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-white mb-4">
              Research Implementation
            </h3>
            <p className="text-base sm:text-lg text-slate-400 max-w-2xl mx-auto">
              Modular framework grounded in established sports science and machine learning literature
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
            {researchComponents.map((feature, index) => (
              <div
                key={index}
                className="p-5 sm:p-6 rounded-xl bg-slate-900/50 border border-slate-800 hover:border-slate-700 transition-colors"
              >
                <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-400 mb-4">
                  {feature.icon}
                </div>
                <h4 className="text-base sm:text-lg font-semibold text-white mb-2">{feature.title}</h4>
                <p className="text-xs sm:text-sm text-slate-400 leading-relaxed mb-3">{feature.description}</p>

                {/* References */}
                {feature.references && (
                  <div className="pt-3 border-t border-slate-800">
                    <div className="text-xs text-slate-500">
                      <span className="font-medium">Key References:</span>
                      <span className="ml-1 italic">{feature.references.join(', ')}</span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Research Context Section */}
      <section className="py-16 sm:py-24 relative">
        <div className="absolute inset-0 bg-gradient-to-b from-slate-950 via-slate-900/50 to-slate-950" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-8 sm:gap-12 items-start">
            <div>
              <h2 className="text-sm font-semibold text-blue-400 uppercase tracking-wider mb-3">
                Research Context
              </h2>
              <h3 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-white mb-6">
                Computational Modeling of Training-Related Injury Risk
              </h3>
              <div className="space-y-4 text-slate-400 text-sm sm:text-base">
                <p className="leading-relaxed">
                  Developed by the <strong className="text-white">Embedded Sensing Group</strong> at the
                  <strong className="text-white"> University of St. Gallen</strong>, this platform implements
                  a supervised learning approach to prospective injury risk stratification in endurance athletes.
                </p>
                <p className="leading-relaxed">
                  The synthetic data component addresses a critical challenge in sports medicine research:
                  the scarcity of large-scale, labeled injury datasets. Our stochastic simulation framework
                  generates realistic annual training trajectories incorporating:
                </p>
                <ul className="list-disc list-inside space-y-1 text-slate-400 ml-2">
                  <li>Periodization phases (base, build, peak, recovery)</li>
                  <li>Physiological adaptation via impulse-response models</li>
                  <li>Load-dependent injury risk mechanisms</li>
                  <li>Individual athlete heterogeneity</li>
                </ul>
                <p className="leading-relaxed">
                  Feature engineering incorporates established constructs from the training load monitoring literature,
                  including Gabbett's <MethodologyTooltip {...METHODOLOGY_TERMS.ACWR}>ACWR framework</MethodologyTooltip> and
                  Coggan's <MethodologyTooltip {...METHODOLOGY_TERMS.TSB}>performance management chart</MethodologyTooltip>.
                </p>
              </div>
            </div>

            <div className="space-y-6">
              {/* Biomarkers Panel */}
              <div className="p-6 sm:p-8 rounded-xl bg-slate-900/80 border border-slate-800">
                <h4 className="text-base sm:text-lg font-semibold text-white mb-6">Core Physiological Biomarkers</h4>
                <div className="space-y-3 sm:space-y-4">
                  {[
                    { name: 'ACWR (Acute:Chronic Workload Ratio)', desc: 'Load progression quantification', formula: '7d / 28d rolling mean' },
                    { name: 'CTL (Chronic Training Load)', desc: 'Fitness accumulation proxy', formula: '42-day EWMA of TSS' },
                    { name: 'ATL (Acute Training Load)', desc: 'Fatigue accumulation proxy', formula: '7-day EWMA of TSS' },
                    { name: 'TSB (Training Stress Balance)', desc: 'Form indicator', formula: 'CTL − ATL' },
                    { name: 'HRV (Heart Rate Variability)', desc: 'Autonomic recovery marker', formula: 'RMSSD, HF power' },
                    { name: 'Sleep Quality Index', desc: 'Recovery composite', formula: 'Duration × efficiency' }
                  ].map((metric, i) => (
                    <div key={i} className="flex items-start">
                      <div className="w-2 h-2 rounded-full bg-blue-400 mt-2 mr-3 flex-shrink-0" />
                      <div className="flex-1">
                        <span className="text-white font-medium text-sm sm:text-base">{metric.name}</span>
                        <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-2">
                          <span className="text-slate-500 text-xs">{metric.desc}</span>
                          <span className="hidden sm:inline text-slate-600">—</span>
                          <span className="text-slate-600 text-xs font-mono">{metric.formula}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Export/Reproducibility Note */}
              <div className="p-4 rounded-lg bg-green-500/5 border border-green-500/20">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                  <div>
                    <h5 className="text-sm font-medium text-green-400 mb-1">Reproducibility Support</h5>
                    <p className="text-xs text-slate-400">
                      All results can be exported with full configuration metadata (random seeds, hyperparameters, dataset IDs)
                      for reproducible research. Charts exportable as SVG/PNG for publication.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 sm:py-24 relative">
        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="p-8 sm:p-12 rounded-xl bg-slate-900/50 border border-slate-800">
            <h3 className="text-2xl sm:text-3xl font-bold text-white mb-4">
              Interactive Research Platform
            </h3>
            <p className="text-base sm:text-lg text-slate-400 mb-6 sm:mb-8 max-w-xl mx-auto">
              Explore the complete ML pipeline: generate synthetic cohorts, engineer features,
              train models, and analyze results with full export capability.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4">
              <Link
                to="/data-generation"
                className="w-full sm:w-auto px-6 sm:px-8 py-3 sm:py-4 text-base font-semibold text-white bg-blue-600 rounded-xl hover:bg-blue-500 transition-colors"
              >
                Generate Synthetic Data
              </Link>
              <Link
                to="/pipeline"
                className="w-full sm:w-auto px-6 sm:px-8 py-3 sm:py-4 text-base font-semibold text-slate-300 bg-slate-800 border border-slate-700 rounded-xl hover:bg-slate-700 hover:text-white transition-colors"
              >
                View Pipeline
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 sm:py-12 border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col items-center gap-6">
            {/* University Branding */}
            <div className="flex flex-col sm:flex-row items-center gap-3 sm:gap-4">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <span className="text-slate-400 text-sm">Injury Risk Prediction Research Platform</span>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row items-center gap-2 sm:gap-4 text-center">
              <div className="flex items-center text-slate-400 text-sm">
                <svg className="w-4 h-4 mr-2 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l9-5-9-5-9 5 9 5z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
                </svg>
                <span>Embedded Sensing Group</span>
              </div>
              <span className="hidden sm:inline text-slate-600">|</span>
              <span className="text-slate-500 text-sm">University of St. Gallen</span>
            </div>

            <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-2 text-xs text-slate-600">
              <span>Flask + React + Celery</span>
              <span className="hidden sm:inline">|</span>
              <span>Lasso, Random Forest, XGBoost</span>
              <span className="hidden sm:inline">|</span>
              <span>SHAP Explanations</span>
            </div>

            <button
              onClick={() => setShowCitation(true)}
              className="text-xs text-slate-500 hover:text-slate-400 transition-colors"
            >
              How to cite this work →
            </button>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default LandingPage
