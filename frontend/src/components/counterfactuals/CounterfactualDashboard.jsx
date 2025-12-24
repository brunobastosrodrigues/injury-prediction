import React, { useState, useEffect } from 'react';
import api from '../../api'; // Fixed import path
import Card from '../common/Card'; // Fixed import - Card doesn't export subcomponents

// Simple mocks for subcomponents if Card doesn't support them
const CardHeader = ({ children }) => <div className="mb-4 border-b pb-2">{children}</div>;
const CardContent = ({ children }) => <div>{children}</div>;
const CardTitle = ({ children }) => <h3 className="text-lg font-bold">{children}</h3>;
const CardDescription = ({ children }) => <p className="text-gray-500 text-sm">{children}</p>;

const CounterfactualDashboard = ({ modelId, splitId }) => {
  const [highRiskAthletes, setHighRiskAthletes] = useState([]);
  const [selectedAthlete, setSelectedAthlete] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (modelId && splitId) {
      fetchHighRiskAthletes();
    }
  }, [modelId, splitId]);

  const fetchHighRiskAthletes = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get('/counterfactuals/high-risk', {
        params: { model_id: modelId, split_id: splitId }
      });
      setHighRiskAthletes(response.data);
    } catch (err) {
      setError('Failed to fetch high risk athletes.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const generateRecommendations = async (index) => {
    try {
      setGenerating(true);
      setRecommendations(null);
      const response = await api.post('/counterfactuals/generate', {
        model_id: modelId,
        split_id: splitId,
        instance_index: index
      });
      setRecommendations(response.data);
    } catch (err) {
      console.error('Error generating recommendations:', err);
      setError('Failed to generate recommendations.');
    } finally {
      setGenerating(false);
    }
  };

  const handleSelectAthlete = (athlete) => {
    setSelectedAthlete(athlete);
    generateRecommendations(athlete.index);
  };

  const getRiskLabel = (probability) => {
    if (probability < 0.3) return 'Low';
    if (probability < 0.7) return 'Medium';
    return 'High';
  };

  if (!modelId) {
    return <div className="p-4 text-gray-500">Please select a trained model to view counterfactuals.</div>;
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Injury Prevention Assistant</CardTitle>
          <CardDescription>
            AI-driven recommendations to reduce injury risk.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-4">Loading high risk cases...</div>
          ) : error ? (
            <div className="text-red-500 py-4">{error}</div>
          ) : highRiskAthletes.length === 0 ? (
            <div className="text-green-500 py-4">No high risk athletes found in the test set.</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* List of High Risk Athletes */}
              <div className="border rounded-lg p-4 h-96 overflow-y-auto">
                <h3 className="font-semibold mb-3">High Risk Alerts ({highRiskAthletes.length})</h3>
                <div className="space-y-2">
                  {highRiskAthletes.map((athlete) => (
                    <div
                      key={athlete.index}
                      onClick={() => handleSelectAthlete(athlete)}
                      className={`p-3 rounded cursor-pointer transition-colors ${
                        selectedAthlete?.index === athlete.index
                          ? 'bg-blue-100 border-blue-500 border'
                          : 'bg-gray-50 hover:bg-gray-100 border border-transparent'
                      }`}
                    >
                      <div className="flex justify-between items-center">
                        <span className="font-medium">Case #{athlete.index}</span>
                        <span className="text-red-600 font-bold">
                          {(athlete.risk * 100).toFixed(1)}% Risk
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Recommendations Panel */}
              <div className="border rounded-lg p-4 h-96 overflow-y-auto bg-gray-50">
                <h3 className="font-semibold mb-3">Recommended Interventions</h3>

                {selectedAthlete ? (
                  generating ? (
                    <div className="flex items-center justify-center h-64">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    </div>
                  ) : recommendations ? (
                    <div className="space-y-4">
                      <div className="bg-white p-4 rounded shadow-sm">
                        <div className="text-sm text-gray-500">Current Risk</div>
                        <div className="text-2xl font-bold text-red-600">
                          {(recommendations.base_risk * 100).toFixed(1)}%
                        </div>
                      </div>

                      {recommendations.recommendations.length > 0 ? (
                        recommendations.recommendations.map((rec, i) => (
                          <div key={i} className="bg-white p-4 rounded shadow-sm border-l-4 border-green-500">
                            <div className="flex justify-between items-start">
                              <div>
                                <h4 className="font-bold text-green-700">{rec.type}</h4>
                                <p className="text-gray-700 text-sm mt-1">{rec.description}</p>
                              </div>
                              <div className="text-right">
                                <div className="text-xs text-gray-500">New Risk</div>
                                <div className="font-bold text-green-600">
                                  {(rec.new_risk * 100).toFixed(1)}% ({getRiskLabel(rec.new_risk)})
                                </div>
                                <div className="text-xs text-green-800 bg-green-100 px-2 py-0.5 rounded mt-1 inline-block">
                                  -{(rec.risk_reduction * 100).toFixed(1)}%
                                </div>
                              </div>
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="text-center py-8 text-gray-500">
                          No effective interventions found for this case.
                        </div>
                      )}
                    </div>
                  ) : null
                ) : (
                  <div className="flex items-center justify-center h-64 text-gray-400">
                    Select a case to view recommendations
                  </div>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default CounterfactualDashboard;
