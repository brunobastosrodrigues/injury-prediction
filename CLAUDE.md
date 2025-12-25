# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Injury prediction system for triathletes using machine learning. Generates synthetic training/physiological data and provides an ML pipeline to predict injuries within a 7-day window. Full-stack web application with Flask backend, React frontend, and Celery for async task processing.

## Development Commands

### Docker (Recommended)
```bash
docker-compose up --build    # Start all services (backend:5000, frontend:5173, redis:6379)
```

### Backend (Flask)
```bash
cd backend
pip install -r requirements.txt
python run.py                                              # Flask dev server on :5000
celery -A app.celery_app.celery_app worker --loglevel=info # Celery worker (requires Redis)
```

### Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev      # Dev server on :5173 with HMR
npm run build    # Production build
```

### Synthetic Data Generation (Standalone)
```bash
python synthetic_data_generation/main.py
```

## Architecture

### Pipeline Flow
Data Generation → Preprocessing/Feature Engineering → Model Training → Evaluation/Analytics

### Backend (`/backend`)
- **Flask + Blueprints**: Routes in `app/api/routes/` (data_generation, preprocessing, training, analytics, data_ingestion)
- **Service Layer**: Business logic in `app/services/` - each pipeline stage has a dedicated service
- **Async Tasks**: Celery handles long-running operations (generation, training); frontend polls status
- **Validation**: Pydantic schemas in `app/api/schemas.py`
- **ML Config**: `app/config/hyperparameters.yaml` (Lasso, Random Forest, XGBoost settings)

### Frontend (`/frontend`)
- **React 18 + Vite**: SPA with React Router
- **State**: PipelineContext (`src/context/`) manages pipeline state across views
- **Visualization**: Plotly.js for charts (`src/components/results/`, `src/components/analytics/`)
- **API Client**: Axios in `src/api/index.js` (proxied to backend via Vite config)

### Simulation Engine (`/synthetic_data_generation`)
- **Orchestrator**: `simulate_year.py` runs year-long athlete simulation
- **Athlete Profiles**: `logistics/athlete_profiles.py` - generates realistic athlete attributes
- **Training Plans**: `logistics/training_plan.py` - periodized training with CTL/ATL/TSB
- **Injury Model**: `training_response/injury_simulation.py` - risk calculations based on load/fatigue

### Data Storage
- `/data/raw/` - Generated datasets (CSV/Parquet per dataset_id)
- `/data/processed/` - Train/test splits after preprocessing
- `/data/models/` - Serialized trained models (joblib/pkl)

## Key Patterns

- **Dataset-centric**: All operations reference a `dataset_id` that tracks data through the pipeline
- **Job Tracking**: Async operations return job IDs; poll `/api/*/status/{job_id}` for progress
- **Progress Tracker**: `backend/app/utils/progress_tracker.py` for real-time task updates

## ML Models

Three models available for injury prediction (7-day window):
- Lasso (L1 regularized logistic regression)
- Random Forest (200 estimators, max_depth 8)
- XGBoost (400 estimators, max_depth 2)

## Configuration

- `backend/app/config.py` - Environment configs, default params (100 athletes, 2024 year, seed 42)
- `backend/app/config/hyperparameters.yaml` - ML model hyperparameters
- `frontend/vite.config.js` - Dev proxy (`/api` → `http://backend:5000`)

## Frontend Structure

### Pages & Components
- **Landing Page** (`/`) - Hero section with feature highlights, links to dashboard
- **Dashboard** (`/dashboard`) - Pipeline overview with status cards
- **Data Generation** (`/data-generation`) - Generate synthetic athlete data
- **Data Ingestion** (`/data-ingestion`) - Upload real Garmin data
- **Preprocessing** (`/preprocessing`) - Feature engineering pipeline
- **Training** (`/training`) - Model training with hyperparameter config
- **Results** (`/results`) - Model evaluation metrics, ROC/PR curves, feature importance
- **Analytics** (`/analytics`) - Dataset exploration with tabs: Distributions, Correlations, Pre-Injury, ACWR, Stats, What-If
- **Athlete Dashboard** (`/athlete-dashboard`) - Individual athlete analysis with tabs: Overview, Timeline, Pre-Injury Patterns, Risk Analysis, What-If

### Common Components (`/frontend/src/components/common/`)
- `Layout.jsx` - Main layout with responsive sidebar
- `Sidebar.jsx` - Navigation with mobile hamburger menu
- `Header.jsx` - Top bar with mobile menu toggle
- `Card.jsx` - Reusable card wrapper
- `ProgressBar.jsx` - Task progress indicator
- `StatusBadge.jsx` - Status pill component

## Recent Changes (Dec 2025)

### Mobile Responsiveness (commit a04b3f2)
All frontend components are now fully mobile-responsive:
- Collapsible sidebar with hamburger menu on mobile
- Horizontal scrollable tabs for navigation
- Responsive grid layouts (1 col mobile → 2-4 cols desktop)
- Scaled typography using `text-xs sm:text-sm` pattern
- Optimized Plotly charts with hidden mode bar on mobile
- Touch-friendly controls and spacing

### Athlete Dashboard Features
- Individual athlete profiles with lifestyle analysis
- Risk timeline visualization with threshold zones
- Pre-injury pattern detection across multiple metrics
- What-If simulator for intervention planning
- Personalized recommendations based on athlete data

## Development Notes

### Running with Docker
```bash
docker compose up --build          # All services
docker compose up frontend -d      # Frontend only
docker compose logs frontend -f    # Watch logs
```

### Testing Mobile Responsiveness
Use browser DevTools (F12 → Ctrl+Shift+M) to test responsive breakpoints:
- `sm`: 640px+ (tablets)
- `md`: 768px+
- `lg`: 1024px+ (desktop)

### Tailwind CSS Patterns Used
- Responsive: `class="text-xs sm:text-sm lg:text-base"`
- Grids: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-4`
- Spacing: `p-2 sm:p-4`, `gap-2 sm:gap-4`
- Visibility: `hidden sm:block`, `sm:hidden`
