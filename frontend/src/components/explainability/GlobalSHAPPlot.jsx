import React from 'react';
import Plot from 'react-plotly.js';

/**
 * Global SHAP Importance Plot
 *
 * Shows average feature importance across all predictions.
 */
const GlobalSHAPPlot = ({ globalExplanation, height = 400 }) => {
  if (!globalExplanation || !globalExplanation.mean_shap_values) {
    return (
      <div className="text-center text-slate-400 py-8">
        No global explanation data available
      </div>
    );
  }

  const { mean_shap_values, feature_names } = globalExplanation;

  // Show top 15 features
  const topN = 15;
  const topFeatures = feature_names.slice(0, topN);
  const topValues = mean_shap_values.slice(0, topN);

  // Reverse for horizontal bar chart (top feature at top)
  const reversedFeatures = [...topFeatures].reverse();
  const reversedValues = [...topValues].reverse();

  const data = [{
    type: 'bar',
    x: reversedValues,
    y: reversedFeatures.map(f => f.replace(/_/g, ' ')),
    orientation: 'h',
    marker: {
      color: reversedValues.map(v => {
        const max = Math.max(...reversedValues);
        const intensity = v / max;
        return `rgba(59, 130, 246, ${0.4 + intensity * 0.6})`;
      }),
      line: { color: '#3b82f6', width: 1 }
    },
    hovertemplate:
      '<b>%{y}</b><br>' +
      'Mean |SHAP|: %{x:.4f}<br>' +
      '<extra></extra>'
  }];

  const layout = {
    title: {
      text: 'Global Feature Importance',
      font: { size: 14, color: '#e2e8f0', family: 'Inter, sans-serif' }
    },
    xaxis: {
      title: { text: 'Mean |SHAP Value|', font: { color: '#94a3b8', size: 11 } },
      gridcolor: '#334155',
      tickfont: { color: '#94a3b8', size: 10 },
      zerolinecolor: '#475569'
    },
    yaxis: {
      automargin: true,
      tickfont: { color: '#e2e8f0', size: 10 }
    },
    height: height,
    margin: { l: 130, r: 30, t: 50, b: 50 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(30,41,59,0.5)',
    font: { family: 'Inter, sans-serif', size: 11, color: '#e2e8f0' },
    bargap: 0.3
  };

  const config = {
    responsive: true,
    displayModeBar: false
  };

  return (
    <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-4">
      <Plot
        data={data}
        layout={layout}
        config={config}
        className="w-full"
      />

      <div className="mt-4 p-3 bg-green-500/10 rounded-lg border border-green-500/20">
        <h4 className="text-sm font-medium text-green-300 mb-2">
          Global Importance
        </h4>
        <p className="text-xs text-slate-400">
          Shows which features matter most on average across all athletes.
          Higher values indicate stronger influence on injury risk predictions.
        </p>
      </div>
    </div>
  );
};

export default GlobalSHAPPlot;
