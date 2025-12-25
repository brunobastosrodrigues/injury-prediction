import React from 'react';
import {
  ExclamationTriangleIcon,
  CheckCircleIcon,
  LightBulbIcon,
  ArrowTrendingDownIcon
} from '@heroicons/react/24/outline';

/**
 * Recommendations Panel - Actionable Insights
 *
 * Combines SHAP analysis with actionable recommendations.
 */
const RecommendationsPanel = ({ recommendations, className = '' }) => {
  if (!recommendations) {
    return (
      <div className="text-center text-slate-400 py-8">
        No recommendations available
      </div>
    );
  }

  const { current_risk, risk_level, message, actions = [] } = recommendations;

  const riskConfig = {
    high: {
      bgColor: 'bg-red-500/10',
      borderColor: 'border-red-500/30',
      textColor: 'text-red-300',
      valueColor: 'text-red-400',
      icon: ExclamationTriangleIcon
    },
    moderate: {
      bgColor: 'bg-yellow-500/10',
      borderColor: 'border-yellow-500/30',
      textColor: 'text-yellow-300',
      valueColor: 'text-yellow-400',
      icon: ExclamationTriangleIcon
    },
    low: {
      bgColor: 'bg-green-500/10',
      borderColor: 'border-green-500/30',
      textColor: 'text-green-300',
      valueColor: 'text-green-400',
      icon: CheckCircleIcon
    }
  };

  const config = riskConfig[risk_level] || riskConfig.moderate;
  const RiskIcon = config.icon;

  const formatFeature = (name) => {
    return name
      .replace(/_/g, ' ')
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Current Risk Status */}
      <div className={`${config.bgColor} border ${config.borderColor} rounded-xl p-4`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <RiskIcon className={`w-8 h-8 ${config.textColor}`} />
            <div>
              <h3 className={`text-lg font-semibold ${config.textColor}`}>
                {risk_level.charAt(0).toUpperCase() + risk_level.slice(1)} Risk
              </h3>
              <p className="text-sm text-slate-400 mt-1">{message}</p>
            </div>
          </div>

          <div className="text-right">
            <div className={`text-3xl font-bold ${config.valueColor}`}>
              {(current_risk * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-slate-500 mt-1">
              7-day Risk
            </div>
          </div>
        </div>
      </div>

      {/* No actions needed */}
      {actions.length === 0 && (
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 text-center">
          <CheckCircleIcon className="w-12 h-12 text-slate-500 mx-auto mb-3" />
          <p className="text-slate-400">
            {risk_level === 'low'
              ? "Great job! Keep up your current training and recovery habits."
              : "Risk is elevated, but specific interventions couldn't be identified."}
          </p>
        </div>
      )}

      {/* Action Items */}
      {actions.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center space-x-2 mb-2">
            <LightBulbIcon className="w-5 h-5 text-amber-400" />
            <h4 className="text-sm font-semibold text-slate-200">
              Recommended Actions
            </h4>
          </div>

          {actions.map((action, idx) => {
            const priorityColors = [
              { bg: 'bg-red-500/20', text: 'text-red-300', label: 'High Priority' },
              { bg: 'bg-orange-500/20', text: 'text-orange-300', label: 'Medium' },
              { bg: 'bg-yellow-500/20', text: 'text-yellow-300', label: 'Low' }
            ];
            const priority = priorityColors[Math.min(idx, 2)];

            return (
              <div
                key={idx}
                className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 hover:border-blue-500/50 transition-colors"
              >
                {/* Priority Badge */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 text-xs font-semibold rounded ${priority.bg} ${priority.text}`}>
                      {priority.label}
                    </span>
                    <span className="text-xs text-slate-500">
                      Impact: {action.impact.toFixed(3)}
                    </span>
                  </div>
                </div>

                {/* Feature & Action */}
                <div className="mb-3">
                  <h5 className="text-base font-semibold text-slate-200 mb-1">
                    {formatFeature(action.feature)}
                  </h5>
                  <p className="text-sm font-medium text-blue-400">
                    {action.action}
                  </p>
                </div>

                {/* Current vs Recommended */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-slate-900/50 rounded-lg p-3">
                    <div className="text-xs text-slate-500 mb-1">Current</div>
                    <div className="text-lg font-bold text-slate-300">
                      {action.current_value.toFixed(2)}
                    </div>
                  </div>

                  <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-3">
                    <div className="text-xs text-slate-500 mb-1">Recommended</div>
                    <div className="text-lg font-bold text-green-400">
                      {action.recommended_value.toFixed(2)}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Implementation Tips */}
      {actions.length > 0 && (
        <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4">
          <h4 className="text-sm font-medium text-blue-300 mb-2">
            Implementation Tips
          </h4>
          <ul className="text-xs text-slate-400 space-y-1">
            <li>• Start with the highest priority action</li>
            <li>• Make gradual changes over several days</li>
            <li>• Monitor your risk daily to track improvements</li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default RecommendationsPanel;
