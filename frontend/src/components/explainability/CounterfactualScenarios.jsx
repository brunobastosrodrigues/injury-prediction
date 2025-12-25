import React from 'react';
import { ArrowRightIcon, CheckCircleIcon } from '@heroicons/react/24/outline';

/**
 * Counterfactual Scenarios - "What should I change?"
 *
 * Displays actionable what-if scenarios.
 */
const CounterfactualScenarios = ({ counterfactuals, className = '' }) => {
  if (!counterfactuals || !counterfactuals.counterfactuals || counterfactuals.counterfactuals.length === 0) {
    return (
      <div className="text-center text-slate-400 py-8">
        No counterfactual scenarios available
      </div>
    );
  }

  const { original_prediction, counterfactuals: scenarios } = counterfactuals;

  const formatFeature = (name) => {
    return name
      .replace(/_/g, ' ')
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const getChangeInfo = (change) => {
    const direction = change.change > 0 ? 'increase' : 'decrease';
    const color = change.change > 0 ? 'text-red-400' : 'text-green-400';
    const arrow = change.change > 0 ? '↑' : '↓';
    return { direction, color, arrow };
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Original Risk */}
      <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-red-300">
            Current Risk Level
          </span>
          <span className="text-2xl font-bold text-red-400">
            {(original_prediction * 100).toFixed(1)}%
          </span>
        </div>
      </div>

      {/* Scenarios */}
      <div className="space-y-3">
        {scenarios.map((scenario, idx) => {
          const riskReduction = scenario.risk_reduction * 100;
          const newRisk = scenario.predicted_risk * 100;

          return (
            <div
              key={idx}
              className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 hover:border-blue-500/50 transition-colors"
            >
              {/* Scenario Header */}
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h4 className="text-sm font-semibold text-slate-200 flex items-center">
                    <CheckCircleIcon className="w-5 h-5 text-green-400 mr-2" />
                    Scenario {idx + 1}
                  </h4>
                  <p className="text-xs text-slate-500 mt-1">
                    {Object.keys(scenario.changes).length} change{Object.keys(scenario.changes).length > 1 ? 's' : ''} recommended
                  </p>
                </div>

                <div className="text-right">
                  <div className="text-xs text-slate-500">New Risk</div>
                  <div className="text-xl font-bold text-green-400">
                    {newRisk.toFixed(1)}%
                  </div>
                  <div className="text-xs text-green-500">
                    {riskReduction > 0 ? '↓' : '↑'} {Math.abs(riskReduction).toFixed(1)}%
                  </div>
                </div>
              </div>

              {/* Changes List */}
              <div className="space-y-2">
                {Object.entries(scenario.changes).map(([feature, change]) => {
                  const { direction, color, arrow } = getChangeInfo(change);

                  return (
                    <div
                      key={feature}
                      className="flex items-center justify-between p-2 bg-slate-900/50 rounded-lg"
                    >
                      <div className="flex-1">
                        <div className="text-sm font-medium text-slate-300">
                          {formatFeature(feature)}
                        </div>
                        <div className="text-xs text-slate-500 mt-1">
                          {direction.charAt(0).toUpperCase() + direction.slice(1)} by{' '}
                          <span className={`font-semibold ${color}`}>
                            {Math.abs(change.change).toFixed(2)}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2 text-sm">
                        <span className="text-slate-400 font-medium">
                          {change.from.toFixed(2)}
                        </span>
                        <ArrowRightIcon className="w-4 h-4 text-slate-600" />
                        <span className={`font-bold ${color}`}>
                          {change.to.toFixed(2)} {arrow}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Risk Reduction Bar */}
              <div className="mt-3 pt-3 border-t border-slate-700">
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="text-slate-500">Risk Reduction</span>
                  <span className="font-semibold text-green-400">
                    {riskReduction.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div
                    className="bg-green-500 h-2 rounded-full transition-all"
                    style={{ width: `${Math.min(100, (riskReduction / (original_prediction * 100)) * 100)}%` }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Info Box */}
      <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4">
        <h4 className="text-sm font-medium text-blue-300 mb-2">
          How to Use These Scenarios
        </h4>
        <ul className="text-xs text-slate-400 space-y-1">
          <li>• Each scenario shows specific changes you can make</li>
          <li>• Changes are based on model analysis</li>
          <li>• Choose the scenario that fits your situation best</li>
        </ul>
      </div>
    </div>
  );
};

export default CounterfactualScenarios;
