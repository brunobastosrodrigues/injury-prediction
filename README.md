# Preventing Injuries in Triathletes with Machine Learning using Wearable Sensor Data

## Application Preview

<img width="941" height="570" alt="injury-prediction-landingpage-new" src="https://github.com/user-attachments/assets/47f36be8-647d-43dc-8fb3-a1e3717a43c7" />

> *Landing page with research abstract and validation results overview.*

This repository contains a comprehensive framework for injury prediction in endurance athletes using machine learning. The platform provides:

- **Synthetic Data Generation**: Physiologically plausible training and physiological data simulation
- **ML Pipeline**: Complete workflow from data preprocessing to model training and evaluation
- **Scientific Validation Suite**: Publication-quality validation with Three Pillars framework
- **Explainable AI (XAI)**: SHAP-based model interpretability with counterfactual explanations
- **Interactive Analytics**: Risk analysis, what-if scenarios, and athlete-level dashboards

While focused on triathlon, the framework is adaptable to other endurance sports facing similar data accessibility challenges.

## Key Features

### Data Generation & Ingestion
- **Synthetic Athlete Profiles**: Diverse athlete characteristics based on realistic physiological parameters for competitive age-group triathletes
- **Periodized Training Plans**: Structured training prescriptions with appropriate intensity distribution
- **Wearable Sensor Simulation**: Heart rate, sleep, HRV, and metrics commonly collected by devices
- **Real Data Support**: Garmin Connect data ingestion for real-world validation

### Machine Learning Pipeline
- **Preprocessing**: Feature engineering with ACWR (Acute:Chronic Workload Ratio), rolling statistics, and lag features
- **Three Model Types**: Lasso (L1 regularized), Random Forest, and XGBoost
- **7-Day Injury Prediction Window**: Binary classification for near-term injury risk
- **Hyperparameter Configuration**: YAML-based settings for reproducible experiments

### Scientific Validation
- **Three Pillars Framework**: Face validity, predictive validity, and hypothesis validity
- **Causal Mechanism Analysis**: ACWR zone injury rate verification
- **External Validation**: Real PMData dataset support for cross-validation
- **Publication-Ready Metrics**: AUC-ROC, sensitivity, specificity, calibration curves

### Explainable AI (Federated XAI)
- **SHAP Waterfall Plots**: Individual prediction explanations
- **Feature Dependence**: Partial dependence and interaction effects
- **Counterfactual Explanations**: "What-if" scenarios for risk modification
- **Personalized Recommendations**: Actionable insights for injury prevention

### Analytics & Visualization
- **Dataset Explorer**: Distribution analysis, correlations, and pre-injury patterns
- **Athlete Dashboard**: Individual athlete profiles with risk timeline
- **What-If Simulator**: Interactive intervention planning
- **Dark/Light Theme**: Full theme support across all components
- **Mobile Responsive**: Optimized for all screen sizes

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React + Vite)                   │
│  Landing → Dashboard → Generation → Preprocessing → Training    │
│           → Results → Interpretability → Analytics → Validation │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Backend (Flask + Celery)                     │
│  Routes: data_generation, preprocessing, training, analytics,   │
│          validation, explainability                              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Data Storage                             │
│  /data/raw/      - Generated/ingested datasets                  │
│  /data/processed/ - Train/test splits                           │
│  /data/models/    - Trained model artifacts                     │
│  /data/validation/ - Pre-seeded validation results              │
└─────────────────────────────────────────────────────────────────┘
```

## How to Run

### Docker (Recommended)

```bash
docker-compose up --build
```

Services:
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:5000`
- Redis: `localhost:6379` (for Celery task queue)

### Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/brunobastosrodrigues/injury-prediction
   cd injury-prediction
   ```

2. **Backend setup:**
   ```bash
   cd backend
   pip install -r requirements.txt
   python run.py
   ```
   Backend runs at: `http://localhost:5000`

3. **Celery worker (for async tasks):**
   ```bash
   celery -A app.celery_app.celery_app worker --loglevel=info
   ```

4. **Frontend setup:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Frontend runs at: `http://localhost:5173`

### Generating Synthetic Data (Standalone)

```bash
python synthetic_data_generation/main.py
```

Outputs to `data/raw/`:
- `athletes.csv`: Synthetic athlete profiles
- `daily_data.csv`: Daily physiological readings
- `activity_data.csv`: Training activity logs

## Project Structure

```
injury-prediction/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # Flask blueprints
│   │   ├── services/            # Business logic
│   │   ├── config/              # Hyperparameters (YAML)
│   │   └── utils/               # Progress tracking, helpers
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── components/          # React components by feature
│   │   ├── context/             # Pipeline & Theme context
│   │   └── api/                 # Axios client
│   └── vite.config.js
├── synthetic_data_generation/
│   ├── main.py                  # Entry point
│   ├── simulate_year.py         # Year-long simulation
│   ├── logistics/               # Athlete profiles, training plans
│   └── training_response/       # Injury simulation models
└── data/
    ├── raw/                     # Generated datasets
    ├── processed/               # Train/test splits
    ├── models/                  # Trained models
    └── validation/              # Pre-seeded validation results
```

## Configuration

- **ML Hyperparameters**: `backend/app/config/hyperparameters.yaml`
- **Backend Config**: `backend/app/config.py` (100 athletes, 2024 year, seed 42)
- **Frontend Proxy**: `frontend/vite.config.js` (`/api` → backend)

## Screenshots

<img width="1254" height="690" alt="injury-prediction-athlete-profile" src="https://github.com/user-attachments/assets/4c0a263a-6a64-4aa6-849d-1a5b6a799018" />

> *Athlete profile generation with physiological parameters.*

<img width="1254" height="690" alt="injury-prediction-athlete-profile2" src="https://github.com/user-attachments/assets/d93eeadf-8125-4940-b931-63586344c344" />

> *Training simulation with CTL/ATL/TSB modeling.*

## Research Context

This framework was developed as part of research on injury prediction in endurance athletes at the University of St. Gallen, Embedded Sensing Group. It addresses the challenge of limited data accessibility in sports performance research due to privacy concerns and the proprietary nature of athlete monitoring data.

The platform supports both synthetic data experimentation and validation with real-world datasets (e.g., PMData from Ni et al., 2019).

## Acknowledgments

- Built on established sports science concepts (Banister's Impulse-Response Model, ACWR)
- Simulation parameters informed by literature on endurance athlete physiology and injury risk factors
- Validation framework inspired by publication standards in sports medicine research
