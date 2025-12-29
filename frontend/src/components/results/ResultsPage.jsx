import { useState, useEffect, useRef } from 'react'
import Plot from 'react-plotly.js'
import { usePipeline } from '../../context/PipelineContext'
import { trainingApi, analyticsApi } from '../../api'
import Card from '../common/Card'
import StatisticalMetric from '../common/StatisticalMetric'
import MethodologyTooltip, { METHODOLOGY_TERMS } from '../common/MethodologyTooltip'
import ExportButton from '../common/ExportButton'
import ReproducibilityPanel from '../common/ReproducibilityPanel'
import CitationBlock from '../common/CitationBlock'

function ResultsPage() {
  const { models, refreshModels, splits } = usePipeline()
  const [selectedModel, setSelectedModel] = useState(null)
  const [rocData, setRocData] = useState(null)
  const [prData, setPrData] = useState(null)
  const [featureImportance, setFeatureImportance] = useState(null)
  const [loading, setLoading] = useState(false)
  const [showCitation, setShowCitation] = useState(false)

  // Refs for plot export
  const rocPlotRef = useRef(null)
  const prPlotRef = useRef(null)
  const fiPlotRef = useRef(null)

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
      // Use individual catches to prevent one failure from blocking all data
      const [rocRes, prRes, fiRes] = await Promise.all([
        trainingApi.getRocCurve(model.id, model.split_id).catch(err => {
          console.warn('Failed to load ROC curve:', err)
          return { data: null }
        }),
        trainingApi.getPrCurve(model.id, model.split_id).catch(err => {
          console.warn('Failed to load PR curve:', err)
          return { data: null }
        }),
        analyticsApi.getFeatureImportance(model.id).catch(err => {
          console.warn('Failed to load feature importance:', err)
          return { data: null }
        })
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

  // Get split info for the selected model
  const selectedSplit = splits.find(s => s.id === selectedModel?.split_id)

  // Prepare data for export
  const getMetricsExportData = () => {
    if (!selectedModel?.metrics) return []
    const m = selectedModel.metrics
    return [
      { metric: 'ROC-AUC', value: m.roc_auc, description: 'Area Under ROC Curve' },
      { metric: 'Average Precision', value: m.average_precision, description: 'Area Under PR Curve' },
      { metric: 'Precision', value: m.precision, description: 'Positive Predictive Value' },
      { metric: 'Recall', value: m.recall, description: 'Sensitivity / True Positive Rate' },
      { metric: 'F1 Score', value: m.f1, description: 'Harmonic Mean of Precision and Recall' },
      { metric: 'Specificity', value: m.specificity, description: 'True Negative Rate' },
      { metric: 'Accuracy', value: m.accuracy, description: 'Overall Classification Accuracy' }
    ]
  }

  const getROCExportData = () => {
    if (!rocData || !rocData.fpr || !rocData.tpr) return []
    return rocData.fpr.map((fpr, i) => ({
      false_positive_rate: fpr,
      true_positive_rate: i < rocData.tpr.length ? rocData.tpr[i] : null,
      threshold: rocData.thresholds && i < rocData.thresholds.length ? rocData.thresholds[i] : null
    }))
  }

  // Dark theme layout for Plotly
  const darkLayout = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(15,23,42,0.5)',
    font: { color: '#94a3b8', size: 11 },
    xaxis: { gridcolor: '#334155', zerolinecolor: '#475569' },
    yaxis: { gridcolor: '#334155', zerolinecolor: '#475569' },
    legend: { bgcolor: 'rgba(0,0,0,0)', font: { color: '#cbd5e1' } }
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-white">Model Evaluation Results</h1>
          <p className="text-sm sm:text-base text-slate-400 mt-1">
            Performance metrics, discrimination curves, and feature attribution analysis
          </p>
        </div>
        <button
          onClick={() => setShowCitation(!showCitation)}
          className="inline-flex items-center gap-2 px-3 py-2 text-sm text-slate-300 bg-slate-800 border border-slate-700 rounded-lg hover:bg-slate-700 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          Cite
        </button>
      </div>

      {showCitation && (
        <CitationBlock className="animate-in fade-in duration-200" />
      )}

      {/* Model Selection */}
      <Card
        title="Model Selection"
        actions={
          selectedModel && (
            <ExportButton
              data={getMetricsExportData()}
              filename={`model_metrics_${selectedModel.id}`}
              formats={['csv', 'json']}
            />
          )
        }
      >
        {models.length === 0 ? (
          <div className="text-center py-8">
            <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
              </svg>
            </div>
            <p className="text-slate-400">No trained models available</p>
            <p className="text-slate-500 text-sm mt-1">Train a model first to view evaluation results</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
            {models.map(model => (
              <button
                key={model.id}
                onClick={() => setSelectedModel(model)}
                className={`p-3 sm:p-4 border rounded-xl text-left transition-all ${
                  selectedModel?.id === model.id
                    ? 'border-blue-500 bg-blue-500/10 ring-1 ring-blue-500/50'
                    : 'border-slate-700 bg-slate-800/50 hover:border-slate-600 hover:bg-slate-800'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className={`px-2 py-0.5 text-xs font-medium rounded ${
                    model.model_type === 'xgboost' ? 'bg-purple-500/20 text-purple-400' :
                    model.model_type === 'random_forest' ? 'bg-green-500/20 text-green-400' :
                    'bg-blue-500/20 text-blue-400'
                  }`}>
                    {model.model_name || model.model_type}
                  </span>
                  {selectedModel?.id === model.id && (
                    <svg className="w-4 h-4 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  )}
                </div>
                <p className="text-xs text-slate-500 font-mono truncate mb-2">{model.id}</p>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">
                    <MethodologyTooltip {...METHODOLOGY_TERMS.ROC_AUC}>AUC</MethodologyTooltip>: {' '}
                    <span className="text-white font-medium">{model.metrics?.roc_auc?.toFixed(3)}</span>
                  </span>
                  <span className="text-slate-400">
                    <MethodologyTooltip {...METHODOLOGY_TERMS.PR_AUC}>AP</MethodologyTooltip>: {' '}
                    <span className="text-white font-medium">{model.metrics?.average_precision?.toFixed(3)}</span>
                  </span>
                </div>
              </button>
            ))}
          </div>
        )}
      </Card>

      {selectedModel && (
        <>
          {/* Primary Metrics with Statistical Context */}
          <Card title="Performance Metrics">
            <div className="mb-4 p-3 bg-slate-800/50 rounded-lg border border-slate-700">
              <p className="text-xs text-slate-400">
                <strong className="text-slate-300">Interpretation Guide:</strong> For imbalanced datasets (typical injury rate ~2-5%),
                prioritize <MethodologyTooltip {...METHODOLOGY_TERMS.PR_AUC}>Average Precision (AP)</MethodologyTooltip> over
                <MethodologyTooltip {...METHODOLOGY_TERMS.ROC_AUC}> ROC-AUC</MethodologyTooltip>.
                AP is more sensitive to performance on the minority (injury) class.
              </p>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2 sm:gap-4">
              <StatisticalMetric
                label="ROC-AUC"
                value={selectedModel.metrics?.roc_auc}
                methodology="ROC_AUC"
                color="blue"
                precision={4}
              />
              <StatisticalMetric
                label="Avg Precision"
                value={selectedModel.metrics?.average_precision}
                methodology="PR_AUC"
                color="green"
                precision={4}
              />
              <StatisticalMetric
                label="Precision"
                value={selectedModel.metrics?.precision}
                color="purple"
                precision={4}
              />
              <StatisticalMetric
                label="Recall (Sensitivity)"
                value={selectedModel.metrics?.recall}
                color="orange"
                precision={4}
              />
              <StatisticalMetric
                label="F1 Score"
                value={selectedModel.metrics?.f1}
                color="red"
                precision={4}
                className="col-span-2 sm:col-span-1"
              />
            </div>

            {/* Additional metrics row */}
            {(selectedModel.metrics?.specificity || selectedModel.metrics?.accuracy) && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-4 mt-4 pt-4 border-t border-slate-800">
                {selectedModel.metrics?.specificity && (
                  <div className="p-3 bg-slate-800/30 rounded-lg">
                    <div className="text-lg font-bold text-slate-300">{selectedModel.metrics.specificity.toFixed(4)}</div>
                    <div className="text-xs text-slate-500">Specificity (TNR)</div>
                  </div>
                )}
                {selectedModel.metrics?.accuracy && (
                  <div className="p-3 bg-slate-800/30 rounded-lg">
                    <div className="text-lg font-bold text-slate-300">{selectedModel.metrics.accuracy.toFixed(4)}</div>
                    <div className="text-xs text-slate-500">Accuracy</div>
                  </div>
                )}
                {selectedModel.metrics?.brier_score !== undefined && (
                  <div className="p-3 bg-slate-800/30 rounded-lg">
                    <div className="text-lg font-bold text-slate-300">{selectedModel.metrics.brier_score.toFixed(4)}</div>
                    <div className="text-xs text-slate-500">Brier Score</div>
                  </div>
                )}
                {selectedModel.metrics?.log_loss !== undefined && (
                  <div className="p-3 bg-slate-800/30 rounded-lg">
                    <div className="text-lg font-bold text-slate-300">{selectedModel.metrics.log_loss.toFixed(4)}</div>
                    <div className="text-xs text-slate-500">Log Loss</div>
                  </div>
                )}
              </div>
            )}
          </Card>

          {/* Discrimination Curves */}
          {loading ? (
            <Card title="Loading Curves...">
              <div className="flex justify-center py-8 sm:py-12">
                <div className="animate-spin h-6 w-6 sm:h-8 sm:w-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
              </div>
            </Card>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
              {/* ROC Curve */}
              {rocData && (
                <Card
                  title={
                    <span className="flex items-center gap-2">
                      <MethodologyTooltip {...METHODOLOGY_TERMS.ROC_AUC}>ROC Curve</MethodologyTooltip>
                      <span className="text-xs font-normal text-slate-500">(Receiver Operating Characteristic)</span>
                    </span>
                  }
                  actions={
                    <ExportButton
                      data={getROCExportData()}
                      filename={`roc_curve_${selectedModel.id}`}
                      formats={['csv', 'json', 'svg', 'png']}
                      plotRef={rocPlotRef}
                    />
                  }
                >
                  <Plot
                    ref={rocPlotRef}
                    data={[
                      {
                        x: rocData.fpr,
                        y: rocData.tpr,
                        type: 'scatter',
                        mode: 'lines',
                        name: `Model (AUC = ${rocData.auc.toFixed(3)})`,
                        line: { color: '#3b82f6', width: 2 }
                      },
                      {
                        x: [0, 1],
                        y: [0, 1],
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Random Classifier',
                        line: { color: '#64748b', width: 1, dash: 'dash' }
                      }
                    ]}
                    layout={{
                      ...darkLayout,
                      xaxis: { ...darkLayout.xaxis, title: 'False Positive Rate (1 - Specificity)', range: [0, 1] },
                      yaxis: { ...darkLayout.yaxis, title: 'True Positive Rate (Sensitivity)', range: [0, 1] },
                      showlegend: true,
                      legend: { ...darkLayout.legend, x: 0.5, y: 0.1, font: { size: 10, color: '#cbd5e1' } },
                      margin: { t: 10, r: 10, b: 50, l: 50 },
                      autosize: true
                    }}
                    useResizeHandler
                    style={{ width: '100%', height: '300px' }}
                    config={{ displayModeBar: false }}
                  />
                  <div className="mt-2 text-xs text-slate-500 text-center">
                    AUC = {rocData.auc.toFixed(4)} | Optimal threshold analysis available via export
                  </div>
                </Card>
              )}

              {/* PR Curve */}
              {prData && (
                <Card
                  title={
                    <span className="flex items-center gap-2">
                      <MethodologyTooltip {...METHODOLOGY_TERMS.PR_AUC}>Precision-Recall Curve</MethodologyTooltip>
                    </span>
                  }
                  actions={
                    <ExportButton
                      data={prData.recall?.map((r, i) => ({
                        recall: r,
                        precision: prData.precision[i]
                      })) || []}
                      filename={`pr_curve_${selectedModel.id}`}
                      formats={['csv', 'json', 'svg', 'png']}
                      plotRef={prPlotRef}
                    />
                  }
                >
                  <Plot
                    ref={prPlotRef}
                    data={[
                      {
                        x: prData.recall,
                        y: prData.precision,
                        type: 'scatter',
                        mode: 'lines',
                        name: `Model (AP = ${prData.average_precision.toFixed(3)})`,
                        line: { color: '#10b981', width: 2 }
                      }
                    ]}
                    layout={{
                      ...darkLayout,
                      xaxis: { ...darkLayout.xaxis, title: 'Recall (Sensitivity)', range: [0, 1] },
                      yaxis: { ...darkLayout.yaxis, title: 'Precision (PPV)', range: [0, 1] },
                      showlegend: true,
                      legend: { ...darkLayout.legend, x: 0.1, y: 0.1, font: { size: 10, color: '#cbd5e1' } },
                      margin: { t: 10, r: 10, b: 50, l: 50 },
                      autosize: true
                    }}
                    useResizeHandler
                    style={{ width: '100%', height: '300px' }}
                    config={{ displayModeBar: false }}
                  />
                  <div className="mt-2 text-xs text-slate-500 text-center">
                    Average Precision = {prData.average_precision.toFixed(4)} | Recommended for imbalanced data
                  </div>
                </Card>
              )}
            </div>
          )}

          {/* Feature Importance */}
          {featureImportance && featureImportance.feature_importance?.length > 0 && (
            <Card
              title={
                <span className="flex items-center gap-2">
                  Feature Attribution
                  <span className="text-xs font-normal text-slate-500">
                    ({selectedModel.model_type === 'lasso' ? 'Coefficient Magnitude' : 'Impurity-based Importance'})
                  </span>
                </span>
              }
              actions={
                <ExportButton
                  data={featureImportance.feature_importance}
                  filename={`feature_importance_${selectedModel.id}`}
                  formats={['csv', 'json', 'svg', 'png']}
                  plotRef={fiPlotRef}
                />
              }
            >
              <div className="mb-4 p-3 bg-slate-800/50 rounded-lg border border-slate-700">
                <p className="text-xs text-slate-400">
                  <strong className="text-slate-300">Note:</strong> Feature importance reflects the relative contribution of each variable to model predictions.
                  For causal interpretation, consider using <MethodologyTooltip {...METHODOLOGY_TERMS.SHAP}>SHAP values</MethodologyTooltip> from the Interpretability page.
                </p>
              </div>
              <div className="-mx-2 sm:mx-0 overflow-x-auto">
                <Plot
                  ref={fiPlotRef}
                  data={[
                    {
                      x: featureImportance.feature_importance.slice(0, 20).map(f => f.importance),
                      y: featureImportance.feature_importance.slice(0, 20).map(f => f.feature),
                      type: 'bar',
                      orientation: 'h',
                      marker: {
                        color: featureImportance.feature_importance.slice(0, 20).map((_, i) =>
                          `rgba(99, 102, 241, ${1 - i * 0.03})`
                        )
                      }
                    }
                  ]}
                  layout={{
                    ...darkLayout,
                    xaxis: { ...darkLayout.xaxis, title: 'Importance Score' },
                    yaxis: { ...darkLayout.yaxis, automargin: true, tickfont: { size: 10, color: '#94a3b8' } },
                    margin: { t: 10, r: 10, b: 50, l: 140 },
                    autosize: true
                  }}
                  useResizeHandler
                  style={{ width: '100%', minWidth: '300px', height: '500px' }}
                  config={{ displayModeBar: false }}
                />
              </div>
            </Card>
          )}

          {/* Confusion Matrix */}
          {selectedModel.metrics?.confusion_matrix && (
            <Card title="Confusion Matrix">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="flex justify-center overflow-x-auto">
                  <Plot
                    data={[
                      {
                        z: selectedModel.metrics.confusion_matrix,
                        x: ['Predicted Negative', 'Predicted Positive'],
                        y: ['Actual Negative', 'Actual Positive'],
                        type: 'heatmap',
                        colorscale: [[0, '#1e293b'], [1, '#3b82f6']],
                        showscale: false,
                        text: selectedModel.metrics.confusion_matrix.map(row =>
                          row.map(val => val.toLocaleString())
                        ),
                        texttemplate: '%{text}',
                        textfont: { size: 16, color: '#fff' },
                        hovertemplate: '%{y} / %{x}: %{z}<extra></extra>'
                      }
                    ]}
                    layout={{
                      ...darkLayout,
                      xaxis: { ...darkLayout.xaxis, title: 'Predicted Label', tickfont: { size: 11, color: '#94a3b8' } },
                      yaxis: { ...darkLayout.yaxis, title: 'True Label', autorange: 'reversed', tickfont: { size: 11, color: '#94a3b8' } },
                      margin: { t: 10, r: 10, b: 70, l: 100 },
                      autosize: true
                    }}
                    useResizeHandler
                    style={{ width: '100%', maxWidth: '400px', height: '320px' }}
                    config={{ displayModeBar: false }}
                  />
                </div>

                {/* Confusion Matrix Interpretation */}
                <div className="space-y-3">
                  <h4 className="text-sm font-semibold text-white">Matrix Interpretation</h4>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="p-2 bg-green-500/10 border border-green-500/20 rounded">
                      <div className="font-medium text-green-400">True Negatives (TN)</div>
                      <div className="text-slate-400">{selectedModel.metrics.confusion_matrix[0][0].toLocaleString()}</div>
                      <div className="text-slate-500">Correctly predicted no injury</div>
                    </div>
                    <div className="p-2 bg-red-500/10 border border-red-500/20 rounded">
                      <div className="font-medium text-red-400">False Positives (FP)</div>
                      <div className="text-slate-400">{selectedModel.metrics.confusion_matrix[0][1].toLocaleString()}</div>
                      <div className="text-slate-500">False alarms</div>
                    </div>
                    <div className="p-2 bg-orange-500/10 border border-orange-500/20 rounded">
                      <div className="font-medium text-orange-400">False Negatives (FN)</div>
                      <div className="text-slate-400">{selectedModel.metrics.confusion_matrix[1][0].toLocaleString()}</div>
                      <div className="text-slate-500">Missed injuries</div>
                    </div>
                    <div className="p-2 bg-blue-500/10 border border-blue-500/20 rounded">
                      <div className="font-medium text-blue-400">True Positives (TP)</div>
                      <div className="text-slate-400">{selectedModel.metrics.confusion_matrix[1][1].toLocaleString()}</div>
                      <div className="text-slate-500">Correctly predicted injury</div>
                    </div>
                  </div>
                  <p className="text-xs text-slate-500 mt-2">
                    In injury prediction, minimizing False Negatives (missed injuries) is typically prioritized,
                    even at the cost of more False Positives (false alarms).
                  </p>
                </div>
              </div>
            </Card>
          )}

          {/* Reproducibility Panel */}
          <ReproducibilityPanel
            config={{
              model_type: selectedModel.model_type,
              n_estimators: selectedModel.config?.n_estimators,
              max_depth: selectedModel.config?.max_depth,
              learning_rate: selectedModel.config?.learning_rate,
              alpha: selectedModel.config?.alpha
            }}
            datasetId={selectedModel.dataset_id}
            modelId={selectedModel.id}
            splitId={selectedModel.split_id}
          />
        </>
      )}
    </div>
  )
}

export default ResultsPage
