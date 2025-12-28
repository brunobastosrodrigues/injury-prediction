import { useState } from 'react'

/**
 * ExportButton - Academic-focused export functionality
 * Supports exporting data in various formats for research publications
 */
function ExportButton({
  data,
  filename = 'export',
  formats = ['csv', 'json'],
  plotRef = null,
  className = ''
}) {
  const [isOpen, setIsOpen] = useState(false)
  const [exporting, setExporting] = useState(false)

  const exportCSV = () => {
    if (!data || !Array.isArray(data)) return

    const headers = Object.keys(data[0] || {})
    const csvContent = [
      headers.join(','),
      ...data.map(row => headers.map(h => JSON.stringify(row[h] ?? '')).join(','))
    ].join('\n')

    downloadFile(csvContent, `${filename}.csv`, 'text/csv')
  }

  const exportJSON = () => {
    if (!data) return
    const jsonContent = JSON.stringify(data, null, 2)
    downloadFile(jsonContent, `${filename}.json`, 'application/json')
  }

  const exportPlotSVG = async () => {
    if (!plotRef?.current) return
    setExporting(true)
    try {
      const Plotly = await import('plotly.js')
      const svgData = await Plotly.toImage(plotRef.current, { format: 'svg', width: 800, height: 600 })
      const link = document.createElement('a')
      link.href = svgData
      link.download = `${filename}.svg`
      link.click()
    } catch (err) {
      console.error('Failed to export SVG:', err)
    }
    setExporting(false)
  }

  const exportPlotPNG = async () => {
    if (!plotRef?.current) return
    setExporting(true)
    try {
      const Plotly = await import('plotly.js')
      const pngData = await Plotly.toImage(plotRef.current, { format: 'png', width: 1200, height: 900, scale: 2 })
      const link = document.createElement('a')
      link.href = pngData
      link.download = `${filename}.png`
      link.click()
    } catch (err) {
      console.error('Failed to export PNG:', err)
    }
    setExporting(false)
  }

  const downloadFile = (content, filename, mimeType) => {
    const blob = new Blob([content], { type: mimeType })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  const formatOptions = {
    csv: { label: 'CSV', icon: '📊', action: exportCSV, description: 'Spreadsheet format' },
    json: { label: 'JSON', icon: '{ }', action: exportJSON, description: 'Structured data' },
    svg: { label: 'SVG', icon: '🎨', action: exportPlotSVG, description: 'Vector graphics' },
    png: { label: 'PNG', icon: '🖼️', action: exportPlotPNG, description: 'High-res image' }
  }

  const availableFormats = formats.filter(f => formatOptions[f])

  return (
    <div className={`relative ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={exporting}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-300 bg-slate-800 border border-slate-700 rounded-lg hover:bg-slate-700 hover:text-white transition-colors disabled:opacity-50"
      >
        {exporting ? (
          <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        ) : (
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
        )}
        Export
        <svg className={`w-3 h-3 transition-transform ${isOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
          <div className="absolute right-0 mt-1 w-44 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-20 py-1">
            {availableFormats.map(format => {
              const opt = formatOptions[format]
              return (
                <button
                  key={format}
                  onClick={() => {
                    opt.action()
                    setIsOpen(false)
                  }}
                  className="w-full px-3 py-2 text-left text-sm text-slate-300 hover:bg-slate-700 hover:text-white flex items-center gap-2"
                >
                  <span className="w-5 text-center text-xs">{opt.icon}</span>
                  <div>
                    <div className="font-medium">{opt.label}</div>
                    <div className="text-xs text-slate-500">{opt.description}</div>
                  </div>
                </button>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}

export default ExportButton
