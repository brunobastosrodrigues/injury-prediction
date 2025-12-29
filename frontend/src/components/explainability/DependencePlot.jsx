import React from 'react';
import Plot from 'react-plotly.js';
import { useTheme } from '../../context/ThemeContext';

/**
 * SHAP Dependence Plot - Reveals Feature Interactions
 *
 * Shows how a feature's impact varies based on another feature's value.
 */
const DependencePlot = ({ interaction, height = 400 }) => {
  const { isDark } = useTheme();
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
          font: { color: isDark ? '#e2e8f0' : '#1f2937', size: 11 }
        },
        tickfont: { color: isDark ? '#94a3b8' : '#4b5563', size: 10 },
        thickness: 12,
        len: 0.6
      },
      line: {
        color: isDark ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.1)',
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
      font: { size: 14, color: isDark ? '#e2e8f0' : '#1f2937', family: 'Inter, sans-serif' }
    },
    xaxis: {
      title: { text: feature1_name.replace(/_/g, ' '), font: { color: isDark ? '#94a3b8' : '#4b5563', size: 11 } },
      gridcolor: isDark ? '#334155' : '#e5e7eb',
      tickfont: { color: isDark ? '#94a3b8' : '#4b5563', size: 10 },
      zerolinecolor: isDark ? '#475569' : '#d1d5db'
    },
    yaxis: {
      title: { text: 'SHAP Value', font: { color: isDark ? '#94a3b8' : '#4b5563', size: 11 } },
      gridcolor: isDark ? '#334155' : '#e5e7eb',
      tickfont: { color: isDark ? '#94a3b8' : '#4b5563', size: 10 },
      zeroline: true,
      zerolinecolor: isDark ? '#64748b' : '#9ca3af',
      zerolinewidth: 1
    },
    height: height,
    margin: { l: 60, r: 100, t: 50, b: 50 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: isDark ? 'rgba(30,41,59,0.5)' : 'rgba(249,250,251,0.8)',
    font: { family: 'Inter, sans-serif', size: 11, color: isDark ? '#e2e8f0' : '#1f2937' }
  };

  const config = {
    responsive: true,
    displayModeBar: false
  };

  return (
    <div className={`${isDark ? 'bg-slate-800/50 border-slate-700' : 'bg-white border-gray-200'} rounded-xl border p-4`}>
      <Plot
        data={data}
        layout={layout}
        config={config}
        className="w-full"
      />

      <div className={`mt-4 p-3 ${isDark ? 'bg-purple-500/10 border-purple-500/20' : 'bg-purple-50 border-purple-200'} rounded-lg border`}>
        <h4 className={`text-sm font-medium ${isDark ? 'text-purple-300' : 'text-purple-700'} mb-2`}>
          Understanding Interactions
        </h4>
        <div className={`text-xs ${isDark ? 'text-slate-400' : 'text-gray-600'} space-y-1`}>
          <p>
            Shows how <span className={isDark ? 'text-purple-300' : 'text-purple-700'}>{feature1_name.replace(/_/g, ' ')}</span>'s
            impact depends on <span className={isDark ? 'text-purple-300' : 'text-purple-700'}>{feature2_name.replace(/_/g, ' ')}</span>.
          </p>
          <div className="flex gap-4 mt-2">
            <span><span className="text-red-500">Red</span> = High {feature2_name.replace(/_/g, ' ')}</span>
            <span><span className="text-green-500">Green</span> = Low {feature2_name.replace(/_/g, ' ')}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DependencePlot;
