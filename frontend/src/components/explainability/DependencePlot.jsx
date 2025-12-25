import React from 'react';
import Plot from 'react-plotly.js';

/**
 * SHAP Dependence Plot - Reveals Feature Interactions
 *
 * Shows how a feature's impact varies based on another feature's value.
 * Key for understanding "Training-Injury Prevention Paradox":
 * - High load is OK if stress is low
 * - High load is RISKY if stress is high
 */
const DependencePlot = ({ interaction, height = 500 }) => {
  if (!interaction || !interaction.feature1_values) {
    return (
      <div className="text-center text-gray-500 py-8">
        No interaction data available
      </div>
    );
  }

  const {
    feature1_values,
    shap_values,
    interaction_values,
    feature1_name,
    feature2_name
  } = interaction;

  // Create scatter plot data
  const data = [{
    type: 'scatter',
    mode: 'markers',
    x: feature1_values,
    y: shap_values,
    marker: {
      size: 6,
      color: interaction_values,
      colorscale: 'RdYlGn_r',  // Red (high) to Green (low)
      showscale: true,
      colorbar: {
        title: {
          text: feature2_name.replace(/_/g, ' '),
          side: 'right'
        },
        thickness: 15,
        len: 0.7
      },
      line: {
        color: 'rgba(0,0,0,0.1)',
        width: 0.5
      }
    },
    hovertemplate:
      `<b>${feature1_name.replace(/_/g, ' ')}</b>: %{x:.2f}<br>` +
      '<b>SHAP Value</b>: %{y:.3f}<br>' +
      `<b>${feature2_name.replace(/_/g, ' ')}</b>: %{marker.color:.2f}<br>` +
      '<extra></extra>'
  }];

  const layout = {
    title: {
      text: `Impact of ${feature1_name.replace(/_/g, ' ')} (colored by ${feature2_name.replace(/_/g, ' ')})`,
      font: { size: 16, family: 'Inter, sans-serif' }
    },
    xaxis: {
      title: feature1_name.replace(/_/g, ' '),
      gridcolor: '#e5e7eb'
    },
    yaxis: {
      title: 'SHAP Value (Impact on Risk)',
      gridcolor: '#e5e7eb',
      zeroline: true,
      zerolinecolor: '#9ca3af',
      zerolinewidth: 2
    },
    height: height,
    margin: { l: 80, r: 150, t: 80, b: 80 },
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

      <div className="mt-4 p-4 bg-purple-50 rounded-lg border border-purple-200">
        <h4 className="text-sm font-semibold text-purple-900 mb-2">
          Understanding Interactions
        </h4>
        <div className="text-xs text-purple-800 space-y-2">
          <p>
            This chart reveals how <strong>{feature1_name.replace(/_/g, ' ')}</strong>'s
            impact depends on <strong>{feature2_name.replace(/_/g, ' ')}</strong>.
          </p>
          <ul className="space-y-1 ml-4">
            <li>• <span className="text-red-600">Red points</span>: High {feature2_name.replace(/_/g, ' ')}</li>
            <li>• <span className="text-green-600">Green points</span>: Low {feature2_name.replace(/_/g, ' ')}</li>
            <li>• If slopes differ by color, features interact</li>
            <li>• Flat line = no interaction with {feature2_name.replace(/_/g, ' ')}</li>
          </ul>
          <p className="mt-2 italic">
            Example: If high training load (x-axis) has positive SHAP when stress is high (red),
            but neutral SHAP when stress is low (green), it proves the "paradox."
          </p>
        </div>
      </div>
    </div>
  );
};

export default DependencePlot;
