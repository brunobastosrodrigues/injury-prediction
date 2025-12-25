function StatusBadge({ status }) {
  const getStatusStyles = () => {
    switch (status) {
      case 'completed':
        return 'bg-green-500/20 text-green-400 border-green-500/30'
      case 'running':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30'
      case 'pending':
        return 'bg-slate-700/50 text-slate-400 border-slate-600/30'
      case 'failed':
        return 'bg-red-500/20 text-red-400 border-red-500/30'
      case 'cancelled':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
      default:
        return 'bg-slate-700/50 text-slate-400 border-slate-600/30'
    }
  }

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusStyles()}`}>
      {status === 'running' && (
        <span className="mr-1.5 h-2 w-2 bg-blue-400 rounded-full animate-pulse"></span>
      )}
      {status}
    </span>
  )
}

export default StatusBadge
