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
 * Combines SHAP (what's driving risk) + Counterfactuals (what to change)
 * into prioritized, actionable recommendations.
 */
const RecommendationsPanel = ({ recommendations, className = '' }) => {
  if (!recommendations) {
    return (
      <div className="text-center text-gray-500 py-8">
        No recommendations available
      </div>
    );
  }

  const { current_risk, risk_level, message, actions = [] } = recommendations;

  // Risk level styling
  const riskConfig = {
    high: {
      bgColor: 'bg-red-50',
      borderColor: 'border-red-200',
      textColor: 'text-red-900',
      badgeColor: 'bg-red-600',
      icon: ExclamationTriangleIcon
    },
    medium: {
      bgColor: 'bg-yellow-50',
      borderColor: 'border-yellow-200',
      textColor: 'text-yellow-900',
      badgeColor: 'bg-yellow-600',
      icon: ExclamationTriangleIcon
    },
    low: {
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
      textColor: 'text-green-900',
      badgeColor: 'bg-green-600',
      icon: CheckCircleIcon
    }
  };

  const config = riskConfig[risk_level] || riskConfig.medium;
  const RiskIcon = config.icon;

  // Helper to format feature names
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
      <div className={`${config.bgColor} border ${config.borderColor} rounded-lg p-4`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <RiskIcon className={`w-8 h-8 ${config.textColor}`} />
            <div>
              <h3 className={`text-lg font-semibold ${config.textColor}`}>
                {risk_level.charAt(0).toUpperCase() + risk_level.slice(1)} Risk Level
              </h3>
              <p className="text-sm text-gray-600 mt-1">{message}</p>
            </div>
          </div>

          <div className="text-right">
            <div className="text-3xl font-bold" style={{ color: config.badgeColor.replace('bg-', '#') }}>
              {(current_risk * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-gray-600 mt-1">
              Injury Risk (7-day)
            </div>
          </div>
        </div>
      </div>

      {/* No actions needed */}
      {actions.length === 0 && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
          <CheckCircleIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-600">
            {risk_level === 'low'
              ? "Great job! Keep up your current training and recovery habits."
              : "Risk is elevated, but specific interventions couldn't be identified. Consider consulting a coach."}
          </p>
        </div>
      )}

      {/* Action Items */}
      {actions.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center space-x-2 mb-2">
            <LightBulbIcon className="w-5 h-5 text-blue-600" />
            <h4 className="text-sm font-semibold text-gray-900">
              Recommended Actions
            </h4>
          </div>

          {actions.map((action, idx) => {
            const isPositive = action.recommended_value > action.current_value;
            const direction = isPositive ? 'Increase' : 'Decrease';
            const directionColor = isPositive ? 'text-blue-600' : 'text-green-600';
            const directionBg = isPositive ? 'bg-blue-50' : 'bg-green-50';

            return (
              <div
                key={idx}
                className="bg-white border-2 border-gray-200 rounded-lg p-4 hover:border-blue-400 transition-colors"
              >
                {/* Priority Badge */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 text-xs font-semibold rounded ${
                      idx === 0 ? 'bg-red-100 text-red-700' :
                      idx === 1 ? 'bg-orange-100 text-orange-700' :
                      'bg-yellow-100 text-yellow-700'
                    }`}>
                      {idx === 0 ? 'High Priority' : idx === 1 ? 'Medium' : 'Low'}
                    </span>
                    <span className="text-xs text-gray-500">
                      Impact: {action.impact.toFixed(3)}
                    </span>
                  </div>

                  <div className="flex items-center space-x-1">
                    <ArrowTrendingDownIcon className="w-4 h-4 text-green-600" />
                    <span className="text-sm font-semibold text-green-600">
                      -{(action.expected_risk_reduction * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>

                {/* Feature & Action */}
                <div className="mb-3">
                  <h5 className="text-base font-semibold text-gray-900 mb-1">
                    {formatFeature(action.feature)}
                  </h5>
                  <p className={`text-sm font-medium ${directionColor}`}>
                    {action.action}
                  </p>
                </div>

                {/* Current vs Recommended */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-gray-50 rounded p-3">
                    <div className="text-xs text-gray-600 mb-1">Current</div>
                    <div className="text-lg font-bold text-gray-900">
                      {action.current_value.toFixed(2)}
                    </div>
                  </div>

                  <div className={`${directionBg} rounded p-3`}>
                    <div className="text-xs text-gray-600 mb-1">Recommended</div>
                    <div className={`text-lg font-bold ${directionColor}`}>
                      {action.recommended_value.toFixed(2)}
                    </div>
                  </div>
                </div>

                {/* Expected Impact */}
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-600">Expected Risk Reduction</span>
                    <span className="font-semibold text-green-700">
                      {(current_risk * 100).toFixed(1)}% → {((current_risk - action.expected_risk_reduction) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                    <div
                      className="bg-green-500 h-2 rounded-full transition-all"
                      style={{ width: `${(action.expected_risk_reduction / current_risk) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Implementation Tips */}
      {actions.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-blue-900 mb-2">
            Implementation Tips
          </h4>
          <ul className="text-xs text-blue-800 space-y-1">
            <li>• Start with the highest priority action</li>
            <li>• Make gradual changes over several days</li>
            <li>• Monitor your risk daily to track improvements</li>
            <li>• Combine multiple actions for greater impact</li>
            <li>• Consult a coach if risk remains elevated</li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default RecommendationsPanel;
