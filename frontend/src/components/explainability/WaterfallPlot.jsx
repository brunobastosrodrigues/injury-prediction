import React from 'react';
import Plot from 'react-plotly.js';
import { useTheme } from '../../context/ThemeContext';

/**
 * SHAP Waterfall Plot - "Why am I at risk TODAY?"
 *
 * Shows how each feature contributes to the model's prediction for a specific instance.
 */
const WaterfallPlot = ({ explanation, height = 400 }) => {
  const { isDark } = useTheme();
  if (!explanation || !explanation.shap_values) {
    return (
      <div className="text-center text-slate-400 py-8">
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

  // Build waterfall data
  const features = feature_names.map((name, idx) => ({
    name,
    shap_value: shap_values[idx],
    feature_value: feature_values[idx]
  }));

  const labels = ['Base'];
  const measures = ['absolute'];
  const x = [base_value];
  const text = [`${base_value.toFixed(3)}`];

  features.forEach((feat) => {
    const displayName = feat.name.replace(/_/g, ' ');
    const valueStr = typeof feat.feature_value === 'number'
      ? feat.feature_value.toFixed(1)
      : feat.feature_value;

    labels.push(`${displayName} (${valueStr})`);
    measures.push('relative');
    x.push(feat.shap_value);

    const sign = feat.shap_value > 0 ? '+' : '';
    text.push(`${sign}${feat.shap_value.toFixed(3)}`);
  });

  labels.push('Final Risk');
  measures.push('total');
  x.push(prediction);
  text.push(`${(prediction * 100).toFixed(1)}%`);

  const data = [{
    type: 'waterfall',
    orientation: 'h',
    measure: measures,
    y: labels,
    x: x,
    text: text,
    textposition: 'outside',
    textfont: { color: isDark ? '#e2e8f0' : '#1f2937', size: 10 },
    connector: {
      line: { color: isDark ? '#475569' : '#d1d5db', width: 1 }
    },
    increasing: { marker: { color: '#ef4444' } },
    decreasing: { marker: { color: '#22c55e' } },
    totals: { marker: { color: '#3b82f6' } }
  }];

  const layout = {
    title: {
      text: 'Feature Contributions to Risk',
      font: { size: 14, color: isDark ? '#e2e8f0' : '#1f2937', family: 'Inter, sans-serif' }
    },
    xaxis: {
      title: { text: 'SHAP Value', font: { color: isDark ? '#94a3b8' : '#4b5563', size: 11 } },
      gridcolor: isDark ? '#334155' : '#e5e7eb',
      tickfont: { color: isDark ? '#94a3b8' : '#4b5563', size: 10 },
      zerolinecolor: isDark ? '#475569' : '#d1d5db'
    },
    yaxis: {
      automargin: true,
      tickfont: { color: isDark ? '#e2e8f0' : '#1f2937', size: 10 }
    },
    height: height,
    margin: { l: 140, r: 60, t: 50, b: 50 },
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

      <div className={`mt-4 p-3 ${isDark ? 'bg-blue-500/10 border-blue-500/20' : 'bg-blue-50 border-blue-200'} rounded-lg border`}>
        <h4 className={`text-sm font-medium ${isDark ? 'text-blue-300' : 'text-blue-700'} mb-2`}>
          How to Read This Chart
        </h4>
        <div className={`text-xs ${isDark ? 'text-slate-400' : 'text-gray-600'} flex flex-wrap gap-4`}>
          <span><span className="text-red-500">Red</span> = Increases risk</span>
          <span><span className="text-green-500">Green</span> = Decreases risk</span>
          <span><span className="text-blue-500">Blue</span> = Base/Final value</span>
        </div>
      </div>
    </div>
  );
};

export default WaterfallPlot;
