import React from 'react';
import Plot from 'react-plotly.js';

/**
 * SHAP Dependence Plot - Reveals Feature Interactions
 *
 * Shows how a feature's impact varies based on another feature's value.
 */
const DependencePlot = ({ interaction, height = 400 }) => {
  if (!interaction || !interaction.feature1_values) {
    return (
      <div className="text-center text-slate-400 py-8">
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

  const data = [{
    type: 'scatter',
    mode: 'markers',
    x: feature1_values,
    y: shap_values,
    marker: {
      size: 8,
      color: interaction_values,
      colorscale: 'RdYlGn_r',
      showscale: true,
      colorbar: {
        title: {
          text: feature2_name.replace(/_/g, ' '),
          font: { color: '#e2e8f0', size: 11 }
        },
        tickfont: { color: '#94a3b8', size: 10 },
        thickness: 12,
        len: 0.6
      },
      line: {
        color: 'rgba(255,255,255,0.2)',
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
      text: `${feature1_name.replace(/_/g, ' ')} vs SHAP Impact`,
      font: { size: 14, color: '#e2e8f0', family: 'Inter, sans-serif' }
    },
    xaxis: {
      title: { text: feature1_name.replace(/_/g, ' '), font: { color: '#94a3b8', size: 11 } },
      gridcolor: '#334155',
      tickfont: { color: '#94a3b8', size: 10 },
      zerolinecolor: '#475569'
    },
    yaxis: {
      title: { text: 'SHAP Value', font: { color: '#94a3b8', size: 11 } },
      gridcolor: '#334155',
      tickfont: { color: '#94a3b8', size: 10 },
      zeroline: true,
      zerolinecolor: '#64748b',
      zerolinewidth: 1
    },
    height: height,
    margin: { l: 60, r: 100, t: 50, b: 50 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(30,41,59,0.5)',
    font: { family: 'Inter, sans-serif', size: 11, color: '#e2e8f0' }
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

      <div className="mt-4 p-3 bg-purple-500/10 rounded-lg border border-purple-500/20">
        <h4 className="text-sm font-medium text-purple-300 mb-2">
          Understanding Interactions
        </h4>
        <div className="text-xs text-slate-400 space-y-1">
          <p>
            Shows how <span className="text-purple-300">{feature1_name.replace(/_/g, ' ')}</span>'s
            impact depends on <span className="text-purple-300">{feature2_name.replace(/_/g, ' ')}</span>.
          </p>
          <div className="flex gap-4 mt-2">
            <span><span className="text-red-400">Red</span> = High {feature2_name.replace(/_/g, ' ')}</span>
            <span><span className="text-green-400">Green</span> = Low {feature2_name.replace(/_/g, ' ')}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DependencePlot;
