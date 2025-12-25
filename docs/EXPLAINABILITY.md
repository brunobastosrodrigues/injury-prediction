# Model Interpretability (XAI) - Documentation

## Overview

This document describes the **Model Interpretability** features implemented in the injury prediction system. These features address the critical challenge of moving from "black box" predictions to **actionable coaching insights** while respecting **Federated Learning privacy constraints**.

## Motivation

The research literature emphasizes that simple feature importance rankings are insufficient for real-world applications. Athletes and coaches need:

1. **"Why?"** - Understanding what drives a specific prediction
2. **"How?"** - Understanding feature interactions (e.g., the Training-Injury Prevention Paradox)
3. **"What should I do?"** - Actionable recommendations to reduce injury risk

## Architecture: Federated XAI

### Key Challenge
In Federated Learning (FL), the **server has the model** but **not the data**. Traditional XAI assumes all data is centralized.

### Our Solution

```
┌─────────────────────────────────────────────────────────────┐
│                      FL Server                              │
│  • Trains global model                                      │
│  • Receives only AGGREGATED SHAP values                     │
│  • Builds global insights (Beeswarm plots)                  │
└─────────────────────────────────────────────────────────────┘
                           ↕
                    (Model + Aggregates)
                           ↕
┌─────────────────────────────────────────────────────────────┐
│                    Client (Athlete Device)                   │
│  • Receives global model from server                        │
│  • Computes SHAP locally on private data                    │
│  • Displays local explanations (Waterfall)                  │
│  • Generates counterfactuals (What-If)                      │
│  • Sends only mean |SHAP| values to server                  │
│  • RAW DATA NEVER LEAVES DEVICE                             │
└─────────────────────────────────────────────────────────────┘
```

## Features Implemented

### 1. Local Explanations (SHAP Waterfall)

**Purpose:** "Why am I at risk TODAY?"

**Implementation:**
- Uses `shap.TreeExplainer` for tree-based models (XGBoost, Random Forest)
- Uses `shap.LinearExplainer` for Lasso
- Computes SHAP values for a single prediction
- Visualizes as waterfall plot showing contribution of each feature

**Privacy:** Computed **locally on client device**. Never sent to server.

**API Endpoint:** `POST /api/explainability/explain/prediction`

**Request:**
```json
{
  "dataset_id": "dataset_123",
  "model_name": "xgboost",
  "athlete_data": {
    "Sleep_Hours": 6.5,
    "Acute_TSS": 150,
    "Daily_Stress": 7,
    ...
  },
  "prediction_index": -1,
  "max_display": 10
}
```

**Response:**
```json
{
  "base_value": 0.15,
  "shap_values": [0.12, -0.05, 0.08, ...],
  "feature_values": [6.5, 150, 7, ...],
  "feature_names": ["Sleep_Hours", "Acute_TSS", "Daily_Stress", ...],
  "prediction": 0.42,
  "explanation_type": "waterfall"
}
```

**Interpretation:**
- **Base value:** Model's baseline prediction (average across training data)
- **SHAP values:** Impact of each feature (positive = increases risk, negative = decreases risk)
- **Feature values:** Actual values for this athlete on this day
- **Prediction:** Final risk score (base + sum of SHAP values)

### 2. Interaction Analysis (SHAP Dependence)

**Purpose:** Reveal the "Training-Injury Prevention Paradox"

**Hypothesis:** High training load is OK if stress is low, but RISKY if stress is high.

**Implementation:**
- Uses `shap.dependence_plot` (adapted for web visualization)
- Shows how feature1's impact varies with feature2
- Auto-detects strongest interaction if feature2 not specified

**Privacy:** Can be computed locally or on aggregated data (no individual samples exposed).

**API Endpoint:** `POST /api/explainability/explain/interactions`

**Request:**
```json
{
  "dataset_id": "dataset_123",
  "model_name": "xgboost",
  "feature1": "Acute_TSS",
  "feature2": "Daily_Stress",
  "sample_size": 1000
}
```

**Response:**
```json
{
  "feature1_values": [100, 150, 200, ...],
  "shap_values": [0.05, 0.12, 0.25, ...],
  "interaction_values": [3, 7, 8, ...],
  "feature1_name": "Acute_TSS",
  "feature2_name": "Daily_Stress",
  "explanation_type": "dependence"
}
```

**Interpretation:**
- Plot feature1_values (x-axis) vs shap_values (y-axis), colored by interaction_values
- If high stress (red) shows steeper slope than low stress (green), interaction is confirmed

### 3. Global Feature Importance

**Purpose:** "What matters most across all athletes?"

**Implementation:**
- Computes mean absolute SHAP values across dataset
- Visualizes as bar chart or beeswarm plot
- In FL: Each client computes locally, sends only mean to server

**Privacy:** **Only aggregated statistics** shared with server (privacy-preserving).

**API Endpoint:** `POST /api/explainability/explain/global`

**Request:**
```json
{
  "dataset_id": "dataset_123",
  "model_name": "xgboost",
  "sample_size": 1000
}
```

**Response:**
```json
{
  "mean_shap_values": [0.15, 0.12, 0.10, ...],
  "feature_names": ["Acute_TSS", "Sleep_Hours", "Daily_Stress", ...],
  "explanation_type": "global",
  "shap_values_matrix": [[...], [...], ...],
  "feature_values_matrix": [[...], [...], ...]
}
```

### 4. Counterfactual Explanations (What-If)

**Purpose:** "What should I change to avoid injury?"

**Implementation:**
- Uses `dice-ml` (Diverse Counterfactual Explanations)
- Generates feasible scenarios that flip the prediction (high risk → low risk)
- Respects immutable features (Age, Gender)
- Only varies actionable features (Sleep, Training Intensity, etc.)

**Privacy:** Computed **locally on client device**. Never sent to server.

**API Endpoint:** `POST /api/explainability/counterfactuals`

**Request:**
```json
{
  "dataset_id": "dataset_123",
  "model_name": "xgboost",
  "athlete_data": {...},
  "desired_class": 0,
  "total_cfs": 3,
  "continuous_features": ["Sleep_Hours", "Acute_TSS", ...],
  "immutable_features": ["Age", "Gender"]
}
```

**Response:**
```json
{
  "counterfactuals": [
    {
      "changes": {
        "Sleep_Hours": {"from": 6, "to": 8, "change": 2},
        "Acute_TSS": {"from": 150, "to": 120, "change": -30}
      },
      "predicted_risk": 0.15,
      "risk_reduction": 0.27
    },
    ...
  ],
  "original_prediction": 0.42,
  "total_scenarios": 3
}
```

**Interpretation:**
- Each scenario shows specific changes needed to reduce risk
- Changes are feasible (based on historical data distribution)
- Athlete chooses which scenario fits their lifestyle

### 5. Actionable Recommendations

**Purpose:** Combine SHAP + Counterfactuals into prioritized action plan

**Implementation:**
- Uses SHAP to identify top risk drivers
- Uses counterfactuals to find actionable changes
- Prioritizes by impact (SHAP importance) × feasibility (counterfactual)

**Privacy:** Computed **locally on client device**.

**API Endpoint:** `POST /api/explainability/recommendations`

**Request:**
```json
{
  "dataset_id": "dataset_123",
  "model_name": "xgboost",
  "athlete_data": {...},
  "risk_threshold": 0.3
}
```

**Response:**
```json
{
  "current_risk": 0.42,
  "risk_level": "high",
  "message": "Found 3 actionable recommendations to reduce risk.",
  "actions": [
    {
      "feature": "Sleep_Hours",
      "current_value": 6,
      "recommended_value": 8,
      "action": "Increase Sleep Hours by 2.0",
      "impact": 0.15,
      "expected_risk_reduction": 0.27
    },
    ...
  ]
}
```

## Frontend Components

### WaterfallPlot.jsx
Renders SHAP waterfall visualization showing feature contributions.

### DependencePlot.jsx
Renders scatter plot for interaction analysis (feature1 vs SHAP, colored by feature2).

### GlobalSHAPPlot.jsx
Renders bar chart or beeswarm plot for global feature importance.

### CounterfactualScenarios.jsx
Displays what-if scenarios with specific action recommendations.

### RecommendationsPanel.jsx
Combines all explanations into prioritized action plan with implementation tips.

## Usage

### 1. Navigate to Model Interpretability Page

Access via sidebar: **🔍 Model Interpretability**

### 2. Select Dataset & Model

Choose from completed pipeline runs.

### 3. Explore Tabs

- **Local (Waterfall):** Why am I at risk today?
- **Global Importance:** What matters most overall?
- **Interactions:** How do features interact?
- **What-If:** What should I change?
- **Recommendations:** Prioritized action plan

### 4. Integrate into Athlete Dashboard (Future)

The interpretability components can be embedded into individual athlete views for personalized daily insights.

## Backend Service

### ExplainabilityService (`app/services/explainability.py`)

Main service class with methods:

- `explain_prediction()` - Local SHAP waterfall
- `explain_interactions()` - Feature interaction analysis
- `compute_global_shap()` - Global feature importance
- `generate_counterfactuals()` - What-if scenarios
- `generate_recommendations()` - Actionable insights

### API Routes (`app/api/routes/explainability.py`)

RESTful endpoints for all explainability features.

## Technical Details

### SHAP Implementation

**For Tree Models (XGBoost, Random Forest):**
```python
explainer = shap.TreeExplainer(model, feature_perturbation="interventional")
shap_values = explainer(X)
```

**For Linear Models (Lasso):**
```python
explainer = shap.LinearExplainer(model, background_data)
shap_values = explainer(X)
```

### Counterfactual Implementation

```python
import dice_ml

# Data interface
d = dice_ml.Data(
    dataframe=train_data,
    continuous_features=['Sleep_Hours', 'Acute_TSS', ...],
    outcome_name='Injury_7day'
)

# Model interface
m = dice_ml.Model(model=model, backend='sklearn')

# Generate counterfactuals
exp = dice_ml.Dice(d, m, method='random')
dice_exp = exp.generate_counterfactuals(
    query_instance,
    total_CFs=3,
    desired_class=0,
    features_to_vary=[...]  # Exclude immutable features
)
```

## Privacy Guarantees

### What Stays on Device (Client-side)
✅ Raw training data
✅ Individual SHAP values (before aggregation)
✅ Waterfall plots
✅ Counterfactual scenarios
✅ Personal recommendations

### What Can Be Shared with Server
✅ Mean absolute SHAP values (aggregated)
✅ Model parameters (already on server)
❌ Individual data points
❌ Raw SHAP values for specific athletes

## Dependencies

Added to `requirements.txt`:
- `shap==0.46.0` - SHAP explanations
- `dice-ml==0.11` - Counterfactual generation

## Future Enhancements

### 1. Integrate into Athlete Dashboard
- Add "Why am I at risk?" section to athlete detail view
- Real-time recommendations based on daily metrics

### 2. Federated SHAP Aggregation
- Implement secure aggregation protocol
- Allow athletes to opt-in to sharing aggregated SHAP values
- Build global beeswarm plots without exposing individual data

### 3. Temporal SHAP
- Explain predictions over time
- Show how risk factors evolve during training cycles

### 4. Multi-Model Comparison
- Compare SHAP values across Lasso, RF, and XGBoost
- Identify which features are consistently important

### 5. Interactive What-If Simulator
- Allow athletes to drag sliders (e.g., Sleep Hours: 6 → 8)
- Real-time risk prediction updates
- Similar to existing What-If tab in Analytics, but with counterfactual-based suggestions

## References

1. **SHAP:** Lundberg, S. M., & Lee, S. I. (2017). A unified approach to interpreting model predictions. NeurIPS.
2. **DiCE:** Mothilal, R. K., Sharma, A., & Tan, C. (2020). Explaining machine learning classifiers through diverse counterfactual explanations. FAT*.
3. **Federated XAI:** Stripelis, D., et al. (2021). Secure Neuroimaging Analysis using Federated Learning with Homomorphic Encryption. MIDL.

## Contact

For questions or issues, please refer to the main project documentation or contact the development team.

---

**Last Updated:** 2025-12-25
**Version:** 1.0.0
