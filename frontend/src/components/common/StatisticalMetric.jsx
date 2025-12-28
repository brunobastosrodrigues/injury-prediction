import MethodologyTooltip, { METHODOLOGY_TERMS } from './MethodologyTooltip'

/**
 * StatisticalMetric - Academic-style metric display
 * Shows metrics with confidence intervals and statistical context
 */
function StatisticalMetric({
  label,
  value,
  ci = null,           // Confidence interval [lower, upper]
  std = null,          // Standard deviation
  n = null,            // Sample size
  pValue = null,
  significanceLevel = 0.05,
  format = 'decimal',  // 'decimal', 'percent', 'integer'
  precision = 4,
  methodology = null,  // Key from METHODOLOGY_TERMS
  color = 'blue',      // 'blue', 'green', 'purple', 'orange', 'red'
  size = 'default',    // 'small', 'default', 'large'
  className = ''
}) {
  const colorClasses = {
    blue: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
    green: 'text-green-400 bg-green-500/10 border-green-500/20',
    purple: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
    orange: 'text-orange-400 bg-orange-500/10 border-orange-500/20',
    red: 'text-red-400 bg-red-500/10 border-red-500/20'
  }

  const sizeClasses = {
    small: { value: 'text-lg', label: 'text-xs' },
    default: { value: 'text-2xl', label: 'text-sm' },
    large: { value: 'text-3xl', label: 'text-base' }
  }

  const formatValue = (val) => {
    if (val === null || val === undefined) return 'N/A'
    switch (format) {
      case 'percent':
        return `${(val * 100).toFixed(precision - 2)}%`
      case 'integer':
        return Math.round(val).toLocaleString()
      default:
        return val.toFixed(precision)
    }
  }

  const formatCI = () => {
    if (!ci || ci.length !== 2) return null
    return `[${formatValue(ci[0])}, ${formatValue(ci[1])}]`
  }

  const isSignificant = pValue !== null && pValue < significanceLevel

  const methodologyData = methodology ? METHODOLOGY_TERMS[methodology] : null

  return (
    <div className={`p-3 sm:p-4 rounded-xl border ${colorClasses[color]} ${className}`}>
      <div className="flex items-baseline justify-between mb-1">
        <span className={`font-bold ${sizeClasses[size].value} ${colorClasses[color].split(' ')[0]}`}>
          {formatValue(value)}
        </span>

        {pValue !== null && (
          <span className={`text-xs font-mono ${isSignificant ? 'text-green-400' : 'text-slate-500'}`}>
            p={pValue < 0.001 ? '<.001' : pValue.toFixed(3)}
            {isSignificant && ' *'}
          </span>
        )}
      </div>

      <div className={`${sizeClasses[size].label} text-slate-400 flex items-center gap-1`}>
        {methodologyData ? (
          <MethodologyTooltip {...methodologyData}>
            {label}
          </MethodologyTooltip>
        ) : (
          label
        )}
      </div>

      {/* Confidence Interval */}
      {ci && (
        <div className="mt-1 text-xs text-slate-500 font-mono">
          95% CI: {formatCI()}
        </div>
      )}

      {/* Standard Deviation */}
      {std !== null && (
        <div className="mt-1 text-xs text-slate-500">
          SD: ±{formatValue(std)}
        </div>
      )}

      {/* Sample Size */}
      {n !== null && (
        <div className="mt-1 text-xs text-slate-600">
          n = {n.toLocaleString()}
        </div>
      )}
    </div>
  )
}

export default StatisticalMetric
