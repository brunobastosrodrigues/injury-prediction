import { useState } from 'react'

/**
 * CitationBlock - Academic citation component
 * Provides BibTeX export and citation formatting for research use
 */
function CitationBlock({
  title = 'Injury Risk Prediction in Triathletes',
  authors = 'Embedded Sensing Group',
  institution = 'University of St. Gallen',
  year = new Date().getFullYear(),
  url = null,
  doi = null,
  className = ''
}) {
  const [copied, setCopied] = useState(false)
  const [format, setFormat] = useState('bibtex')

  const bibtex = `@misc{injury_prediction_${year},
  title = {${title}},
  author = {${authors}},
  institution = {${institution}},
  year = {${year}},
  ${url ? `url = {${url}},` : ''}
  ${doi ? `doi = {${doi}},` : ''}
  note = {Research Platform for Prospective Injury Risk Prediction}
}`

  const apa = `${authors}. (${year}). ${title}. ${institution}.${doi ? ` https://doi.org/${doi}` : ''}`

  const chicago = `${authors}. "${title}." ${institution}, ${year}.${doi ? ` https://doi.org/${doi}` : ''}`

  const citations = { bibtex, apa, chicago }

  const copyToClipboard = () => {
    navigator.clipboard.writeText(citations[format])
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className={`bg-slate-900/50 border border-slate-800 rounded-xl p-4 ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-semibold text-white flex items-center gap-2">
          <svg className="w-4 h-4 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          Cite This Work
        </h4>

        <div className="flex items-center gap-2">
          <select
            value={format}
            onChange={(e) => setFormat(e.target.value)}
            className="text-xs bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-300"
          >
            <option value="bibtex">BibTeX</option>
            <option value="apa">APA</option>
            <option value="chicago">Chicago</option>
          </select>

          <button
            onClick={copyToClipboard}
            className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-slate-300 bg-slate-800 border border-slate-700 rounded hover:bg-slate-700 transition-colors"
          >
            {copied ? (
              <>
                <svg className="w-3 h-3 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Copied
              </>
            ) : (
              <>
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                Copy
              </>
            )}
          </button>
        </div>
      </div>

      <pre className="text-xs text-slate-400 bg-slate-800/50 rounded p-3 overflow-x-auto font-mono whitespace-pre-wrap">
        {citations[format]}
      </pre>
    </div>
  )
}

export default CitationBlock
