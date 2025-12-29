import { useTheme } from '../../context/ThemeContext'

function ProgressBar({ progress, status, label, showPercentage = true }) {
  const { isDark } = useTheme()

  const getStatusColor = () => {
    switch (status) {
      case 'completed':
        return 'bg-gradient-to-r from-green-500 to-emerald-500'
      case 'failed':
        return 'bg-gradient-to-r from-red-500 to-red-600'
      case 'cancelled':
        return 'bg-gradient-to-r from-yellow-500 to-amber-500'
      case 'starting':
        return 'bg-gradient-to-r from-purple-500 to-purple-600'
      default:
        return 'bg-gradient-to-r from-blue-500 to-purple-500'
    }
  }

  const isIndeterminate = status === 'starting'

  return (
    <div className="w-full">
      {label && (
        <div className="flex justify-between mb-2">
          <span className={`text-sm font-medium ${isDark ? 'text-slate-300' : 'text-gray-700'}`}>{label}</span>
          {showPercentage && !isIndeterminate && (
            <span className={`text-sm font-medium ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>{Math.round(progress)}%</span>
          )}
          {isIndeterminate && (
            <span className={`text-sm font-medium ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>Initializing...</span>
          )}
        </div>
      )}
      <div className={`w-full ${isDark ? 'bg-slate-800' : 'bg-gray-200'} rounded-full h-2.5 overflow-hidden`}>
        {isIndeterminate ? (
          <div className="h-2.5 rounded-full bg-gradient-to-r from-purple-500 to-purple-600 animate-pulse w-full opacity-60"></div>
        ) : (
          <div
            className={`h-2.5 rounded-full transition-all duration-300 ${getStatusColor()}`}
            style={{ width: `${Math.min(progress, 100)}%` }}
          ></div>
        )}
      </div>
    </div>
  )
}

export default ProgressBar
