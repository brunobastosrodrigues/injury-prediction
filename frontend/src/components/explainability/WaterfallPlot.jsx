import React from 'react';
import Plot from 'react-plotly.js';

/**
 * SHAP Waterfall Plot - "Why am I at risk TODAY?"
 *
 * Shows how each feature contributes to the model's prediction for a specific instance.
 */
const WaterfallPlot = ({ explanation, height = 400 }) => {
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
    textfont: { color: '#e2e8f0', size: 10 },
    connector: {
      line: { color: '#475569', width: 1 }
    },
    increasing: { marker: { color: '#ef4444' } },
    decreasing: { marker: { color: '#22c55e' } },
    totals: { marker: { color: '#3b82f6' } }
  }];

  const layout = {
    title: {
      text: 'Feature Contributions to Risk',
      font: { size: 14, color: '#e2e8f0', family: 'Inter, sans-serif' }
    },
    xaxis: {
      title: { text: 'SHAP Value', font: { color: '#94a3b8', size: 11 } },
      gridcolor: '#334155',
      tickfont: { color: '#94a3b8', size: 10 },
      zerolinecolor: '#475569'
    },
    yaxis: {
      automargin: true,
      tickfont: { color: '#e2e8f0', size: 10 }
    },
    height: height,
    margin: { l: 140, r: 60, t: 50, b: 50 },
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

      <div className="mt-4 p-3 bg-blue-500/10 rounded-lg border border-blue-500/20">
        <h4 className="text-sm font-medium text-blue-300 mb-2">
          How to Read This Chart
        </h4>
        <div className="text-xs text-slate-400 flex flex-wrap gap-4">
          <span><span className="text-red-400">Red</span> = Increases risk</span>
          <span><span className="text-green-400">Green</span> = Decreases risk</span>
          <span><span className="text-blue-400">Blue</span> = Base/Final value</span>
        </div>
      </div>
    </div>
  );
};

export default WaterfallPlot;
