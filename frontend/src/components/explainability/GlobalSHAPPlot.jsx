import React, { useState } from 'react';
import Plot from 'react-plotly.js';

/**
 * Global SHAP Importance Plot
 *
 * Shows average feature importance across all predictions.
 * In Federated Learning: Only aggregated values shared, not raw data.
 */
const GlobalSHAPPlot = ({ globalExplanation, height = 500, mode = 'bar' }) => {
  const [viewMode, setViewMode] = useState(mode);

  if (!globalExplanation || !globalExplanation.mean_shap_values) {
    return (
      <div className="text-center text-gray-500 py-8">
        No global explanation data available
      </div>
    );
  }

  const {
    mean_shap_values,
    feature_names,
    shap_values_matrix,
    feature_values_matrix
  } = globalExplanation;

  // Bar chart: Mean absolute SHAP values
  const renderBarChart = () => {
    // Show top 15 features
    const topN = 15;
    const topFeatures = feature_names.slice(0, topN);
    const topValues = mean_shap_values.slice(0, topN);

    const data = [{
      type: 'bar',
      x: topValues.reverse(),
      y: topFeatures.map(f => f.replace(/_/g, ' ')).reverse(),
      orientation: 'h',
      marker: {
        color: topValues.reverse(),
        colorscale: 'Blues',
        showscale: false
      },
      hovertemplate:
        '<b>%{y}</b><br>' +
        'Mean |SHAP|: %{x:.3f}<br>' +
        '<extra></extra>'
    }];

    const layout = {
      title: {
        text: 'Global Feature Importance (Mean Absolute SHAP)',
        font: { size: 16, family: 'Inter, sans-serif' }
      },
      xaxis: {
        title: 'Mean Absolute SHAP Value',
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

    return { data, layout };
  };

  // Beeswarm chart: Distribution of SHAP values
  const renderBeeswarm = () => {
    if (!shap_values_matrix || !feature_values_matrix) {
      return renderBarChart();  // Fallback to bar chart
    }

    // Create violin/box plot for each feature (top 10)
    const topN = 10;
    const traces = [];

    for (let i = 0; i < Math.min(topN, feature_names.length); i++) {
      const featureName = feature_names[i];
      const shapCol = shap_values_matrix.map(row => row[i]);
      const valueCol = feature_values_matrix.map(row => row[i]);

      traces.push({
        type: 'violin',
        x: shapCol,
        y: Array(shapCol.length).fill(featureName.replace(/_/g, ' ')),
        name: featureName.replace(/_/g, ' '),
        marker: {
          color: valueCol,
          colorscale: 'RdYlGn_r',
          showscale: i === 0,  // Only show colorbar for first trace
          colorbar: {
            title: 'Feature<br>Value',
            thickness: 15,
            len: 0.5
          }
        },
        orientation: 'h',
        side: 'positive',
        width: 0.5,
        points: 'all',
        pointpos: 0,
        jitter: 0.3,
        scalemode: 'width',
        meanline: { visible: true },
        hovertemplate:
          '<b>%{y}</b><br>' +
          'SHAP: %{x:.3f}<br>' +
          '<extra></extra>'
      });
    }

    const layout = {
      title: {
        text: 'SHAP Value Distribution (Beeswarm)',
        font: { size: 16, family: 'Inter, sans-serif' }
      },
      xaxis: {
        title: 'SHAP Value',
        gridcolor: '#e5e7eb',
        zeroline: true,
        zerolinecolor: '#9ca3af',
        zerolinewidth: 2
      },
      yaxis: {
        automargin: true
      },
      height: height,
      margin: { l: 150, r: 150, t: 80, b: 80 },
      paper_bgcolor: 'white',
      plot_bgcolor: '#f9fafb',
      font: { family: 'Inter, sans-serif', size: 12 },
      showlegend: false
    };

    return { data: traces, layout };
  };

  const { data, layout } = viewMode === 'bar' ? renderBarChart() : renderBeeswarm();

  const config = {
    responsive: true,
    displayModeBar: false
  };

  return (
    <div className="bg-white rounded-lg shadow p-4">
      {/* View mode toggle */}
      <div className="flex justify-end mb-4">
        <div className="inline-flex rounded-md shadow-sm" role="group">
          <button
            type="button"
            onClick={() => setViewMode('bar')}
            className={`px-4 py-2 text-sm font-medium border ${
              viewMode === 'bar'
                ? 'bg-blue-600 text-white border-blue-600'
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
            } rounded-l-lg`}
          >
            Bar Chart
          </button>
          <button
            type="button"
            onClick={() => setViewMode('beeswarm')}
            className={`px-4 py-2 text-sm font-medium border-t border-b border-r ${
              viewMode === 'beeswarm'
                ? 'bg-blue-600 text-white border-blue-600'
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
            } rounded-r-lg`}
            disabled={!shap_values_matrix}
          >
            Beeswarm
          </button>
        </div>
      </div>

      <Plot
        data={data}
        layout={layout}
        config={config}
        className="w-full"
      />

      <div className="mt-4 p-4 bg-green-50 rounded-lg border border-green-200">
        <h4 className="text-sm font-semibold text-green-900 mb-2">
          Global Importance Explained
        </h4>
        <div className="text-xs text-green-800 space-y-1">
          <p>
            <strong>Bar Chart:</strong> Shows which features matter most on average across all athletes.
          </p>
          <p>
            <strong>Beeswarm:</strong> Shows the distribution of impacts (how consistently a feature matters).
          </p>
          <p className="mt-2 italic">
            In Federated Learning, only these aggregated values are shared with the server—
            individual athlete data stays private.
          </p>
        </div>
      </div>
    </div>
  );
};

export default GlobalSHAPPlot;
