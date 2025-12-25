import { useState, useEffect } from 'react'
import Plot from 'react-plotly.js'
import { usePipeline } from '../../context/PipelineContext'
import { useTheme } from '../../context/ThemeContext'
import { trainingApi } from '../../api'
import Card from '../common/Card'

// Color palette for models
const MODEL_COLORS = [
  '#3b82f6', // blue
  '#10b981', // green
  '#f59e0b', // amber
  '#ef4444', // red
  '#8b5cf6', // purple
  '#ec4899', // pink
  '#06b6d4', // cyan
  '#84cc16', // lime
]

function ComparisonPage() {
  const { models, refreshModels } = usePipeline()
  const { isDark } = useTheme()
  const [selectedModelIds, setSelectedModelIds] = useState([])
  const [comparisonData, setComparisonData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('metrics')

  useEffect(() => {
    refreshModels()
  }, [refreshModels])

  const handleModelToggle = (modelId) => {
    setSelectedModelIds(prev => {
      if (prev.includes(modelId)) {
        return prev.filter(id => id !== modelId)
      }
      return [...prev, modelId]
    })
  }

  const handleCompare = async () => {
    if (selectedModelIds.length < 2) return

    setLoading(true)
    try {
      const response = await trainingApi.compareModels(selectedModelIds)
      setComparisonData(response.data)
    } catch (error) {
      console.error('Failed to compare models:', error)
    } finally {
      setLoading(false)
    }
  }

  const getPlotlyLayout = (baseLayout) => ({
    ...baseLayout,
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { color: isDark ? '#94a3b8' : '#475569' },
    xaxis: {
      ...baseLayout.xaxis,
      gridcolor: isDark ? '#334155' : '#e2e8f0',
      linecolor: isDark ? '#475569' : '#cbd5e1',
    },
    yaxis: {
      ...baseLayout.yaxis,
      gridcolor: isDark ? '#334155' : '#e2e8f0',
      linecolor: isDark ? '#475569' : '#cbd5e1',
    },
    legend: {
      ...baseLayout.legend,
      font: { color: isDark ? '#94a3b8' : '#475569', size: 11 }
    }
  })

  const tabs = [
    { id: 'metrics', label: 'Metrics' },
    { id: 'roc', label: 'ROC Curves' },
    { id: 'pr', label: 'PR Curves' },
    { id: 'features', label: 'Features' },
    { id: 'confusion', label: 'Confusion' }
  ]

  return (
    <div className="space-y-4 sm:space-y-6">
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white">Model Comparison</h1>
        <p className="text-sm sm:text-base text-slate-600 dark:text-slate-400 mt-1">Compare performance across multiple models</p>
      </div>

      {/* Model Selection */}
      <Card title="Select Models to Compare">
        {models.length < 2 ? (
          <p className="text-slate-500 dark:text-slate-400 text-sm sm:text-base">
            You need at least 2 trained models to compare. Currently have {models.length} model(s).
          </p>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {models.map((model, index) => (
                <label
                  key={model.id}
                  className={`flex items-start p-3 border rounded-lg cursor-pointer transition-colors ${
                    selectedModelIds.includes(model.id)
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600 bg-white dark:bg-slate-800/50'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedModelIds.includes(model.id)}
                    onChange={() => handleModelToggle(model.id)}
                    className="mt-1 mr-3 h-4 w-4 rounded border-slate-300 dark:border-slate-600 text-blue-600 focus:ring-blue-500"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center">
                      <span
                        className="w-3 h-3 rounded-full mr-2 flex-shrink-0"
                        style={{ backgroundColor: MODEL_COLORS[index % MODEL_COLORS.length] }}
                      />
                      <p className="font-medium text-sm text-slate-900 dark:text-white truncate">
                        {model.model_name || model.model_type}
                      </p>
                    </div>
                    <p className="text-xs text-slate-500 dark:text-slate-400 font-mono truncate mt-1">{model.id}</p>
                    <div className="mt-1 flex justify-between text-xs text-slate-600 dark:text-slate-300">
                      <span>AUC: {model.metrics?.roc_auc?.toFixed(3)}</span>
                      <span>AP: {model.metrics?.average_precision?.toFixed(3)}</span>
                    </div>
                  </div>
                </label>
              ))}
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-200 dark:border-slate-700">
              <span className="text-sm text-slate-600 dark:text-slate-400">
                {selectedModelIds.length} model(s) selected
              </span>
              <button
                onClick={handleCompare}
                disabled={selectedModelIds.length < 2 || loading}
                className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
                  selectedModelIds.length >= 2
                    ? 'bg-blue-600 hover:bg-blue-700 text-white'
                    : 'bg-slate-200 dark:bg-slate-700 text-slate-400 dark:text-slate-500 cursor-not-allowed'
                }`}
              >
                {loading ? 'Comparing...' : 'Compare Models'}
              </button>
            </div>
          </div>
        )}
      </Card>

      {/* Comparison Results */}
      {comparisonData && comparisonData.models.length >= 2 && (
        <>
          {/* Tabs */}
          <div className="flex overflow-x-auto scrollbar-hide -mx-4 px-4 sm:mx-0 sm:px-0">
            <div className="flex space-x-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-lg">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-3 sm:px-4 py-2 text-xs sm:text-sm font-medium rounded-lg whitespace-nowrap transition-colors ${
                    activeTab === tab.id
                      ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* Metrics Comparison Table */}
          {activeTab === 'metrics' && (
            <Card title="Performance Metrics">
              <div className="overflow-x-auto -mx-6">
                <table className="w-full min-w-[600px]">
                  <thead>
                    <tr className="border-b border-slate-200 dark:border-slate-700">
                      <th className="text-left py-3 px-6 text-sm font-semibold text-slate-900 dark:text-white">Model</th>
                      <th className="text-center py-3 px-4 text-sm font-semibold text-slate-900 dark:text-white">ROC AUC</th>
                      <th className="text-center py-3 px-4 text-sm font-semibold text-slate-900 dark:text-white">Avg Precision</th>
                      <th className="text-center py-3 px-4 text-sm font-semibold text-slate-900 dark:text-white">Precision</th>
                      <th className="text-center py-3 px-4 text-sm font-semibold text-slate-900 dark:text-white">Recall</th>
                      <th className="text-center py-3 px-4 text-sm font-semibold text-slate-900 dark:text-white">F1</th>
                    </tr>
                  </thead>
                  <tbody>
                    {comparisonData.models.map((model, index) => (
                      <tr key={model.model_id} className="border-b border-slate-100 dark:border-slate-800">
                        <td className="py-3 px-6">
                          <div className="flex items-center">
                            <span
                              className="w-3 h-3 rounded-full mr-3 flex-shrink-0"
                              style={{ backgroundColor: MODEL_COLORS[index % MODEL_COLORS.length] }}
                            />
                            <span className="text-sm font-medium text-slate-900 dark:text-white">
                              {model.model_name || model.model_type}
                            </span>
                          </div>
                        </td>
                        {['roc_auc', 'average_precision', 'precision', 'recall', 'f1'].map(metric => (
                          <td
                            key={metric}
                            className={`text-center py-3 px-4 text-sm font-mono ${
                              comparisonData.best_by[metric] === model.model_id
                                ? 'text-green-600 dark:text-green-400 font-bold'
                                : 'text-slate-600 dark:text-slate-400'
                            }`}
                          >
                            {model.metrics?.[metric]?.toFixed(4) || '-'}
                            {comparisonData.best_by[metric] === model.model_id && (
                              <span className="ml-1 text-xs">*</span>
                            )}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-3 px-6">
                * Best performing model for this metric
              </p>
            </Card>
          )}

          {/* ROC Curves */}
          {activeTab === 'roc' && (
            <Card title="ROC Curves Comparison">
              <Plot
                data={[
                  ...comparisonData.models.map((model, index) => ({
                    x: model.roc_curve?.fpr || [],
                    y: model.roc_curve?.tpr || [],
                    type: 'scatter',
                    mode: 'lines',
                    name: `${model.model_name || model.model_type} (AUC=${model.roc_curve?.auc?.toFixed(3) || '-'})`,
                    line: { color: MODEL_COLORS[index % MODEL_COLORS.length], width: 2 }
                  })),
                  {
                    x: [0, 1],
                    y: [0, 1],
                    type: 'scatter',
                    mode: 'lines',
                    name: 'Random',
                    line: { color: '#9ca3af', width: 1, dash: 'dash' }
                  }
                ]}
                layout={getPlotlyLayout({
                  xaxis: { title: 'False Positive Rate', range: [0, 1] },
                  yaxis: { title: 'True Positive Rate', range: [0, 1] },
                  showlegend: true,
                  legend: { orientation: 'h', y: -0.2 },
                  margin: { t: 20, r: 20, b: 80, l: 50 },
                  autosize: true
                })}
                useResizeHandler
                style={{ width: '100%', height: '400px' }}
                config={{ displayModeBar: false }}
              />
            </Card>
          )}

          {/* PR Curves */}
          {activeTab === 'pr' && (
            <Card title="Precision-Recall Curves Comparison">
              <Plot
                data={comparisonData.models.map((model, index) => ({
                  x: model.pr_curve?.recall || [],
                  y: model.pr_curve?.precision || [],
                  type: 'scatter',
                  mode: 'lines',
                  name: `${model.model_name || model.model_type} (AP=${model.pr_curve?.average_precision?.toFixed(3) || '-'})`,
                  line: { color: MODEL_COLORS[index % MODEL_COLORS.length], width: 2 }
                }))}
                layout={getPlotlyLayout({
                  xaxis: { title: 'Recall', range: [0, 1] },
                  yaxis: { title: 'Precision', range: [0, 1] },
                  showlegend: true,
                  legend: { orientation: 'h', y: -0.2 },
                  margin: { t: 20, r: 20, b: 80, l: 50 },
                  autosize: true
                })}
                useResizeHandler
                style={{ width: '100%', height: '400px' }}
                config={{ displayModeBar: false }}
              />
            </Card>
          )}

          {/* Feature Importance Comparison */}
          {activeTab === 'features' && (
            <Card title="Feature Importance Comparison (Top 10)">
              <Plot
                data={comparisonData.models.map((model, index) => {
                  const top10 = model.feature_importance?.slice(0, 10) || []
                  return {
                    x: top10.map(f => f.importance),
                    y: top10.map(f => f.feature),
                    type: 'bar',
                    orientation: 'h',
                    name: model.model_name || model.model_type,
                    marker: { color: MODEL_COLORS[index % MODEL_COLORS.length] }
                  }
                })}
                layout={getPlotlyLayout({
                  barmode: 'group',
                  xaxis: { title: 'Importance' },
                  yaxis: { automargin: true, tickfont: { size: 10 } },
                  showlegend: true,
                  legend: { orientation: 'h', y: -0.15 },
                  margin: { t: 20, r: 20, b: 60, l: 150 },
                  autosize: true
                })}
                useResizeHandler
                style={{ width: '100%', height: '500px' }}
                config={{ displayModeBar: false }}
              />
            </Card>
          )}

          {/* Confusion Matrices */}
          {activeTab === 'confusion' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {comparisonData.models.map((model, index) => (
                <Card key={model.model_id} title={model.model_name || model.model_type}>
                  <div className="flex justify-center">
                    <Plot
                      data={[
                        {
                          z: model.metrics?.confusion_matrix || [[0, 0], [0, 0]],
                          x: ['Pred. No Injury', 'Pred. Injury'],
                          y: ['No Injury', 'Injury'],
                          type: 'heatmap',
                          colorscale: [
                            [0, isDark ? '#1e293b' : '#f1f5f9'],
                            [1, MODEL_COLORS[index % MODEL_COLORS.length]]
                          ],
                          showscale: false,
                          text: (model.metrics?.confusion_matrix || [[0, 0], [0, 0]]).map(row =>
                            row.map(val => val.toLocaleString())
                          ),
                          texttemplate: '%{text}',
                          textfont: { size: 12, color: isDark ? '#fff' : '#000' },
                          hovertemplate: '%{y} / %{x}: %{z}<extra></extra>'
                        }
                      ]}
                      layout={getPlotlyLayout({
                        xaxis: { tickfont: { size: 9 } },
                        yaxis: { autorange: 'reversed', tickfont: { size: 9 } },
                        margin: { t: 10, r: 10, b: 40, l: 70 },
                        autosize: true
                      })}
                      useResizeHandler
                      style={{ width: '100%', height: '200px' }}
                      config={{ displayModeBar: false }}
                    />
                  </div>
                </Card>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default ComparisonPage
