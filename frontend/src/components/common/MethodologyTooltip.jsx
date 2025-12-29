import { useState } from 'react'
import { useTheme } from '../../context/ThemeContext'

/**
 * MethodologyTooltip - Academic documentation tooltip
 * Provides detailed methodology explanations on hover/click
 */
function MethodologyTooltip({
  term,
  definition,
  formula = null,
  reference = null,
  children,
  className = ''
}) {
  const [isOpen, setIsOpen] = useState(false)
  const { isDark } = useTheme()

  return (
    <span className={`relative inline-flex items-center ${className}`}>
      <span
        className={`cursor-help border-b border-dotted ${isDark ? 'border-slate-500 hover:border-blue-400' : 'border-gray-400 hover:border-blue-500'} transition-colors`}
        onMouseEnter={() => setIsOpen(true)}
        onMouseLeave={() => setIsOpen(false)}
        onClick={() => setIsOpen(!isOpen)}
      >
        {children || term}
      </span>

      {isOpen && (
        <div className={`absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 p-3 ${isDark ? 'bg-slate-800 border-slate-700' : 'bg-white border-gray-200 shadow-lg'} border rounded-lg shadow-xl text-left`}>
          <div className={`text-sm font-semibold ${isDark ? 'text-white' : 'text-gray-900'} mb-1`}>{term}</div>
          <div className={`text-xs ${isDark ? 'text-slate-300' : 'text-gray-600'} leading-relaxed`}>{definition}</div>

          {formula && (
            <div className={`mt-2 p-2 ${isDark ? 'bg-slate-900 text-blue-300' : 'bg-blue-50 text-blue-700'} rounded font-mono text-xs overflow-x-auto`}>
              {formula}
            </div>
          )}

          {reference && (
            <div className={`mt-2 pt-2 border-t ${isDark ? 'border-slate-700 text-slate-500' : 'border-gray-200 text-gray-500'} text-xs`}>
              <span className="italic">{reference}</span>
            </div>
          )}

          <div className={`absolute left-1/2 -translate-x-1/2 -bottom-1.5 w-3 h-3 ${isDark ? 'bg-slate-800 border-slate-700' : 'bg-white border-gray-200'} border-r border-b transform rotate-45`} />
        </div>
      )}
    </span>
  )
}

// Pre-defined methodology terms for consistency
export const METHODOLOGY_TERMS = {
  ACWR: {
    term: 'ACWR',
    definition: 'Acute:Chronic Workload Ratio. Compares recent training load (7-day) to chronic load (28-day rolling average). Values > 1.5 indicate elevated injury risk.',
    formula: 'ACWR = Acute Load (7d) / Chronic Load (28d)',
    reference: 'Gabbett, T.J. (2016). The training—injury prevention paradox. BJSM.'
  },
  CTL: {
    term: 'CTL',
    definition: 'Chronic Training Load. Exponentially weighted moving average of daily training stress, representing accumulated fitness. Uses 42-day time constant.',
    formula: 'CTL_n = CTL_{n-1} + (TSS_n - CTL_{n-1}) / τ',
    reference: 'Coggan, A. (2003). Training with Power.'
  },
  ATL: {
    term: 'ATL',
    definition: 'Acute Training Load. Short-term fatigue proxy using 7-day exponentially weighted moving average of training stress.',
    formula: 'ATL_n = ATL_{n-1} + (TSS_n - ATL_{n-1}) / τ',
    reference: 'Coggan, A. (2003). Training with Power.'
  },
  TSB: {
    term: 'TSB',
    definition: 'Training Stress Balance. Difference between fitness (CTL) and fatigue (ATL). Positive values indicate freshness; negative values indicate fatigue.',
    formula: 'TSB = CTL - ATL',
    reference: 'Coggan, A. (2003). Training with Power.'
  },
  ROC_AUC: {
    term: 'ROC-AUC',
    definition: 'Area Under the Receiver Operating Characteristic Curve. Measures discrimination ability: probability that a randomly chosen positive has higher predicted risk than a randomly chosen negative.',
    formula: 'AUC = ∫₀¹ TPR(FPR) dFPR',
    reference: 'Hanley & McNeil (1982). Radiology.'
  },
  PR_AUC: {
    term: 'PR-AUC',
    definition: 'Area Under the Precision-Recall Curve. Preferred metric for imbalanced datasets. Measures trade-off between precision and recall across thresholds.',
    formula: 'AP = Σ(R_n - R_{n-1}) × P_n',
    reference: 'Davis & Goadrich (2006). ICML.'
  },
  SHAP: {
    term: 'SHAP',
    definition: 'SHapley Additive exPlanations. Game-theoretic approach to explain model predictions by computing each feature\'s contribution to the prediction.',
    formula: 'φᵢ = Σ |S|!(p-|S|-1)!/p! [f(S∪{i}) - f(S)]',
    reference: 'Lundberg & Lee (2017). NeurIPS.'
  },
  HRV: {
    term: 'HRV',
    definition: 'Heart Rate Variability. Variation in time between heartbeats, reflecting autonomic nervous system activity. Higher HRV typically indicates better recovery status.',
    reference: 'Buchheit, M. (2014). Sports Medicine.'
  }
}

export default MethodologyTooltip
