import React, { useState, useEffect } from 'react';
import { usePipeline } from '../context/PipelineContext';
import api from '../api';
import Card from '../components/common/Card';
import {
  WaterfallPlot,
  DependencePlot,
  GlobalSHAPPlot,
  CounterfactualScenarios,
  RecommendationsPanel
} from '../components/explainability';
import {
  SparklesIcon,
  GlobeAltIcon,
  ArrowsRightLeftIcon,
  LightBulbIcon,
  BeakerIcon
} from '@heroicons/react/24/outline';

/**
 * Model Interpretability Page
 *
 * Comprehensive XAI dashboard implementing:
 * 1. SHAP Waterfall (Local Explanation)
 * 2. SHAP Dependence (Interaction Analysis)
 * 3. Global SHAP (Feature Importance)
 * 4. Counterfactuals (What-If Scenarios)
 * 5. Recommendations (Actionable Insights)
 *
 * Designed for Federated Learning privacy constraints.
 */
const ModelInterpretability = () => {
  const { models, refreshModels } = usePipeline();
  const [activeTab, setActiveTab] = useState('local');
  const [selectedModelId, setSelectedModelId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [initialLoading, setInitialLoading] = useState(true);

  // Explanations state
  const [localExplanation, setLocalExplanation] = useState(null);
  const [globalExplanation, setGlobalExplanation] = useState(null);
  const [interactionExplanation, setInteractionExplanation] = useState(null);
  const [counterfactuals, setCounterfactuals] = useState(null);
  const [recommendations, setRecommendations] = useState(null);

  // Example athlete data (for demo - in real FL, this would be on client device)
  const [athleteData, setAthleteData] = useState(null);

  // Features for interaction analysis
  const [feature1, setFeature1] = useState('stress');
  const [feature2, setFeature2] = useState('acute_load');

  // Load models on mount
  useEffect(() => {
    const loadModels = async () => {
      setInitialLoading(true);
      await refreshModels();
      setInitialLoading(false);
    };
    loadModels();
  }, [refreshModels]);

  // Set default model when models load
  useEffect(() => {
    if (models.length > 0 && !selectedModelId) {
      setSelectedModelId(models[0].model_id);
    }
  }, [models, selectedModelId]);

  // Get selected model details
  const selectedModel = models.find(m => m.model_id === selectedModelId);

  // Load sample athlete data for demo
  const loadSampleAthleteData = async () => {
    if (!selectedModel) return;

    try {
      setLoading(true);
      setError(null);

      // Fetch a sample from the test set using the model's split_id
      const response = await api.get(`/explainability/sample/${selectedModelId}`);

      if (response.data && response.data.sample) {
        setAthleteData(response.data.sample);
      }
    } catch (err) {
      console.error('Error loading sample data:', err);
      setError('Failed to load sample athlete data. Make sure a model is trained.');
    } finally {
      setLoading(false);
    }
  };

  // Load local explanation (Waterfall)
  const loadLocalExplanation = async () => {
    if (!selectedModelId || !athleteData) return;

    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/explainability/explain/prediction', {
        model_id: selectedModelId,
        athlete_data: athleteData,
        prediction_index: 0,
        max_display: 10
      });

      setLocalExplanation(response.data);
    } catch (err) {
      console.error('Error loading local explanation:', err);
      setError('Failed to generate local explanation');
    } finally {
      setLoading(false);
    }
  };

  // Load global explanation
  const loadGlobalExplanation = async () => {
    if (!selectedModelId) return;

    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/explainability/explain/global', {
        model_id: selectedModelId,
        sample_size: 500
      });

      setGlobalExplanation(response.data);
    } catch (err) {
      console.error('Error loading global explanation:', err);
      setError('Failed to generate global explanation');
    } finally {
      setLoading(false);
    }
  };

  // Load interaction explanation
  const loadInteractionExplanation = async () => {
    if (!selectedModelId) return;

    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/explainability/explain/interactions', {
        model_id: selectedModelId,
        feature1: feature1,
        feature2: feature2 || null,
        sample_size: 500
      });

      setInteractionExplanation(response.data);
    } catch (err) {
      console.error('Error loading interaction explanation:', err);
      setError('Failed to generate interaction explanation');
    } finally {
      setLoading(false);
    }
  };

  // Load counterfactuals
  const loadCounterfactuals = async () => {
    if (!selectedModelId || !athleteData) return;

    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/explainability/counterfactuals', {
        model_id: selectedModelId,
        athlete_data: athleteData,
        desired_class: 0,
        total_cfs: 3
      });

      setCounterfactuals(response.data);
    } catch (err) {
      console.error('Error loading counterfactuals:', err);
      setError('Failed to generate counterfactuals');
    } finally {
      setLoading(false);
    }
  };

  // Load recommendations
  const loadRecommendations = async () => {
    if (!selectedModelId || !athleteData) return;

    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/explainability/recommendations', {
        model_id: selectedModelId,
        athlete_data: athleteData,
        risk_threshold: 0.3
      });

      setRecommendations(response.data);
    } catch (err) {
      console.error('Error loading recommendations:', err);
      setError('Failed to generate recommendations');
    } finally {
      setLoading(false);
    }
  };

  // Load explanations when tab changes
  useEffect(() => {
    if (!selectedModelId) return;

    if (activeTab === 'local' && !localExplanation && athleteData) {
      loadLocalExplanation();
    } else if (activeTab === 'global' && !globalExplanation) {
      loadGlobalExplanation();
    } else if (activeTab === 'interactions' && !interactionExplanation) {
      loadInteractionExplanation();
    } else if (activeTab === 'counterfactuals' && !counterfactuals && athleteData) {
      loadCounterfactuals();
    } else if (activeTab === 'recommendations' && !recommendations && athleteData) {
      loadRecommendations();
    }
  }, [activeTab, selectedModelId, athleteData]);

  // Load sample data when model changes
  useEffect(() => {
    if (selectedModelId) {
      // Clear previous explanations when model changes
      setLocalExplanation(null);
      setGlobalExplanation(null);
      setInteractionExplanation(null);
      setCounterfactuals(null);
      setRecommendations(null);
      setAthleteData(null);
      loadSampleAthleteData();
    }
  }, [selectedModelId]);

  const tabs = [
    { id: 'local', name: 'Local (Waterfall)', icon: SparklesIcon },
    { id: 'global', name: 'Global Importance', icon: GlobeAltIcon },
    { id: 'interactions', name: 'Interactions', icon: ArrowsRightLeftIcon },
    { id: 'counterfactuals', name: 'What-If', icon: BeakerIcon },
    { id: 'recommendations', name: 'Recommendations', icon: LightBulbIcon }
  ];

  return (
    <div className="h-full">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2">
            Model Interpretability (XAI)
          </h1>
          <p className="text-sm sm:text-base text-slate-400">
            Understand model predictions using SHAP, interaction analysis, and counterfactuals.
          </p>
        </div>

        {/* Controls */}
        <div className="mb-6 bg-slate-800/50 rounded-xl border border-slate-700 p-4">
          {initialLoading ? (
            <div className="text-center py-4 text-slate-400">Loading trained models...</div>
          ) : models.length === 0 ? (
            <div className="text-center py-4">
              <p className="text-slate-400 mb-2">No trained models found.</p>
              <p className="text-sm text-slate-500">
                Please train a model first using the Training page.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Model Selector */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Trained Model
                </label>
                <select
                  value={selectedModelId}
                  onChange={(e) => setSelectedModelId(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Select a trained model...</option>
                  {models.map(model => (
                    <option key={model.model_id} value={model.model_id}>
                      {model.model_name || model.model_type} - {new Date(model.created_at).toLocaleDateString()}
                      {model.metrics?.roc_auc ? ` (AUC: ${model.metrics.roc_auc.toFixed(3)})` : ''}
                    </option>
                  ))}
                </select>
              </div>

              {/* Reload Button */}
              <div className="flex items-end">
                <button
                  onClick={() => {
                    setLocalExplanation(null);
                    setGlobalExplanation(null);
                    setInteractionExplanation(null);
                    setCounterfactuals(null);
                    setRecommendations(null);
                    loadSampleAthleteData();
                  }}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 transition-colors disabled:bg-slate-700 disabled:text-slate-500"
                  disabled={!selectedModelId || loading}
                >
                  {loading ? 'Loading...' : 'Load Explanations'}
                </button>
              </div>
            </div>
          )}

          {/* Model Info */}
          {selectedModel && (
            <div className="mt-4 pt-4 border-t border-slate-700">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-slate-500">Type:</span>{' '}
                  <span className="font-medium text-slate-300">{selectedModel.model_type}</span>
                </div>
                <div>
                  <span className="text-slate-500">AUC:</span>{' '}
                  <span className="font-medium text-green-400">{selectedModel.metrics?.roc_auc?.toFixed(3) || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-slate-500">Precision:</span>{' '}
                  <span className="font-medium text-slate-300">{selectedModel.metrics?.precision?.toFixed(3) || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-slate-500">Recall:</span>{' '}
                  <span className="font-medium text-slate-300">{selectedModel.metrics?.recall?.toFixed(3) || 'N/A'}</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400">
            {error}
          </div>
        )}

        {/* Tabs */}
        <div className="mb-6 overflow-x-auto">
          <div className="flex space-x-1 border-b border-slate-700 min-w-max">
            {tabs.map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors whitespace-nowrap ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-400 font-semibold'
                      : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-600'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span className="text-sm">{tab.name}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Tab Content */}
        <div className="space-y-6">
          {activeTab === 'local' && (
            <div>
              <h2 className="text-lg font-semibold text-white mb-4">
                Local Explanation - Why this prediction?
              </h2>
              {loading && <p className="text-slate-400">Loading explanation...</p>}
              {!loading && localExplanation && (
                <WaterfallPlot explanation={localExplanation} height={450} />
              )}
              {!loading && !localExplanation && athleteData && (
                <p className="text-slate-500">Click "Load Explanations" to generate</p>
              )}
            </div>
          )}

          {activeTab === 'global' && (
            <div>
              <h2 className="text-lg font-semibold text-white mb-4">
                Global Feature Importance
              </h2>
              {loading && <p className="text-slate-400">Loading explanation...</p>}
              {!loading && globalExplanation && (
                <GlobalSHAPPlot globalExplanation={globalExplanation} height={450} />
              )}
              {!loading && !globalExplanation && (
                <p className="text-slate-500">Click "Load Explanations" to generate</p>
              )}
            </div>
          )}

          {activeTab === 'interactions' && (
            <div>
              <h2 className="text-lg font-semibold text-white mb-4">
                Interaction Analysis
              </h2>

              {/* Feature Selectors */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Primary Feature
                  </label>
                  <input
                    type="text"
                    value={feature1}
                    onChange={(e) => setFeature1(e.target.value)}
                    placeholder="e.g., stress"
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Interaction Feature (optional)
                  </label>
                  <input
                    type="text"
                    value={feature2}
                    onChange={(e) => setFeature2(e.target.value)}
                    placeholder="Auto-detect if empty"
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>

              <button
                onClick={loadInteractionExplanation}
                className="mb-4 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-500 disabled:bg-slate-700 disabled:text-slate-500"
                disabled={loading || !selectedModelId}
              >
                {loading ? 'Loading...' : 'Analyze Interaction'}
              </button>

              {!loading && interactionExplanation && (
                <DependencePlot interaction={interactionExplanation} height={400} />
              )}
              {!loading && !interactionExplanation && (
                <p className="text-slate-500">Enter a feature name and click "Analyze Interaction"</p>
              )}
            </div>
          )}

          {activeTab === 'counterfactuals' && (
            <div>
              <h2 className="text-lg font-semibold text-white mb-4">
                What-If Scenarios
              </h2>
              {loading && <p className="text-slate-400">Generating scenarios...</p>}
              {!loading && counterfactuals && (
                <CounterfactualScenarios counterfactuals={counterfactuals} />
              )}
              {!loading && !counterfactuals && athleteData && (
                <p className="text-slate-500">Click "Load Explanations" to generate scenarios</p>
              )}
            </div>
          )}

          {activeTab === 'recommendations' && (
            <div>
              <h2 className="text-lg font-semibold text-white mb-4">
                Actionable Recommendations
              </h2>
              {loading && <p className="text-slate-400">Generating recommendations...</p>}
              {!loading && recommendations && (
                <RecommendationsPanel recommendations={recommendations} />
              )}
              {!loading && !recommendations && athleteData && (
                <p className="text-slate-500">Click "Load Explanations" to generate recommendations</p>
              )}
            </div>
          )}
        </div>

        {/* Privacy Note */}
        <div className="mt-6 bg-purple-500/10 border border-purple-500/20 rounded-xl p-4">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <div>
              <h4 className="text-sm font-medium text-purple-300 mb-1">
                Privacy-Preserving Federated XAI
              </h4>
              <p className="text-xs text-slate-400">
                In Federated Learning: Local explanations stay on-device, only aggregated insights are shared.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModelInterpretability;
