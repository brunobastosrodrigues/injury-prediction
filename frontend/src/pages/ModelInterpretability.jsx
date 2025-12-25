import React, { useState, useEffect } from 'react';
import { usePipeline } from '../context/PipelineContext';
import api from '../api';
import Layout from '../components/common/Layout';
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
  const { datasets } = usePipeline();
  const [activeTab, setActiveTab] = useState('local');
  const [selectedDataset, setSelectedDataset] = useState('');
  const [selectedModel, setSelectedModel] = useState('xgboost');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Explanations state
  const [localExplanation, setLocalExplanation] = useState(null);
  const [globalExplanation, setGlobalExplanation] = useState(null);
  const [interactionExplanation, setInteractionExplanation] = useState(null);
  const [counterfactuals, setCounterfactuals] = useState(null);
  const [recommendations, setRecommendations] = useState(null);

  // Example athlete data (for demo - in real FL, this would be on client device)
  const [athleteData, setAthleteData] = useState(null);

  // Features for interaction analysis
  const [feature1, setFeature1] = useState('Acute_TSS');
  const [feature2, setFeature2] = useState('Daily_Stress');

  // Available datasets from pipeline
  const availableDatasets = datasets
    .filter(d => d.status === 'completed')
    .map(d => ({ id: d.id, name: d.id }));

  // Set default dataset
  useEffect(() => {
    if (availableDatasets.length > 0 && !selectedDataset) {
      setSelectedDataset(availableDatasets[0].id);
    }
  }, [availableDatasets]);

  // Load sample athlete data for demo
  const loadSampleAthleteData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch a sample from the test set
      const response = await api.get(`/api/analytics/dataset/${selectedDataset}`);

      if (response.data && response.data.test_data) {
        // Get the last row (most recent)
        const lastRow = response.data.test_data[response.data.test_data.length - 1];
        setAthleteData(lastRow);
      }
    } catch (err) {
      console.error('Error loading sample data:', err);
      setError('Failed to load sample athlete data');
    } finally {
      setLoading(false);
    }
  };

  // Load local explanation (Waterfall)
  const loadLocalExplanation = async () => {
    if (!selectedDataset || !athleteData) return;

    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/explainability/explain/prediction', {
        dataset_id: selectedDataset,
        model_name: selectedModel,
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
    if (!selectedDataset) return;

    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/explainability/explain/global', {
        dataset_id: selectedDataset,
        model_name: selectedModel,
        sample_size: 1000
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
    if (!selectedDataset) return;

    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/explainability/explain/interactions', {
        dataset_id: selectedDataset,
        model_name: selectedModel,
        feature1: feature1,
        feature2: feature2 || null,
        sample_size: 1000
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
    if (!selectedDataset || !athleteData) return;

    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/explainability/counterfactuals', {
        dataset_id: selectedDataset,
        model_name: selectedModel,
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
    if (!selectedDataset || !athleteData) return;

    try {
      setLoading(true);
      setError(null);

      const response = await api.post('/api/explainability/recommendations', {
        dataset_id: selectedDataset,
        model_name: selectedModel,
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
    if (!selectedDataset) return;

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
  }, [activeTab, selectedDataset, athleteData]);

  // Load sample data when dataset changes
  useEffect(() => {
    if (selectedDataset) {
      loadSampleAthleteData();
    }
  }, [selectedDataset]);

  const tabs = [
    { id: 'local', name: 'Local (Waterfall)', icon: SparklesIcon },
    { id: 'global', name: 'Global Importance', icon: GlobeAltIcon },
    { id: 'interactions', name: 'Interactions', icon: ArrowsRightLeftIcon },
    { id: 'counterfactuals', name: 'What-If', icon: BeakerIcon },
    { id: 'recommendations', name: 'Recommendations', icon: LightBulbIcon }
  ];

  return (
    <Layout>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
            Model Interpretability (XAI)
          </h1>
          <p className="text-sm sm:text-base text-gray-600">
            Understand model predictions using SHAP, interaction analysis, and counterfactuals.
            Privacy-preserving design for Federated Learning.
          </p>
        </div>

        {/* Controls */}
        <Card className="mb-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* Dataset Selector */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Dataset
              </label>
              <select
                value={selectedDataset}
                onChange={(e) => setSelectedDataset(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select dataset...</option>
                {availableDatasets.map(ds => (
                  <option key={ds.id} value={ds.id}>
                    {ds.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Model Selector */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Model
              </label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              >
                <option value="xgboost">XGBoost</option>
                <option value="random_forest">Random Forest</option>
                <option value="lasso">Lasso</option>
              </select>
            </div>

            {/* Reload Button */}
            <div className="flex items-end">
              <button
                onClick={() => {
                  // Clear all explanations
                  setLocalExplanation(null);
                  setGlobalExplanation(null);
                  setInteractionExplanation(null);
                  setCounterfactuals(null);
                  setRecommendations(null);
                  loadSampleAthleteData();
                }}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                disabled={!selectedDataset || loading}
              >
                {loading ? 'Loading...' : 'Reload Data'}
              </button>
            </div>
          </div>
        </Card>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {/* Tabs */}
        <div className="mb-6 overflow-x-auto">
          <div className="flex space-x-2 border-b border-gray-200 min-w-max">
            {tabs.map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors whitespace-nowrap ${
                    activeTab === tab.id
                      ? 'border-blue-600 text-blue-600 font-semibold'
                      : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
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
            <Card>
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                Local Explanation - "Why am I at risk TODAY?"
              </h2>
              {loading && <p className="text-gray-600">Loading explanation...</p>}
              {!loading && localExplanation && (
                <WaterfallPlot explanation={localExplanation} height={600} />
              )}
              {!loading && !localExplanation && athleteData && (
                <p className="text-gray-600">Click "Reload Data" to generate explanation</p>
              )}
            </Card>
          )}

          {activeTab === 'global' && (
            <Card>
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                Global Feature Importance
              </h2>
              {loading && <p className="text-gray-600">Loading explanation...</p>}
              {!loading && globalExplanation && (
                <GlobalSHAPPlot globalExplanation={globalExplanation} height={600} />
              )}
              {!loading && !globalExplanation && (
                <p className="text-gray-600">Click "Reload Data" to generate explanation</p>
              )}
            </Card>
          )}

          {activeTab === 'interactions' && (
            <Card>
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                Interaction Analysis - "Training-Injury Prevention Paradox"
              </h2>

              {/* Feature Selectors */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Primary Feature
                  </label>
                  <input
                    type="text"
                    value={feature1}
                    onChange={(e) => setFeature1(e.target.value)}
                    placeholder="e.g., Acute_TSS"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Interaction Feature (optional)
                  </label>
                  <input
                    type="text"
                    value={feature2}
                    onChange={(e) => setFeature2(e.target.value)}
                    placeholder="e.g., Daily_Stress (auto-detect if empty)"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
              </div>

              <button
                onClick={loadInteractionExplanation}
                className="mb-4 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
                disabled={loading || !selectedDataset}
              >
                {loading ? 'Loading...' : 'Analyze Interaction'}
              </button>

              {!loading && interactionExplanation && (
                <DependencePlot interaction={interactionExplanation} height={600} />
              )}
            </Card>
          )}

          {activeTab === 'counterfactuals' && (
            <Card>
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                What-If Scenarios - "What should I change?"
              </h2>
              {loading && <p className="text-gray-600">Generating scenarios...</p>}
              {!loading && counterfactuals && (
                <CounterfactualScenarios counterfactuals={counterfactuals} />
              )}
              {!loading && !counterfactuals && athleteData && (
                <p className="text-gray-600">Click "Reload Data" to generate scenarios</p>
              )}
            </Card>
          )}

          {activeTab === 'recommendations' && (
            <Card>
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                Actionable Recommendations
              </h2>
              {loading && <p className="text-gray-600">Generating recommendations...</p>}
              {!loading && recommendations && (
                <RecommendationsPanel recommendations={recommendations} />
              )}
              {!loading && !recommendations && athleteData && (
                <p className="text-gray-600">Click "Reload Data" to generate recommendations</p>
              )}
            </Card>
          )}
        </div>

        {/* Privacy Note */}
        <Card className="mt-6 bg-gradient-to-r from-purple-50 to-blue-50 border-2 border-purple-200">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-purple-900 mb-1">
                Privacy-Preserving Federated XAI
              </h4>
              <p className="text-xs text-purple-800">
                In a real Federated Learning deployment:
              </p>
              <ul className="text-xs text-purple-800 mt-2 space-y-1 ml-4">
                <li>• <strong>Local Explanations</strong> (Waterfall, What-If) stay on your device</li>
                <li>• <strong>Global Insights</strong> use only aggregated SHAP values (no raw data shared)</li>
                <li>• The server never sees your training data or personal metrics</li>
                <li>• You maintain full control over your data while benefiting from collective intelligence</li>
              </ul>
            </div>
          </div>
        </Card>
      </div>
    </Layout>
  );
};

export default ModelInterpretability;
