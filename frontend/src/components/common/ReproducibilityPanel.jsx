import { useState } from 'react'
import { useTheme } from '../../context/ThemeContext'

/**
 * ReproducibilityPanel - Research reproducibility information
 * Displays and exports configuration for replication studies
 */
function ReproducibilityPanel({
  config = {},
  datasetId = null,
  modelId = null,
  splitId = null,
  className = ''
}) {
  const [copied, setCopied] = useState(false)
  const [expanded, setExpanded] = useState(false)
  const { isDark } = useTheme()

  const reproducibilityInfo = {
    timestamp: new Date().toISOString(),
    dataset_id: datasetId,
    model_id: modelId,
    split_id: splitId,
    configuration: config,
    environment: {
      platform: 'Injury Risk Prediction Platform',
      version: '1.0.0',
      framework: 'Flask + React + Celery'
    }
  }

  const copyConfig = () => {
    navigator.clipboard.writeText(JSON.stringify(reproducibilityInfo, null, 2))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const downloadConfig = () => {
    const blob = new Blob([JSON.stringify(reproducibilityInfo, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `reproducibility_${datasetId || 'config'}_${Date.now()}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  return (
    <div className={`${isDark ? 'bg-slate-900/50 border-slate-800' : 'bg-gray-50 border-gray-200'} border rounded-xl overflow-hidden ${className}`}>
      <button
        onClick={() => setExpanded(!expanded)}
        className={`w-full px-4 py-3 flex items-center justify-between text-left ${isDark ? 'hover:bg-slate-800/50' : 'hover:bg-gray-100'} transition-colors`}
      >
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          <span className={`text-sm font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Reproducibility Information</span>
        </div>
        <svg className={`w-4 h-4 ${isDark ? 'text-slate-400' : 'text-gray-500'} transition-transform ${expanded ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {expanded && (
        <div className={`px-4 pb-4 border-t ${isDark ? 'border-slate-800' : 'border-gray-200'}`}>
          <div className="mt-3 space-y-3">
            {/* Key identifiers */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {datasetId && (
                <div className={`p-2 ${isDark ? 'bg-slate-800/50' : 'bg-white border border-gray-200'} rounded`}>
                  <div className={`text-xs ${isDark ? 'text-slate-500' : 'text-gray-500'}`}>Dataset ID</div>
                  <div className={`text-sm ${isDark ? 'text-slate-300' : 'text-gray-700'} font-mono truncate`}>{datasetId}</div>
                </div>
              )}
              {splitId && (
                <div className={`p-2 ${isDark ? 'bg-slate-800/50' : 'bg-white border border-gray-200'} rounded`}>
                  <div className={`text-xs ${isDark ? 'text-slate-500' : 'text-gray-500'}`}>Split ID</div>
                  <div className={`text-sm ${isDark ? 'text-slate-300' : 'text-gray-700'} font-mono truncate`}>{splitId}</div>
                </div>
              )}
              {modelId && (
                <div className={`p-2 ${isDark ? 'bg-slate-800/50' : 'bg-white border border-gray-200'} rounded`}>
                  <div className={`text-xs ${isDark ? 'text-slate-500' : 'text-gray-500'}`}>Model ID</div>
                  <div className={`text-sm ${isDark ? 'text-slate-300' : 'text-gray-700'} font-mono truncate`}>{modelId}</div>
                </div>
              )}
            </div>

            {/* Configuration parameters */}
            {Object.keys(config).length > 0 && (
              <div>
                <div className={`text-xs ${isDark ? 'text-slate-500' : 'text-gray-500'} mb-2`}>Configuration Parameters</div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {Object.entries(config).map(([key, value]) => (
                    <div key={key} className={`p-2 ${isDark ? 'bg-slate-800/50' : 'bg-white border border-gray-200'} rounded`}>
                      <div className={`text-xs ${isDark ? 'text-slate-500' : 'text-gray-500'}`}>{key.replace(/_/g, ' ')}</div>
                      <div className={`text-sm ${isDark ? 'text-slate-300' : 'text-gray-700'} font-mono`}>
                        {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Timestamp */}
            <div className={`flex items-center justify-between text-xs ${isDark ? 'text-slate-500' : 'text-gray-500'}`}>
              <span>Generated: {new Date().toLocaleString()}</span>
              <div className="flex gap-2">
                <button
                  onClick={copyConfig}
                  className={`inline-flex items-center gap-1 px-2 py-1 ${isDark ? 'bg-slate-800 border-slate-700 hover:bg-slate-700 text-slate-300' : 'bg-white border-gray-300 hover:bg-gray-100 text-gray-700'} border rounded transition-colors`}
                >
                  {copied ? (
                    <>
                      <svg className="w-3 h-3 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      Copied
                    </>
                  ) : (
                    <>
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                      Copy JSON
                    </>
                  )}
                </button>
                <button
                  onClick={downloadConfig}
                  className={`inline-flex items-center gap-1 px-2 py-1 ${isDark ? 'bg-slate-800 border-slate-700 hover:bg-slate-700 text-slate-300' : 'bg-white border-gray-300 hover:bg-gray-100 text-gray-700'} border rounded transition-colors`}
                >
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Download
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ReproducibilityPanel
