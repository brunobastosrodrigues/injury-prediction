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
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Results</h1>
        <p className="text-gray-600 mt-1">View and compare model performance</p>
      </div>

      {/* Model Selection */}
      <Card title="Select Model">
        {models.length === 0 ? (
          <p className="text-gray-500">No trained models. Train some models first.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {models.map(model => (
              <button
                key={model.id}
                onClick={() => setSelectedModel(model)}
                className={`p-4 border rounded-lg text-left transition-colors ${
                  selectedModel?.id === model.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <p className="font-medium">{model.model_name || model.model_type}</p>
                <p className="text-sm text-gray-500 font-mono truncate">{model.id}</p>
                <div className="mt-2 flex justify-between text-sm">
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
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-blue-600">
                  {selectedModel.metrics?.roc_auc?.toFixed(4)}
                </p>
                <p className="text-sm text-gray-500">ROC AUC</p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-green-600">
                  {selectedModel.metrics?.average_precision?.toFixed(4)}
                </p>
                <p className="text-sm text-gray-500">Avg Precision</p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-purple-600">
                  {selectedModel.metrics?.precision?.toFixed(4)}
                </p>
                <p className="text-sm text-gray-500">Precision</p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-orange-600">
                  {selectedModel.metrics?.recall?.toFixed(4)}
                </p>
                <p className="text-sm text-gray-500">Recall</p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-pink-600">
                  {selectedModel.metrics?.f1?.toFixed(4)}
                </p>
                <p className="text-sm text-gray-500">F1 Score</p>
              </div>
            </div>
          </Card>

          {/* Charts */}
          {loading ? (
            <Card title="Loading...">
              <div className="flex justify-center py-12">
                <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
              </div>
            </Card>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
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
                      legend: { x: 0.6, y: 0.1 },
                      margin: { t: 20, r: 20, b: 50, l: 50 },
                      autosize: true
                    }}
                    useResizeHandler
                    style={{ width: '100%', height: '350px' }}
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
                      legend: { x: 0.1, y: 0.1 },
                      margin: { t: 20, r: 20, b: 50, l: 50 },
                      autosize: true
                    }}
                    useResizeHandler
                    style={{ width: '100%', height: '350px' }}
                  />
                </Card>
              )}
            </div>
          )}

          {/* Feature Importance */}
          {featureImportance && featureImportance.feature_importance?.length > 0 && (
            <Card title="Feature Importance (Top 20)">
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
                  yaxis: { automargin: true },
                  margin: { t: 20, r: 20, b: 50, l: 200 },
                  autosize: true
                }}
                useResizeHandler
                style={{ width: '100%', height: '500px' }}
              />
            </Card>
          )}

          {/* Confusion Matrix */}
          {selectedModel.metrics?.confusion_matrix && (
            <Card title="Confusion Matrix">
              <div className="flex justify-center">
                <Plot
                  data={[
                    {
                      z: selectedModel.metrics.confusion_matrix,
                      x: ['Predicted No Injury', 'Predicted Injury'],
                      y: ['Actual No Injury', 'Actual Injury'],
                      type: 'heatmap',
                      colorscale: 'Blues',
                      showscale: true,
                      text: selectedModel.metrics.confusion_matrix.map(row =>
                        row.map(val => val.toLocaleString())
                      ),
                      texttemplate: '%{text}',
                      hovertemplate: '%{y} / %{x}: %{z}<extra></extra>'
                    }
                  ]}
                  layout={{
                    xaxis: { title: 'Predicted' },
                    yaxis: { title: 'Actual', autorange: 'reversed' },
                    margin: { t: 20, r: 80, b: 80, l: 100 },
                    autosize: true
                  }}
                  useResizeHandler
                  style={{ width: '100%', maxWidth: '500px', height: '400px' }}
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
