# Preventing Injuries in Triathletes with Machine Learning using Wearable Sensor Data

This repository contains a comprehensive framework for generating synthetic training, physiological, and injury data for endurance athletes. The simulation models athlete profiles, training plans, daily metrics, and physiological responses over extended time periods, enabling machine learning applications in sports science without requiring access to sensitive real-world athlete data.

In addition to the simulation pipeline, the repository includes self-contained Jupyter notebooks demonstrating how to build and evaluate predictive models. A core task explored is injury prediction, specifically forecasting whether an athlete will experience an injury within the next 7 days based on wearable-derived metrics.

While this application focuses specifically on triathlon, the framework is adaptable to other sports and domains facing similar privacy and data accessibility challenges. 

Given sufficient time this repository also offers strategies for real data collection using the Garmin Connect and Strava API's.

## Repository Structure

```text
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
```

## How to Run

### Docker

To run the project using Docker, navigate to the root directory of the project in your terminal and run:

```bash
docker-compose up --build
```

This will build the Docker images for both the backend and frontend, and then start the services. The backend will be accessible on `http://localhost:5000` and the frontend on `http://localhost:5173`.

If you also want to generate synthetic data before running the application, you can execute the following command in a separate terminal:

```bash
python synthetic_data_generation/main.py
```

### Local Development

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/redsleo02/Bachelorarbeit.git
    cd injury-prediction
    ```

2.  **Install backend dependencies:**

    ```bash
    cd backend
    pip install -r requirements.txt
    ```

3.  **Start the Flask backend:**

    ```bash
    python run.py
    ```

    Backend runs at: `http://localhost:5000`

4.  **Install and start the React frontend:**

    ```bash
    cd ../frontend
    npm install
    npm run dev
    ```

    Frontend runs at: `http://localhost:5173`

## Key Features

- **Physiologically Plausible Athlete Profiles:** Generates diverse athlete characteristics based on realistic physiological parameters (in this implementatin targeted to competitive age-group triathletes)
- **Periodized Training Plans:** Creates structured training prescriptions with appropriate intensity distribution specifically targeted to athlete profiles
- **Wearable Sensor Data Simulation:** Models heart rate, sleep, HRV, and other metrics commonly collected by wearable devices
- **Training Response Modeling:** Simulates fitness, fatigue, and form based on established sports science models
- **Injury Risk Simulation:** Incorporates scheduled injuries and generates realistic injury patterns preceding them

## Usage

### Generating Synthetic Data
To run the full simulation pipeline and generate all datasets:

```bash
python synthetic_data_generation/main.py
```

This will generate multiple CSV files in the `simulated_data/` directory:
- `athletes.csv`: Synthetic athlete profiles
- `daily_data.csv`: Daily physiological readings
- `activity_data.csv`: Wearable activity logs

## Research Context
This framework was developed as part of a thesis on synthetic data generation for sports science applications. It addresses the challenge of limited data accessibility in sports performance research due to privacy concerns and the proprietary nature of athlete monitoring data.

## Acknowledgments
- This project builds on established concepts in sports science
- The simulation parameters were informed by literature on endurance athlete physiological profiles and injury risk factors