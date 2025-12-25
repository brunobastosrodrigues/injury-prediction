import { useState, useEffect } from 'react'
import Plot from 'react-plotly.js'
import { usePipeline } from '../../context/PipelineContext'
import { trainingApi, analyticsApi } from '../../api'
import Card from '../common/Card'

function ResultsPage() {
  const { models, refreshModels } = usePipeline()
  const [selectedModel, setSelectedModel] = useState(null)
  const [rocData, setRocData] = useState(null)
  const [prData, setPrData] = useState(null)
  const [featureImportance, setFeatureImportance] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    refreshModels()
  }, [refreshModels])

  useEffect(() => {
    if (selectedModel) {
      loadModelData(selectedModel)
    }
  }, [selectedModel])

  const loadModelData = async (model) => {
    setLoading(true)
    try {
      const [rocRes, prRes, fiRes] = await Promise.all([
        trainingApi.getRocCurve(model.id, model.split_id),
        trainingApi.getPrCurve(model.id, model.split_id),
        analyticsApi.getFeatureImportance(model.id)
      ])

      setRocData(rocRes.data)
      setPrData(prRes.data)
      setFeatureImportance(fiRes.data)
    } catch (error) {
      console.error('Failed to load model data:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Results</h1>
        <p className="text-sm sm:text-base text-gray-600 mt-1">View and compare model performance</p>
      </div>

      {/* Model Selection */}
      <Card title="Select Model">
        {models.length === 0 ? (
          <p className="text-gray-500 text-sm sm:text-base">No trained models. Train some models first.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
            {models.map(model => (
              <button
                key={model.id}
                onClick={() => setSelectedModel(model)}
                className={`p-3 sm:p-4 border rounded-lg text-left transition-colors ${
                  selectedModel?.id === model.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <p className="font-medium text-sm sm:text-base">{model.model_name || model.model_type}</p>
                <p className="text-xs sm:text-sm text-gray-500 font-mono truncate">{model.id}</p>
                <div className="mt-2 flex justify-between text-xs sm:text-sm">
                  <span>AUC: {model.metrics?.roc_auc?.toFixed(3)}</span>
                  <span>AP: {model.metrics?.average_precision?.toFixed(3)}</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </Card>

      {selectedModel && (
        <>
          {/* Metrics Summary */}
          <Card title="Performance Metrics">
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2 sm:gap-4">
              <div className="text-center p-2 sm:p-4 bg-gray-50 rounded-lg">
                <p className="text-lg sm:text-2xl font-bold text-blue-600">
                  {selectedModel.metrics?.roc_auc?.toFixed(4)}
                </p>
                <p className="text-xs sm:text-sm text-gray-500">ROC AUC</p>
              </div>
              <div className="text-center p-2 sm:p-4 bg-gray-50 rounded-lg">
                <p className="text-lg sm:text-2xl font-bold text-green-600">
                  {selectedModel.metrics?.average_precision?.toFixed(4)}
                </p>
                <p className="text-xs sm:text-sm text-gray-500">Avg Precision</p>
              </div>
              <div className="text-center p-2 sm:p-4 bg-gray-50 rounded-lg">
                <p className="text-lg sm:text-2xl font-bold text-purple-600">
                  {selectedModel.metrics?.precision?.toFixed(4)}
                </p>
                <p className="text-xs sm:text-sm text-gray-500">Precision</p>
              </div>
              <div className="text-center p-2 sm:p-4 bg-gray-50 rounded-lg">
                <p className="text-lg sm:text-2xl font-bold text-orange-600">
                  {selectedModel.metrics?.recall?.toFixed(4)}
                </p>
                <p className="text-xs sm:text-sm text-gray-500">Recall</p>
              </div>
              <div className="text-center p-2 sm:p-4 bg-gray-50 rounded-lg col-span-2 sm:col-span-1">
                <p className="text-lg sm:text-2xl font-bold text-pink-600">
                  {selectedModel.metrics?.f1?.toFixed(4)}
                </p>
                <p className="text-xs sm:text-sm text-gray-500">F1 Score</p>
              </div>
            </div>
          </Card>

          {/* Charts */}
          {loading ? (
            <Card title="Loading...">
              <div className="flex justify-center py-8 sm:py-12">
                <div className="animate-spin h-6 w-6 sm:h-8 sm:w-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
              </div>
            </Card>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
              {/* ROC Curve */}
              {rocData && (
                <Card title="ROC Curve">
                  <Plot
                    data={[
                      {
                        x: rocData.fpr,
                        y: rocData.tpr,
                        type: 'scatter',
                        mode: 'lines',
                        name: `AUC = ${rocData.auc.toFixed(3)}`,
                        line: { color: '#3b82f6', width: 2 }
                      },
                      {
                        x: [0, 1],
                        y: [0, 1],
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Random',
                        line: { color: '#9ca3af', width: 1, dash: 'dash' }
                      }
                    ]}
                    layout={{
                      xaxis: { title: 'False Positive Rate', range: [0, 1] },
                      yaxis: { title: 'True Positive Rate', range: [0, 1] },
                      showlegend: true,
                      legend: { x: 0.5, y: 0.1, font: { size: 10 } },
                      margin: { t: 10, r: 10, b: 40, l: 40 },
                      autosize: true
                    }}
                    useResizeHandler
                    style={{ width: '100%', height: '280px' }}
                    config={{ displayModeBar: false }}
                  />
                </Card>
              )}

              {/* PR Curve */}
              {prData && (
                <Card title="Precision-Recall Curve">
                  <Plot
                    data={[
                      {
                        x: prData.recall,
                        y: prData.precision,
                        type: 'scatter',
                        mode: 'lines',
                        name: `AP = ${prData.average_precision.toFixed(3)}`,
                        line: { color: '#10b981', width: 2 }
                      }
                    ]}
                    layout={{
                      xaxis: { title: 'Recall', range: [0, 1] },
                      yaxis: { title: 'Precision', range: [0, 1] },
                      showlegend: true,
                      legend: { x: 0.1, y: 0.1, font: { size: 10 } },
                      margin: { t: 10, r: 10, b: 40, l: 40 },
                      autosize: true
                    }}
                    useResizeHandler
                    style={{ width: '100%', height: '280px' }}
                    config={{ displayModeBar: false }}
                  />
                </Card>
              )}
            </div>
          )}

          {/* Feature Importance */}
          {featureImportance && featureImportance.feature_importance?.length > 0 && (
            <Card title="Feature Importance (Top 20)">
              <div className="-mx-2 sm:mx-0 overflow-x-auto">
                <Plot
                  data={[
                    {
                      x: featureImportance.feature_importance.slice(0, 20).map(f => f.importance),
                      y: featureImportance.feature_importance.slice(0, 20).map(f => f.feature),
                      type: 'bar',
                      orientation: 'h',
                      marker: { color: '#6366f1' }
                    }
                  ]}
                  layout={{
                    xaxis: { title: 'Importance' },
                    yaxis: { automargin: true, tickfont: { size: 10 } },
                    margin: { t: 10, r: 10, b: 40, l: 120 },
                    autosize: true
                  }}
                  useResizeHandler
                  style={{ width: '100%', minWidth: '300px', height: '450px' }}
                  config={{ displayModeBar: false }}
                />
              </div>
            </Card>
          )}

          {/* Confusion Matrix */}
          {selectedModel.metrics?.confusion_matrix && (
            <Card title="Confusion Matrix">
              <div className="flex justify-center overflow-x-auto">
                <Plot
                  data={[
                    {
                      z: selectedModel.metrics.confusion_matrix,
                      x: ['Pred. No Injury', 'Pred. Injury'],
                      y: ['No Injury', 'Injury'],
                      type: 'heatmap',
                      colorscale: 'Blues',
                      showscale: false,
                      text: selectedModel.metrics.confusion_matrix.map(row =>
                        row.map(val => val.toLocaleString())
                      ),
                      texttemplate: '%{text}',
                      textfont: { size: 14 },
                      hovertemplate: '%{y} / %{x}: %{z}<extra></extra>'
                    }
                  ]}
                  layout={{
                    xaxis: { title: 'Predicted', tickfont: { size: 11 } },
                    yaxis: { title: 'Actual', autorange: 'reversed', tickfont: { size: 11 } },
                    margin: { t: 10, r: 10, b: 60, l: 80 },
                    autosize: true
                  }}
                  useResizeHandler
                  style={{ width: '100%', maxWidth: '400px', height: '300px' }}
                  config={{ displayModeBar: false }}
                />
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  )
}

export default ResultsPage
