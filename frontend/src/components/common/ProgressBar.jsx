function ProgressBar({ progress, status, label, showPercentage = true }) {
  const getStatusColor = () => {
    switch (status) {
      case 'completed':
        return 'bg-gradient-to-r from-green-500 to-emerald-500'
      case 'failed':
        return 'bg-gradient-to-r from-red-500 to-red-600'
      case 'cancelled':
        return 'bg-gradient-to-r from-yellow-500 to-amber-500'
      default:
        return 'bg-gradient-to-r from-blue-500 to-purple-500'
    }
  }

  return (
    <div className="w-full">
      {label && (
        <div className="flex justify-between mb-2">
          <span className="text-sm font-medium text-slate-300">{label}</span>
          {showPercentage && (
            <span className="text-sm font-medium text-slate-400">{Math.round(progress)}%</span>
          )}
        </div>
      )}
      <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
        <div
          className={`h-2.5 rounded-full transition-all duration-300 ${getStatusColor()}`}
          style={{ width: `${Math.min(progress, 100)}%` }}
        ></div>
      </div>
    </div>
  )
}

export default ProgressBar
