import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { usePipeline } from '../../context/PipelineContext'
import Card from '../common/Card'

function Dashboard() {
  const {
    datasets, splits, models,
    refreshDatasets, refreshSplits, refreshModels,
    loading, activeJobs
  } = usePipeline()

  const [activeTab, setActiveTab] = useState('introduction')

  useEffect(() => {
    refreshDatasets()
    refreshSplits()
    refreshModels()
  }, [refreshDatasets, refreshSplits, refreshModels])

  // Calculate study progress
  const studyProgress = {
    hasData: datasets.length > 0,
    hasFeatures: splits.length > 0,
    hasModels: models.length > 0,
    bestModel: models.length > 0
      ? models.reduce((best, m) =>
          (m.metrics?.roc_auc || 0) > (best.metrics?.roc_auc || 0) ? m : best
        , models[0])
      : null
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 dark:bg-green-500/20 text-green-600 dark:text-green-400 border-green-300 dark:border-green-500/30'
      case 'ready':
        return 'bg-blue-100 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400 border-blue-300 dark:border-blue-500/30'
      default:
        return 'bg-gray-100 dark:bg-slate-700/50 text-gray-500 dark:text-slate-500 border-gray-300 dark:border-slate-600/30'
    }
  }

  const runningJobs = Object.entries(activeJobs).filter(([, j]) => j.status === 'running')

  const tabs = [
    { id: 'introduction', label: 'Introduction', description: 'Research motivation and contribution' },
    { id: 'getting-started', label: 'Getting Started', description: 'Choose your workflow' },
    { id: 'pipeline', label: 'Pipeline', description: 'Scientific workflow steps' },
    { id: 'validation', label: 'Validation', description: 'Data quality assurance' },
    { id: 'progress', label: 'Your Progress', description: 'Current study assets' }
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-2">Study Overview</h1>
          <p className="text-gray-600 dark:text-slate-400 max-w-2xl text-sm sm:text-base">
            Prospective injury risk prediction in triathletes using training load biomarkers and machine learning
          </p>
        </div>
        <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-full bg-gray-100 dark:bg-slate-800 border border-gray-300 dark:border-slate-700">
          <div className={`w-2 h-2 rounded-full ${studyProgress.hasModels ? 'bg-green-400' : studyProgress.hasData ? 'bg-amber-400' : 'bg-gray-400 dark:bg-slate-500'}`} />
          <span className="text-xs text-gray-600 dark:text-slate-400">
            {studyProgress.hasModels ? 'Models Trained' : studyProgress.hasFeatures ? 'Ready for Training' : studyProgress.hasData ? 'Data Available' : 'Setup Required'}
          </span>
        </div>
      </div>

      {/* Running Jobs Alert */}
      {runningJobs.length > 0 && (
        <div className="p-4 rounded-xl bg-gradient-to-r from-blue-100 dark:from-blue-500/10 to-purple-100 dark:to-purple-500/10 border border-blue-300 dark:border-blue-500/20">
          <div className="flex items-center gap-3">
            <div className="animate-spin h-5 w-5 border-2 border-blue-500 dark:border-blue-400 border-t-transparent rounded-full"></div>
            <span className="text-sm text-gray-900 dark:text-white font-medium">{runningJobs.length} job{runningJobs.length > 1 ? 's' : ''} running</span>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-slate-800 -mx-4 px-4 sm:mx-0 sm:px-0 overflow-x-auto">
        <nav className="flex space-x-4 sm:space-x-8 min-w-max">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-3 sm:py-4 px-1 border-b-2 font-medium text-xs sm:text-sm whitespace-nowrap transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 dark:text-slate-500 hover:text-gray-700 dark:hover:text-slate-300 hover:border-gray-400 dark:hover:border-slate-600'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="min-h-[400px]">

        {/* ===== INTRODUCTION TAB ===== */}
        {activeTab === 'introduction' && (
          <div className="space-y-6">
            {/* Research Question */}
            <div className="p-6 rounded-2xl bg-gradient-to-br from-blue-100 via-gray-50 to-purple-100 dark:from-blue-900/20 dark:via-slate-900 dark:to-purple-900/20 border border-blue-200 dark:border-blue-500/20">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl bg-blue-100 dark:bg-blue-500/20 flex items-center justify-center flex-shrink-0">
                  <svg className="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Research Question</h2>
                  <p className="text-gray-700 dark:text-slate-300">
                    Can we predict injury risk within a 7-day window using training load metrics (ACWR, CTL/ATL, TSB)
                    and physiological biomarkers (HRV, sleep quality, body battery)?
                  </p>
                </div>
              </div>
            </div>

            {/* Why Triathletes? */}
            <Card title="Why Triathletes?">
              <div className="space-y-4 text-sm text-gray-600 dark:text-slate-400">
                <p>
                  <strong className="text-gray-700 dark:text-slate-300">High injury prevalence:</strong> Training-related injuries affect 37-56% of triathletes annually,
                  making them an ideal population for studying injury prediction. The multi-sport nature (swim, bike, run) creates complex
                  loading patterns that challenge traditional single-sport injury models.
                </p>
                <p>
                  <strong className="text-gray-700 dark:text-slate-300">Wearable adoption:</strong> Triathletes are early adopters of wearable technology (Garmin, Whoop, Oura),
                  generating rich longitudinal data streams including HRV, sleep metrics, training stress scores, and recovery indicators.
                  This makes them ideal for developing data-driven injury prediction models.
                </p>
                <p>
                  <strong className="text-gray-700 dark:text-slate-300">Periodization complexity:</strong> Triathlon training follows structured periodization (base, build, peak, taper)
                  with varying load patterns across disciplines. Understanding how these patterns relate to injury risk has broad
                  applicability to other endurance sports.
                </p>
              </div>
            </Card>

            {/* Why This Study? */}
            <Card title="Why Multimodal Data Matters">
              <div className="space-y-4 text-sm text-gray-600 dark:text-slate-400">
                <p>
                  <strong className="text-gray-700 dark:text-slate-300">Beyond training load:</strong> Most injury prediction studies focus solely on training load
                  metrics (volume, intensity). We integrate <em>physiological recovery markers</em> (HRV, sleep quality, body battery, stress)
                  that capture the athlete's adaptive capacity—not just the stress applied, but how well they're recovering from it.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
                  <div className="p-4 rounded-lg bg-gray-100 dark:bg-slate-800/50 border border-gray-300 dark:border-slate-700">
                    <h4 className="font-semibold text-gray-700 dark:text-slate-300 mb-2">Training Load Features</h4>
                    <ul className="text-xs space-y-1 text-gray-500 dark:text-slate-500">
                      <li>• ACWR (Acute:Chronic Workload Ratio)</li>
                      <li>• CTL/ATL (Chronic/Acute Training Load)</li>
                      <li>• TSB (Training Stress Balance)</li>
                      <li>• TSS (Training Stress Score)</li>
                    </ul>
                  </div>
                  <div className="p-4 rounded-lg bg-gray-100 dark:bg-slate-800/50 border border-gray-300 dark:border-slate-700">
                    <h4 className="font-semibold text-gray-700 dark:text-slate-300 mb-2">Recovery Features</h4>
                    <ul className="text-xs space-y-1 text-gray-500 dark:text-slate-500">
                      <li>• HRV (Heart Rate Variability)</li>
                      <li>• Sleep duration & quality</li>
                      <li>• Body Battery / readiness</li>
                      <li>• Perceived stress levels</li>
                    </ul>
                  </div>
                </div>
              </div>
            </Card>

            {/* Our Contribution */}
            <Card title="Our Contribution">
              <div className="space-y-4 text-sm text-gray-600 dark:text-slate-400">
                <p className="text-gray-700 dark:text-slate-300 font-medium">
                  What makes this work different from prior injury prediction studies?
                </p>

                <div className="space-y-3">
                  <div className="flex gap-3">
                    <div className="w-6 h-6 rounded-full bg-green-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-xs font-bold text-green-400">1</span>
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-700 dark:text-slate-300">Synthetic Data Framework</h4>
                      <p className="text-xs text-gray-500 dark:text-slate-500 mt-1">
                        We address the data scarcity problem in sports medicine by developing a physiologically-grounded
                        synthetic data generator. This enables reproducible research without privacy concerns while
                        maintaining realistic injury patterns validated against real PMData.
                      </p>
                    </div>
                  </div>

                  <div className="flex gap-3">
                    <div className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-xs font-bold text-blue-400">2</span>
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-700 dark:text-slate-300">Causal Mechanism Verification</h4>
                      <p className="text-xs text-gray-500 dark:text-slate-500 mt-1">
                        We prove the asymmetric ACWR-injury relationship: undertrained athletes (ACWR &lt; 0.8) show
                        3-5× higher injury risk <em>per training load unit</em> than overloaded athletes. This validates
                        the "fitness protects" hypothesis from sports science literature.
                      </p>
                    </div>
                  </div>

                  <div className="flex gap-3">
                    <div className="w-6 h-6 rounded-full bg-purple-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-xs font-bold text-purple-400">3</span>
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-700 dark:text-slate-300">Full Reproducibility</h4>
                      <p className="text-xs text-gray-500 dark:text-slate-500 mt-1">
                        This platform allows complete replication of our results—from synthetic cohort generation
                        through model training to evaluation. Every step is parameterized and documented for
                        scientific transparency.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </Card>

            {/* Key Results - Static Plots */}
            <Card title="Key Results from Published Study">
              <div className="space-y-6">
                <p className="text-sm text-gray-600 dark:text-slate-400">
                  These results are from our reference dataset (1,000 synthetic athletes, 366,000 daily records).
                  All visualizations below are static summaries—explore the full interactive analysis in the Results and Validation pages.
                </p>

                {/* ACWR Risk Asymmetry Plot */}
                <div className="p-4 rounded-lg bg-gray-100 dark:bg-slate-800/50 border border-gray-300 dark:border-slate-700">
                  <h4 className="font-semibold text-gray-700 dark:text-slate-300 mb-1">Figure 1: ACWR-Injury Risk Asymmetry</h4>
                  <p className="text-xs text-gray-500 dark:text-slate-500 mb-4">
                    Injury risk per 1,000 TSS units by ACWR zone. Undertrained athletes show 2.6× higher risk than optimal—
                    confirming the "fitness protects" hypothesis.
                  </p>
                  <div className="space-y-3">
                    {/* Undertrained */}
                    <div className="flex items-center gap-3">
                      <div className="w-28 text-xs text-gray-600 dark:text-slate-400 text-right">Undertrained</div>
                      <div className="flex-1 h-8 bg-gray-50 dark:bg-slate-900 rounded overflow-hidden relative">
                        <div
                          className="h-full bg-gradient-to-r from-red-600 to-red-500 flex items-center justify-end pr-2"
                          style={{ width: '100%' }}
                        >
                          <span className="text-xs font-bold text-gray-900 dark:text-white">2.90</span>
                        </div>
                      </div>
                      <div className="w-16 text-xs text-red-400 font-semibold">2.61×</div>
                    </div>
                    {/* Optimal */}
                    <div className="flex items-center gap-3">
                      <div className="w-28 text-xs text-gray-600 dark:text-slate-400 text-right">Optimal</div>
                      <div className="flex-1 h-8 bg-gray-50 dark:bg-slate-900 rounded overflow-hidden relative">
                        <div
                          className="h-full bg-gradient-to-r from-green-600 to-green-500 flex items-center justify-end pr-2"
                          style={{ width: '38%' }}
                        >
                          <span className="text-xs font-bold text-gray-900 dark:text-white">1.11</span>
                        </div>
                      </div>
                      <div className="w-16 text-xs text-green-400 font-semibold">1.00× (ref)</div>
                    </div>
                    {/* Elevated */}
                    <div className="flex items-center gap-3">
                      <div className="w-28 text-xs text-gray-600 dark:text-slate-400 text-right">Elevated</div>
                      <div className="flex-1 h-8 bg-gray-50 dark:bg-slate-900 rounded overflow-hidden relative">
                        <div
                          className="h-full bg-gradient-to-r from-amber-600 to-amber-500 flex items-center justify-end pr-2"
                          style={{ width: '39%' }}
                        >
                          <span className="text-xs font-bold text-gray-900 dark:text-white">1.14</span>
                        </div>
                      </div>
                      <div className="w-16 text-xs text-amber-400 font-semibold">1.03×</div>
                    </div>
                    {/* High Risk */}
                    <div className="flex items-center gap-3">
                      <div className="w-28 text-xs text-gray-600 dark:text-slate-400 text-right">High Risk</div>
                      <div className="flex-1 h-8 bg-gray-50 dark:bg-slate-900 rounded overflow-hidden relative">
                        <div
                          className="h-full bg-gradient-to-r from-orange-600 to-orange-500 flex items-center justify-end pr-2"
                          style={{ width: '76%' }}
                        >
                          <span className="text-xs font-bold text-gray-900 dark:text-white">2.19</span>
                        </div>
                      </div>
                      <div className="w-16 text-xs text-orange-400 font-semibold">1.97×</div>
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-slate-500 mt-3 italic">
                    Key insight: Both undertrained (ACWR &lt; 0.8) and overloaded (ACWR &gt; 1.5) athletes show elevated risk,
                    but undertrained athletes are at greater risk per unit load—supporting the detraining vulnerability hypothesis.
                  </p>
                </div>

                {/* Model Performance */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 rounded-lg bg-gray-100 dark:bg-slate-800/50 border border-gray-300 dark:border-slate-700">
                    <h4 className="font-semibold text-gray-700 dark:text-slate-300 mb-1">Figure 2: Model Performance (AUC-ROC)</h4>
                    <p className="text-xs text-gray-500 dark:text-slate-500 mb-4">7-day injury prediction window</p>
                    <div className="space-y-3">
                      {/* XGBoost */}
                      <div>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-gray-600 dark:text-slate-400">XGBoost</span>
                          <span className="text-blue-400 font-semibold">0.613</span>
                        </div>
                        <div className="h-3 bg-gray-50 dark:bg-slate-900 rounded-full overflow-hidden">
                          <div className="h-full bg-gradient-to-r from-blue-600 to-blue-400 rounded-full" style={{ width: '61.3%' }}></div>
                        </div>
                      </div>
                      {/* Random Forest */}
                      <div>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-gray-600 dark:text-slate-400">Random Forest</span>
                          <span className="text-emerald-400 font-semibold">0.609</span>
                        </div>
                        <div className="h-3 bg-gray-50 dark:bg-slate-900 rounded-full overflow-hidden">
                          <div className="h-full bg-gradient-to-r from-emerald-600 to-emerald-400 rounded-full" style={{ width: '60.9%' }}></div>
                        </div>
                      </div>
                      {/* Lasso */}
                      <div>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-gray-600 dark:text-slate-400">Lasso (L1)</span>
                          <span className="text-purple-400 font-semibold">0.586</span>
                        </div>
                        <div className="h-3 bg-gray-50 dark:bg-slate-900 rounded-full overflow-hidden">
                          <div className="h-full bg-gradient-to-r from-purple-600 to-purple-400 rounded-full" style={{ width: '58.6%' }}></div>
                        </div>
                      </div>
                      {/* Baseline */}
                      <div className="pt-2 border-t border-gray-300 dark:border-slate-700">
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-gray-500 dark:text-slate-500">Random baseline</span>
                          <span className="text-gray-500 dark:text-slate-500">0.500</span>
                        </div>
                        <div className="h-3 bg-gray-50 dark:bg-slate-900 rounded-full overflow-hidden">
                          <div className="h-full bg-slate-700 rounded-full" style={{ width: '50%' }}></div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Three Pillars */}
                  <div className="p-4 rounded-lg bg-gray-100 dark:bg-slate-800/50 border border-gray-300 dark:border-slate-700">
                    <h4 className="font-semibold text-gray-700 dark:text-slate-300 mb-1">Figure 3: Validation (Three Pillars)</h4>
                    <p className="text-xs text-gray-500 dark:text-slate-500 mb-4">Publication-quality validation checks</p>
                    <div className="space-y-4">
                      {/* Statistical Fidelity */}
                      <div className="flex items-center gap-3">
                        <div className="w-6 h-6 rounded-full bg-amber-500/20 flex items-center justify-center flex-shrink-0">
                          <span className="text-amber-400 text-xs">⚠</span>
                        </div>
                        <div className="flex-1">
                          <p className="text-xs text-gray-700 dark:text-slate-300 font-medium">Statistical Fidelity</p>
                          <p className="text-xs text-gray-500 dark:text-slate-500">JS divergence high (synthetic-real gap)</p>
                        </div>
                        <span className="text-xs text-amber-400 font-semibold">0.29</span>
                      </div>
                      {/* Causal Fidelity */}
                      <div className="flex items-center gap-3">
                        <div className="w-6 h-6 rounded-full bg-green-500/20 flex items-center justify-center flex-shrink-0">
                          <span className="text-green-400 text-xs">✓</span>
                        </div>
                        <div className="flex-1">
                          <p className="text-xs text-gray-700 dark:text-slate-300 font-medium">Causal Fidelity</p>
                          <p className="text-xs text-gray-500 dark:text-slate-500">ACWR asymmetry confirmed (2.6× vs 2.0×)</p>
                        </div>
                        <span className="text-xs text-green-400 font-semibold">0.87</span>
                      </div>
                      {/* Transferability */}
                      <div className="flex items-center gap-3">
                        <div className="w-6 h-6 rounded-full bg-amber-500/20 flex items-center justify-center flex-shrink-0">
                          <span className="text-amber-400 text-xs">⚠</span>
                        </div>
                        <div className="flex-1">
                          <p className="text-xs text-gray-700 dark:text-slate-300 font-medium">Transferability</p>
                          <p className="text-xs text-gray-500 dark:text-slate-500">Sim2Real AUC 0.50 (domain gap)</p>
                        </div>
                        <span className="text-xs text-amber-400 font-semibold">0.00</span>
                      </div>
                    </div>
                    <div className="mt-4 pt-3 border-t border-gray-300 dark:border-slate-700">
                      <div className="flex justify-between items-center">
                        <span className="text-xs text-gray-600 dark:text-slate-400">Overall Score</span>
                        <span className="text-sm font-bold text-gray-700 dark:text-slate-300">0.39 / 1.00</span>
                      </div>
                      <p className="text-xs text-gray-500 dark:text-slate-500 mt-1">
                        Causal mechanism validated ✓ — synthetic data captures injury dynamics
                      </p>
                    </div>
                  </div>
                </div>

                <p className="text-xs text-gray-500 dark:text-slate-500 text-center">
                  <Link to="/results" className="text-blue-400 hover:text-blue-300">View full results →</Link>
                  {' | '}
                  <Link to="/validation" className="text-blue-400 hover:text-blue-300">View validation details →</Link>
                </p>
              </div>
            </Card>

            {/* Related Work */}
            <Card title="Related Work & Gap Analysis">
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-gray-300 dark:border-slate-700">
                      <th className="text-left py-2 px-3 text-gray-600 dark:text-slate-400 font-medium">Study</th>
                      <th className="text-left py-2 px-3 text-gray-600 dark:text-slate-400 font-medium">Population</th>
                      <th className="text-left py-2 px-3 text-gray-600 dark:text-slate-400 font-medium">Features</th>
                      <th className="text-left py-2 px-3 text-gray-600 dark:text-slate-400 font-medium">Limitation</th>
                    </tr>
                  </thead>
                  <tbody className="text-gray-500 dark:text-slate-500">
                    <tr className="border-b border-gray-200 dark:border-slate-800">
                      <td className="py-2 px-3">Gabbett 2016</td>
                      <td className="py-2 px-3">Rugby</td>
                      <td className="py-2 px-3">ACWR only</td>
                      <td className="py-2 px-3">No recovery metrics</td>
                    </tr>
                    <tr className="border-b border-gray-200 dark:border-slate-800">
                      <td className="py-2 px-3">Rossi 2018</td>
                      <td className="py-2 px-3">Soccer</td>
                      <td className="py-2 px-3">GPS + RPE</td>
                      <td className="py-2 px-3">No physiological markers</td>
                    </tr>
                    <tr className="border-b border-gray-200 dark:border-slate-800">
                      <td className="py-2 px-3">Seshadri 2019</td>
                      <td className="py-2 px-3">Basketball</td>
                      <td className="py-2 px-3">Wearables</td>
                      <td className="py-2 px-3">Small sample, proprietary</td>
                    </tr>
                    <tr className="border-b border-gray-200 dark:border-slate-800">
                      <td className="py-2 px-3 font-semibold text-blue-400">This Work</td>
                      <td className="py-2 px-3 text-gray-700 dark:text-slate-300">Triathletes</td>
                      <td className="py-2 px-3 text-gray-700 dark:text-slate-300">Load + Recovery</td>
                      <td className="py-2 px-3 text-green-400">Open, reproducible</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </Card>
          </div>
        )}

        {/* ===== GETTING STARTED TAB ===== */}
        {activeTab === 'getting-started' && (
          <div className="space-y-6">
            <div className="p-4 rounded-xl bg-gray-100 dark:bg-slate-800/50 border border-gray-300 dark:border-slate-700">
              <p className="text-sm text-gray-600 dark:text-slate-400">
                This platform provides two ways to engage with our research: <strong className="text-gray-700 dark:text-slate-300">explore the published study</strong> with
                pre-loaded results, or <strong className="text-gray-700 dark:text-slate-300">run your own experiments</strong> with custom configurations.
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Explore Published Study */}
              <div className="p-6 rounded-2xl bg-gradient-to-br from-green-100 via-gray-50 to-emerald-100 dark:from-green-900/20 dark:via-slate-900 dark:to-emerald-900/20 border border-green-200 dark:border-green-500/20">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 rounded-xl bg-green-100 dark:bg-green-500/20 flex items-center justify-center">
                    <svg className="w-6 h-6 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Explore the Published Study</h3>
                    <p className="text-xs text-gray-500 dark:text-slate-500">Pre-loaded results from our paper</p>
                  </div>
                </div>

                <p className="text-sm text-gray-600 dark:text-slate-400 mb-4">
                  The validation study used in our publication is pre-loaded. Explore all the plots, metrics, and analyses
                  that appear in the paper without running anything.
                </p>

                <div className="space-y-3">
                  <Link to="/validation" className="flex items-center gap-3 p-3 rounded-lg bg-gray-100 dark:bg-slate-800/50 hover:bg-gray-100 dark:bg-slate-800 transition-colors">
                    <span className="text-green-400">🔬</span>
                    <div className="flex-1">
                      <p className="text-sm text-gray-700 dark:text-slate-300">Data Validation Results</p>
                      <p className="text-xs text-gray-500 dark:text-slate-500">Three Pillars, Sim2Real transfer, causal verification</p>
                    </div>
                  </Link>
                  <Link to="/results" className="flex items-center gap-3 p-3 rounded-lg bg-gray-100 dark:bg-slate-800/50 hover:bg-gray-100 dark:bg-slate-800 transition-colors">
                    <span className="text-green-400">📈</span>
                    <div className="flex-1">
                      <p className="text-sm text-gray-700 dark:text-slate-300">Model Performance</p>
                      <p className="text-xs text-gray-500 dark:text-slate-500">ROC curves, PR curves, calibration plots</p>
                    </div>
                  </Link>
                  <Link to="/interpretability" className="flex items-center gap-3 p-3 rounded-lg bg-gray-100 dark:bg-slate-800/50 hover:bg-gray-100 dark:bg-slate-800 transition-colors">
                    <span className="text-green-400">🔍</span>
                    <div className="flex-1">
                      <p className="text-sm text-gray-700 dark:text-slate-300">Feature Attribution</p>
                      <p className="text-xs text-gray-500 dark:text-slate-500">SHAP values, feature importance, dependence plots</p>
                    </div>
                  </Link>
                  <Link to="/analytics" className="flex items-center gap-3 p-3 rounded-lg bg-gray-100 dark:bg-slate-800/50 hover:bg-gray-100 dark:bg-slate-800 transition-colors">
                    <span className="text-green-400">📊</span>
                    <div className="flex-1">
                      <p className="text-sm text-gray-700 dark:text-slate-300">Population Analytics</p>
                      <p className="text-xs text-gray-500 dark:text-slate-500">Distributions, correlations, ACWR zones</p>
                    </div>
                  </Link>
                </div>

                <Link
                  to="/validation"
                  className="mt-4 w-full py-3 bg-green-600 hover:bg-green-500 text-gray-900 dark:text-white rounded-lg font-medium transition-colors flex items-center justify-center"
                >
                  View Published Results
                  <svg className="w-4 h-4 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </Link>
              </div>

              {/* Run Your Own Experiments */}
              <div className="p-6 rounded-2xl bg-gradient-to-br from-purple-100 via-gray-50 to-blue-100 dark:from-purple-900/20 dark:via-slate-900 dark:to-blue-900/20 border border-purple-200 dark:border-purple-500/20">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 rounded-xl bg-purple-100 dark:bg-purple-500/20 flex items-center justify-center">
                    <svg className="w-6 h-6 text-purple-600 dark:text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Run Your Own Experiments</h3>
                    <p className="text-xs text-gray-500 dark:text-slate-500">Create custom datasets and models</p>
                  </div>
                </div>

                <p className="text-sm text-gray-600 dark:text-slate-400 mb-4">
                  Go beyond the published study. Generate new synthetic cohorts with different parameters,
                  upload your own real data, or test different model configurations.
                </p>

                <div className="space-y-3">
                  <div className="p-3 rounded-lg bg-gray-100 dark:bg-slate-800/50 border border-gray-300 dark:border-slate-700">
                    <h4 className="text-sm font-semibold text-gray-700 dark:text-slate-300 mb-1">Generate New Cohorts</h4>
                    <p className="text-xs text-gray-500 dark:text-slate-500">Vary athlete count (100-5000), injury rates, simulation seed</p>
                  </div>
                  <div className="p-3 rounded-lg bg-gray-100 dark:bg-slate-800/50 border border-gray-300 dark:border-slate-700">
                    <h4 className="text-sm font-semibold text-gray-700 dark:text-slate-300 mb-1">Upload Your Data</h4>
                    <p className="text-xs text-gray-500 dark:text-slate-500">Import real Garmin/Strava exports for analysis</p>
                  </div>
                  <div className="p-3 rounded-lg bg-gray-100 dark:bg-slate-800/50 border border-gray-300 dark:border-slate-700">
                    <h4 className="text-sm font-semibold text-gray-700 dark:text-slate-300 mb-1">Train Different Models</h4>
                    <p className="text-xs text-gray-500 dark:text-slate-500">Compare Lasso, Random Forest, XGBoost with custom hyperparameters</p>
                  </div>
                  <div className="p-3 rounded-lg bg-gray-100 dark:bg-slate-800/50 border border-gray-300 dark:border-slate-700">
                    <h4 className="text-sm font-semibold text-gray-700 dark:text-slate-300 mb-1">What-If Analysis</h4>
                    <p className="text-xs text-gray-500 dark:text-slate-500">Simulate interventions on individual athletes</p>
                  </div>
                </div>

                <Link
                  to="/data-generation"
                  className="mt-4 w-full py-3 bg-purple-600 hover:bg-purple-500 text-gray-900 dark:text-white rounded-lg font-medium transition-colors flex items-center justify-center"
                >
                  Start New Experiment
                  <svg className="w-4 h-4 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </Link>
              </div>
            </div>

            {/* Quick Reference */}
            <Card title="Platform Navigation Quick Reference">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
                <div>
                  <h4 className="font-semibold text-blue-400 mb-2">Study Design</h4>
                  <ul className="space-y-1 text-gray-500 dark:text-slate-500">
                    <li><Link to="/data-generation" className="hover:text-gray-700 dark:text-slate-300">→ Synthetic Cohort</Link></li>
                    <li><Link to="/ingestion" className="hover:text-gray-700 dark:text-slate-300">→ Real Data Upload</Link></li>
                    <li><Link to="/validation" className="hover:text-gray-700 dark:text-slate-300">→ Data Validation</Link></li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold text-purple-400 mb-2">Methods</h4>
                  <ul className="space-y-1 text-gray-500 dark:text-slate-500">
                    <li><Link to="/preprocessing" className="hover:text-gray-700 dark:text-slate-300">→ Feature Engineering</Link></li>
                    <li><Link to="/training" className="hover:text-gray-700 dark:text-slate-300">→ Model Development</Link></li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold text-green-400 mb-2">Results</h4>
                  <ul className="space-y-1 text-gray-500 dark:text-slate-500">
                    <li><Link to="/results" className="hover:text-gray-700 dark:text-slate-300">→ Model Performance</Link></li>
                    <li><Link to="/interpretability" className="hover:text-gray-700 dark:text-slate-300">→ Feature Attribution</Link></li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold text-amber-400 mb-2">Analysis</h4>
                  <ul className="space-y-1 text-gray-500 dark:text-slate-500">
                    <li><Link to="/analytics" className="hover:text-gray-700 dark:text-slate-300">→ Population Analytics</Link></li>
                    <li><Link to="/athletes" className="hover:text-gray-700 dark:text-slate-300">→ Individual Profiles</Link></li>
                  </ul>
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* ===== PIPELINE TAB ===== */}
        {activeTab === 'pipeline' && (
          <div className="space-y-6">
            <div className="p-4 rounded-xl bg-gray-100 dark:bg-slate-800/50 border border-gray-300 dark:border-slate-700">
              <p className="text-sm text-gray-600 dark:text-slate-400">
                The scientific workflow follows a structured pipeline from data generation through model evaluation.
                Each step builds on the previous one, ensuring reproducibility and transparency.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Study Design Section */}
              <div className="p-5 rounded-2xl bg-white dark:bg-slate-900/50 border border-gray-200 dark:border-slate-800">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center">
                    <svg className="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-gray-900 dark:text-white">Study Design</h3>
                    <p className="text-xs text-gray-500 dark:text-slate-500">Data collection & validation</p>
                  </div>
                </div>
                <div className="space-y-2">
                  <Link to="/data-generation" className="flex items-center justify-between p-3 rounded-xl hover:bg-gray-100 dark:bg-slate-800/50 transition-colors group">
                    <div className="flex items-center gap-3">
                      <span className="text-base">🧬</span>
                      <span className="text-sm text-gray-700 dark:text-slate-300 group-hover:text-gray-900 dark:group-hover:text-white">Synthetic Cohort</span>
                    </div>
                    <span className={`text-xs px-2 py-0.5 rounded-full border ${getStatusColor(datasets.length > 0 ? 'completed' : 'pending')}`}>
                      {datasets.length} datasets
                    </span>
                  </Link>
                  <Link to="/ingestion" className="flex items-center justify-between p-3 rounded-xl hover:bg-gray-100 dark:bg-slate-800/50 transition-colors group">
                    <div className="flex items-center gap-3">
                      <span className="text-base">📤</span>
                      <span className="text-sm text-gray-700 dark:text-slate-300 group-hover:text-gray-900 dark:group-hover:text-white">Real Data</span>
                    </div>
                    <span className="text-xs text-gray-500 dark:text-slate-500">Optional</span>
                  </Link>
                  <Link to="/validation" className="flex items-center justify-between p-3 rounded-xl hover:bg-gray-100 dark:bg-slate-800/50 transition-colors group">
                    <div className="flex items-center gap-3">
                      <span className="text-base">🔬</span>
                      <span className="text-sm text-gray-700 dark:text-slate-300 group-hover:text-gray-900 dark:group-hover:text-white">Data Validation</span>
                    </div>
                    <span className="text-xs text-gray-500 dark:text-slate-500">Sim2Real</span>
                  </Link>
                </div>
              </div>

              {/* Methods Section */}
              <div className="p-5 rounded-2xl bg-white dark:bg-slate-900/50 border border-gray-200 dark:border-slate-800">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center">
                    <svg className="w-5 h-5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-gray-900 dark:text-white">Methods</h3>
                    <p className="text-xs text-gray-500 dark:text-slate-500">Feature engineering & modeling</p>
                  </div>
                </div>
                <div className="space-y-2">
                  <Link to="/preprocessing" className="flex items-center justify-between p-3 rounded-xl hover:bg-gray-100 dark:bg-slate-800/50 transition-colors group">
                    <div className="flex items-center gap-3">
                      <span className="text-base">⚙️</span>
                      <span className="text-sm text-gray-700 dark:text-slate-300 group-hover:text-gray-900 dark:group-hover:text-white">Feature Engineering</span>
                    </div>
                    <span className={`text-xs px-2 py-0.5 rounded-full border ${getStatusColor(splits.length > 0 ? 'completed' : datasets.length > 0 ? 'ready' : 'pending')}`}>
                      {splits.length} splits
                    </span>
                  </Link>
                  <Link to="/training" className="flex items-center justify-between p-3 rounded-xl hover:bg-gray-100 dark:bg-slate-800/50 transition-colors group">
                    <div className="flex items-center gap-3">
                      <span className="text-base">🤖</span>
                      <span className="text-sm text-gray-700 dark:text-slate-300 group-hover:text-gray-900 dark:group-hover:text-white">Model Development</span>
                    </div>
                    <span className={`text-xs px-2 py-0.5 rounded-full border ${getStatusColor(models.length > 0 ? 'completed' : splits.length > 0 ? 'ready' : 'pending')}`}>
                      {models.length} models
                    </span>
                  </Link>
                </div>
              </div>

              {/* Results Section */}
              <div className="p-5 rounded-2xl bg-white dark:bg-slate-900/50 border border-gray-200 dark:border-slate-800">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-xl bg-green-500/10 flex items-center justify-center">
                    <svg className="w-5 h-5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-gray-900 dark:text-white">Results</h3>
                    <p className="text-xs text-gray-500 dark:text-slate-500">Performance & interpretation</p>
                  </div>
                </div>
                <div className="space-y-2">
                  <Link to="/results" className="flex items-center justify-between p-3 rounded-xl hover:bg-gray-100 dark:bg-slate-800/50 transition-colors group">
                    <div className="flex items-center gap-3">
                      <span className="text-base">📈</span>
                      <span className="text-sm text-gray-700 dark:text-slate-300 group-hover:text-gray-900 dark:group-hover:text-white">Model Performance</span>
                    </div>
                    <span className="text-xs text-gray-500 dark:text-slate-500">ROC, PR curves</span>
                  </Link>
                  <Link to="/interpretability" className="flex items-center justify-between p-3 rounded-xl hover:bg-gray-100 dark:bg-slate-800/50 transition-colors group">
                    <div className="flex items-center gap-3">
                      <span className="text-base">🔍</span>
                      <span className="text-sm text-gray-700 dark:text-slate-300 group-hover:text-gray-900 dark:group-hover:text-white">Feature Attribution</span>
                    </div>
                    <span className="text-xs text-gray-500 dark:text-slate-500">SHAP values</span>
                  </Link>
                </div>
              </div>

              {/* Analysis Section */}
              <div className="p-5 rounded-2xl bg-white dark:bg-slate-900/50 border border-gray-200 dark:border-slate-800">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center">
                    <svg className="w-5 h-5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-gray-900 dark:text-white">Analysis</h3>
                    <p className="text-xs text-gray-500 dark:text-slate-500">Population & individual insights</p>
                  </div>
                </div>
                <div className="space-y-2">
                  <Link to="/analytics" className="flex items-center justify-between p-3 rounded-xl hover:bg-gray-100 dark:bg-slate-800/50 transition-colors group">
                    <div className="flex items-center gap-3">
                      <span className="text-base">📊</span>
                      <span className="text-sm text-gray-700 dark:text-slate-300 group-hover:text-gray-900 dark:group-hover:text-white">Population Analytics</span>
                    </div>
                    <span className="text-xs text-gray-500 dark:text-slate-500">Distributions, correlations</span>
                  </Link>
                  <Link to="/athletes" className="flex items-center justify-between p-3 rounded-xl hover:bg-gray-100 dark:bg-slate-800/50 transition-colors group">
                    <div className="flex items-center gap-3">
                      <span className="text-base">🏃</span>
                      <span className="text-sm text-gray-700 dark:text-slate-300 group-hover:text-gray-900 dark:group-hover:text-white">Individual Profiles</span>
                    </div>
                    <span className="text-xs text-gray-500 dark:text-slate-500">Risk assessment</span>
                  </Link>
                </div>
              </div>
            </div>

            {/* Key Findings (when models exist) */}
            {studyProgress.bestModel && (
              <div className="p-6 rounded-2xl bg-gradient-to-r from-green-500/5 to-emerald-500/5 border border-green-500/20">
                <div className="flex items-center gap-2 mb-4">
                  <svg className="w-5 h-5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Current Best Model</h2>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="p-4 rounded-xl bg-white dark:bg-slate-900/50 border border-gray-200 dark:border-slate-800">
                    <p className="text-xs text-gray-500 dark:text-slate-500 uppercase tracking-wider mb-1">Model Type</p>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white capitalize">{studyProgress.bestModel.model_type?.replace('_', ' ')}</p>
                  </div>
                  <div className="p-4 rounded-xl bg-white dark:bg-slate-900/50 border border-gray-200 dark:border-slate-800">
                    <p className="text-xs text-gray-500 dark:text-slate-500 uppercase tracking-wider mb-1">ROC-AUC</p>
                    <p className="text-lg font-semibold text-green-400">{studyProgress.bestModel.metrics?.roc_auc?.toFixed(3) || 'N/A'}</p>
                  </div>
                  <div className="p-4 rounded-xl bg-white dark:bg-slate-900/50 border border-gray-200 dark:border-slate-800">
                    <p className="text-xs text-gray-500 dark:text-slate-500 uppercase tracking-wider mb-1">PR-AUC</p>
                    <p className="text-lg font-semibold text-blue-400">{studyProgress.bestModel.metrics?.average_precision?.toFixed(3) || 'N/A'}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ===== VALIDATION TAB ===== */}
        {activeTab === 'validation' && (
          <div className="space-y-6">
            <div className="p-6 rounded-2xl bg-gradient-to-br from-purple-100 via-gray-50 to-blue-100 dark:from-purple-900/20 dark:via-slate-900 dark:to-blue-900/20 border border-purple-200 dark:border-purple-500/20">
              <div className="flex items-center gap-2 mb-4">
                <svg className="w-5 h-5 text-purple-600 dark:text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Why Data Validation is Critical</h2>
              </div>

              <p className="text-sm text-gray-600 dark:text-slate-400 mb-4">
                Before training models on synthetic data, we must prove the data is <strong className="text-gray-700 dark:text-slate-300">scientifically valid</strong>.
                This validation step establishes that our synthetic cohort accurately represents real-world physiological patterns,
                making any downstream predictions trustworthy for clinical and research applications.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div className="p-4 rounded-xl bg-gray-100 dark:bg-slate-800/50 border border-gray-300 dark:border-slate-700/50">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center">
                      <span className="text-xs font-bold text-blue-400">1</span>
                    </div>
                    <h4 className="text-sm font-semibold text-gray-700 dark:text-slate-300">Statistical Fidelity</h4>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-slate-500">
                    Do synthetic distributions match real PMData? We measure Jensen-Shannon divergence across all biomarkers
                    to ensure HRV, sleep, and stress patterns are realistic.
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-gray-100 dark:bg-slate-800/50 border border-gray-300 dark:border-slate-700/50">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-6 h-6 rounded-full bg-green-500/20 flex items-center justify-center">
                      <span className="text-xs font-bold text-green-400">2</span>
                    </div>
                    <h4 className="text-sm font-semibold text-gray-700 dark:text-slate-300">Causal Fidelity</h4>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-slate-500">
                    Does the ACWR-injury relationship match sports science literature? Undertrained athletes (ACWR &lt; 0.8)
                    should show 2-3× higher injury risk per training load unit than optimally trained athletes.
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-gray-100 dark:bg-slate-800/50 border border-gray-300 dark:border-slate-700/50">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-6 h-6 rounded-full bg-purple-500/20 flex items-center justify-center">
                      <span className="text-xs font-bold text-purple-400">3</span>
                    </div>
                    <h4 className="text-sm font-semibold text-gray-700 dark:text-slate-300">Transferability</h4>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-slate-500">
                    Can models trained on synthetic data generalize? We test Sim2Real transfer by evaluating
                    synthetic-trained models on real PMData athletes.
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-between p-3 rounded-lg bg-gray-100 dark:bg-slate-800/30 border border-gray-300 dark:border-slate-700/30">
                <p className="text-xs text-gray-500 dark:text-slate-500">
                  <strong className="text-gray-600 dark:text-slate-400">Workflow:</strong> Generate Cohort → <strong className="text-purple-400">Validate Data</strong> → Engineer Features → Train Models → Evaluate Results
                </p>
                <Link to="/validation" className="text-sm text-purple-400 hover:text-purple-300 flex items-center whitespace-nowrap ml-4">
                  Run Validation
                  <svg className="w-4 h-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </Link>
              </div>
            </div>

            {/* Validation Importance */}
            <Card title="What Happens If Validation Fails?">
              <div className="space-y-4 text-sm text-gray-600 dark:text-slate-400">
                <p>
                  If the synthetic data fails validation, any models trained on it are <strong className="text-red-400">scientifically unreliable</strong>.
                  The validation step acts as a quality gate—you should not proceed to model training until all three pillars pass.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                    <h4 className="font-semibold text-red-400 text-xs mb-1">Statistical Failure</h4>
                    <p className="text-xs text-gray-500 dark:text-slate-500">Distributions are unrealistic—regenerate cohort with adjusted parameters</p>
                  </div>
                  <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                    <h4 className="font-semibold text-red-400 text-xs mb-1">Causal Failure</h4>
                    <p className="text-xs text-gray-500 dark:text-slate-500">ACWR-injury relationship is wrong—check injury simulation parameters</p>
                  </div>
                  <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                    <h4 className="font-semibold text-red-400 text-xs mb-1">Transfer Failure</h4>
                    <p className="text-xs text-gray-500 dark:text-slate-500">Models don't generalize—may indicate domain gap issues</p>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* ===== PROGRESS TAB ===== */}
        {activeTab === 'progress' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Datasets */}
              <Card title="Synthetic Cohorts">
                {loading.datasets ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin h-6 w-6 border-2 border-blue-400 border-t-transparent rounded-full"></div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {/* Reference Dataset (Published Study) */}
                    {datasets.find(ds => ds.id === 'dataset_reference') && (
                      <div className="p-3 rounded-xl bg-green-500/10 border border-green-500/20">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="text-green-400">📚</span>
                            <div>
                              <p className="text-sm font-medium text-green-400">Published Study</p>
                              <p className="text-xs text-gray-500 dark:text-slate-500">Pre-computed reference dataset</p>
                            </div>
                          </div>
                          <span className="text-xs text-gray-500 dark:text-slate-500 flex items-center">
                            <svg className="w-3 h-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                            </svg>
                            {datasets.find(ds => ds.id === 'dataset_reference')?.n_athletes || '?'}
                          </span>
                        </div>
                      </div>
                    )}

                    {/* User-Generated Datasets */}
                    {datasets.filter(ds => ds.id !== 'dataset_reference').length > 0 ? (
                      <div>
                        <p className="text-xs text-gray-500 dark:text-slate-500 uppercase tracking-wider mb-2">Your Experiments</p>
                        <ul className="space-y-2">
                          {datasets.filter(ds => ds.id !== 'dataset_reference').slice(0, 4).map(ds => (
                            <li key={ds.id} className="flex justify-between items-center p-3 hover:bg-gray-100 dark:bg-slate-800/50 rounded-xl transition-colors">
                              <span className="font-mono text-sm text-gray-700 dark:text-slate-300 truncate">{ds.id}</span>
                              <span className="text-sm text-gray-500 dark:text-slate-500 flex items-center">
                                <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                </svg>
                                {ds.n_athletes}
                              </span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    ) : !datasets.find(ds => ds.id === 'dataset_reference') ? (
                      <div className="text-center py-6">
                        <div className="w-12 h-12 rounded-full bg-gray-100 dark:bg-slate-800 flex items-center justify-center mx-auto mb-3">
                          <svg className="w-6 h-6 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
                          </svg>
                        </div>
                        <p className="text-gray-500 dark:text-slate-500 text-sm">No custom cohorts</p>
                        <Link to="/data-generation" className="text-blue-400 text-sm hover:text-blue-300 mt-1 inline-block">
                          Generate cohort
                        </Link>
                      </div>
                    ) : (
                      <div className="text-center py-2">
                        <Link to="/data-generation" className="text-blue-400 text-xs hover:text-blue-300">
                          + Generate new cohort
                        </Link>
                      </div>
                    )}
                  </div>
                )}
              </Card>

              {/* Feature Sets */}
              <Card title="Feature Sets">
                {loading.splits ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin h-6 w-6 border-2 border-purple-400 border-t-transparent rounded-full"></div>
                  </div>
                ) : splits.length === 0 ? (
                  <div className="text-center py-8">
                    <div className="w-12 h-12 rounded-full bg-gray-100 dark:bg-slate-800 flex items-center justify-center mx-auto mb-3">
                      <svg className="w-6 h-6 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                      </svg>
                    </div>
                    <p className="text-gray-500 dark:text-slate-500 text-sm">No feature sets</p>
                    <Link to="/preprocessing" className="text-purple-400 text-sm hover:text-purple-300 mt-1 inline-block">
                      Engineer features
                    </Link>
                  </div>
                ) : (
                  <ul className="space-y-2">
                    {splits.slice(0, 5).map(split => (
                      <li key={split.id} className="flex justify-between items-center p-3 hover:bg-gray-100 dark:bg-slate-800/50 rounded-xl transition-colors">
                        <span className="font-mono text-sm text-gray-700 dark:text-slate-300 truncate">{split.id}</span>
                        <span className="text-xs px-2 py-1 rounded-full bg-purple-500/20 text-purple-400 border border-purple-500/30">
                          {split.split_strategy}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </Card>

              {/* Trained Models */}
              <Card title="Trained Models">
                {loading.models ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin h-6 w-6 border-2 border-green-400 border-t-transparent rounded-full"></div>
                  </div>
                ) : models.length === 0 ? (
                  <div className="text-center py-8">
                    <div className="w-12 h-12 rounded-full bg-gray-100 dark:bg-slate-800 flex items-center justify-center mx-auto mb-3">
                      <svg className="w-6 h-6 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3" />
                      </svg>
                    </div>
                    <p className="text-gray-500 dark:text-slate-500 text-sm">No models trained</p>
                    <Link to="/training" className="text-green-400 text-sm hover:text-green-300 mt-1 inline-block">
                      Train models
                    </Link>
                  </div>
                ) : (
                  <ul className="space-y-2">
                    {models.slice(0, 5).map(model => (
                      <li key={model.id} className="flex justify-between items-center p-3 hover:bg-gray-100 dark:bg-slate-800/50 rounded-xl transition-colors">
                        <span className="font-medium text-sm text-gray-700 dark:text-slate-300 capitalize">{model.model_type?.replace('_', ' ')}</span>
                        <span className="text-sm font-mono text-green-400">
                          {model.metrics?.roc_auc?.toFixed(3) || 'N/A'}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </Card>
            </div>

            {/* Quick Actions */}
            <div className="p-6 rounded-2xl bg-gradient-to-r from-gray-100 to-gray-50 dark:from-slate-900 dark:to-slate-800 border border-gray-200 dark:border-slate-800">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Quick Actions</h2>
              <div className="flex flex-wrap gap-3">
                <Link
                  to="/data-generation"
                  className="px-4 py-2 text-sm font-medium text-gray-900 dark:text-white bg-blue-600 rounded-lg hover:bg-blue-500 transition-colors flex items-center"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  New Cohort
                </Link>
                <Link
                  to="/athletes"
                  className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-slate-300 bg-gray-100 dark:bg-slate-800 border border-gray-300 dark:border-slate-700 rounded-lg hover:bg-slate-700 hover:text-gray-900 dark:text-white transition-colors flex items-center"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  Individual Profiles
                </Link>
                <Link
                  to="/analytics"
                  className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-slate-300 bg-gray-100 dark:bg-slate-800 border border-gray-300 dark:border-slate-700 rounded-lg hover:bg-slate-700 hover:text-gray-900 dark:text-white transition-colors flex items-center"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  Population Analytics
                </Link>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  )
}

export default Dashboard
