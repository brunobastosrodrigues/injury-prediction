Project Structure

  injury-prediction/
  ├── backend/                    # Flask REST API
  │   ├── app/
  │   │   ├── __init__.py        # Flask app factory
  │   │   ├── config.py          # Configuration
  │   │   ├── api/routes/        # API endpoints
  │   │   │   ├── data_generation.py
  │   │   │   ├── preprocessing.py
  │   │   │   ├── training.py
  │   │   │   └── analytics.py
  │   │   ├── services/          # Business logic
  │   │   │   ├── data_generation_service.py
  │   │   │   ├── preprocessing_service.py
  │   │   │   ├── training_service.py
  │   │   │   └── analytics_service.py
  │   │   └── utils/             # Helpers
  │   └── run.py                 # Entry point
  │
  ├── frontend/                   # React SPA
  │   ├── src/
  │   │   ├── App.jsx
  │   │   ├── api/index.js       # API client
  │   │   ├── context/           # State management
  │   │   ├── components/
  │   │   │   ├── common/        # Layout, Sidebar, Cards
  │   │   │   ├── dashboard/     # Pipeline overview
  │   │   │   ├── dataGeneration/
  │   │   │   ├── preprocessing/
  │   │   │   ├── training/
  │   │   │   ├── results/       # Model evaluation + Plotly
  │   │   │   └── analytics/     # Data exploration + Plotly
  │   │   └── hooks/
  │   └── package.json
  │
  └── data/                       # Generated data storage
      ├── raw/
      ├── processed/
      └── models/

  How to Run

  1. Install backend dependencies:
  pip install flask-cors

  2. Start the Flask backend:
  cd backend
  python run.py
  Backend runs at: http://localhost:5000

  3. Install and start the React frontend:
  cd frontend
  npm install
  npm run dev
  Frontend runs at: http://localhost:3000

  Features

  - Data Generation: Configure athlete count, year, seed and generate synthetic data
  - Preprocessing: Select split strategy (athlete/time-based), feature engineering
  - Training: Train LASSO, Random Forest, XGBoost models
  - Results: Interactive ROC curves, PR curves, confusion matrices, feature importance
  - Analytics: Distribution plots, correlation heatmaps, pre-injury window analysis, ACWR zones

  All long-running tasks (data generation, preprocessing, training) run in background threads with real-time progress polling.
