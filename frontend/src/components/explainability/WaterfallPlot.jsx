import React from 'react';
import Plot from 'react-plotly.js';

/**
 * SHAP Waterfall Plot - "Why am I at risk TODAY?"
 *
 * Shows how each feature contributes to the model's prediction for a specific instance.
 * Base value + sum of SHAP values = final prediction
 */
const WaterfallPlot = ({ explanation, height = 500 }) => {
  if (!explanation || !explanation.shap_values) {
    return (
      <div className="text-center text-gray-500 py-8">
        No explanation data available
      </div>
    );
  }

  const {
    base_value,
    shap_values,
    feature_values,
    feature_names,
    prediction
  } = explanation;

  // Create waterfall data
  // Format: [base, feature1_contrib, feature2_contrib, ..., final]

  // Sort features by absolute SHAP value (already sorted from backend)
  const features = feature_names.map((name, idx) => ({
    name,
    shap_value: shap_values[idx],
    feature_value: feature_values[idx]
  }));

  // Build waterfall structure
  const labels = ['Base Value'];
  const measures = ['absolute'];
  const x = [base_value];
  const text = [`Base: ${base_value.toFixed(3)}`];

  features.forEach((feat, idx) => {
    const displayName = feat.name.replace(/_/g, ' ');
    const valueStr = typeof feat.feature_value === 'number'
      ? feat.feature_value.toFixed(2)
      : feat.feature_value;

    labels.push(`${displayName}<br>= ${valueStr}`);
    measures.push('relative');
    x.push(feat.shap_value);

    const direction = feat.shap_value > 0 ? '↑' : '↓';
    text.push(`${direction} ${Math.abs(feat.shap_value).toFixed(3)}`);
  });

  // Add final prediction
  labels.push('Prediction');
  measures.push('total');
  x.push(prediction);
  text.push(`Risk: ${(prediction * 100).toFixed(1)}%`);

  const data = [{
    type: 'waterfall',
    orientation: 'v',
    measure: measures,
    x: x,
    y: labels,
    text: text,
    textposition: 'outside',
    connector: {
      line: {
        color: 'rgb(63, 63, 63)',
        width: 2
      }
    },
    increasing: { marker: { color: '#ef4444' } },  // Red for increased risk
    decreasing: { marker: { color: '#10b981' } },  // Green for decreased risk
    totals: { marker: { color: '#3b82f6' } }       // Blue for base/prediction
  }];

  const layout = {
    title: {
      text: 'Feature Contributions to Risk Prediction',
      font: { size: 16, family: 'Inter, sans-serif' }
    },
    xaxis: {
      title: 'SHAP Value (Risk Contribution)',
      gridcolor: '#e5e7eb'
    },
    yaxis: {
      automargin: true
    },
    height: height,
    margin: { l: 150, r: 50, t: 80, b: 80 },
    paper_bgcolor: 'white',
    plot_bgcolor: '#f9fafb',
    font: { family: 'Inter, sans-serif', size: 12 }
  };

  const config = {
    responsive: true,
    displayModeBar: false
  };

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <Plot
        data={data}
        layout={layout}
        config={config}
        className="w-full"
      />

      <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <h4 className="text-sm font-semibold text-blue-900 mb-2">
          How to Read This Chart
        </h4>
        <ul className="text-xs text-blue-800 space-y-1">
          <li>• <span className="text-red-600">Red bars</span> increase injury risk</li>
          <li>• <span className="text-green-600">Green bars</span> decrease injury risk</li>
          <li>• Each bar shows the feature's impact on the prediction</li>
          <li>• Values flow from base prediction to final risk score</li>
        </ul>
      </div>
    </div>
  );
};

export default WaterfallPlot;
