# Preventing Injuries in Triathletes with Machine Learning using Wearable Sensor Data

This repository contains a comprehensive framework for generating synthetic training, physiological, and injury data for endurance athletes. The simulation models athlete profiles, training plans, daily metrics, and physiological responses over extended time periods, enabling machine learning applications in sports science without requiring access to sensitive real-world athlete data.

In addition to the simulation pipeline, the repository includes self-contained Jupyter notebooks demonstrating how to build and evaluate predictive models. A core task explored is injury prediction, specifically forecasting whether an athlete will experience an injury within the next 7 days based on wearable-derived metrics.

While this application focuses specifically on triathlon, the framework is adaptable to other sports and domains facing similar privacy and data accessibility challenges. 

Given sufficient time this repository also offers strategies for real data collection using the Garmin Connect and Strava API's.

## Repository Structure

```text
├── explored_unused_solutions/    # Alternative approaches explored for real data access
│   ├── garmin_api_interface/     # Web interface for Garmin API data collection
│   └── strava_api_integration/   # Implementation for Strava API access
│
├── notebooks/                    # Jupyter notebooks documenting analysis
│   ├── 01_eda.ipynb              # Exploratory data analysis of synthetic datasets
│   ├── 02_preprocessing_feature_engineering.ipynb  # Data preparation procedures
│   └── 03_ML_analysis.ipynb      # Machine learning implementation and evaluation
│
├── simulated_data/               # Output directory for generated datasets
│
└── synthetic_data_generation/    # Core simulation framework
    ├── logistics/                # Utility functions and helper modules
    │   ├── athlete_profiles.py   # generates realistic athlete profiles
    │   └── training_plan.py      # Generates personalised training plans to athlete profiles
    ├── sensor_data/              # Wearable sensor data simulation
    │   ├── daily_metrics_simulation.py  # Simulates daily biometric readings
    │   └── simulate_activities.py       # Generates training session data
    ├── training_response/        # Physiological response modeling
    │   ├── fitness_fatigue_form.py      # Implements fitness-fatigue model
    │   └── injury_simulation.py         # Injects realistic injury patters
    ├── main.py                   # Main orchestration script
    ├── simulate_year.py          # Annual simulation controller
    └── README.md                 # Module-specific documentation
```

## Key Features

- **Physiologically Plausible Athlete Profiles:** Generates diverse athlete characteristics based on realistic physiological parameters (in this implementatin targeted to competitive age-group triathletes)
- **Periodized Training Plans:** Creates structured training prescriptions with appropriate intensity distribution specifically targeted to athlete profiles
- **Wearable Sensor Data Simulation:** Models heart rate, sleep, HRV, and other metrics commonly collected by wearable devices
- **Training Response Modeling:** Simulates fitness, fatigue, and form based on established sports science models
- **Injury Risk Simulation:** Incorporates scheduled injuries and generates realistic injury patterns preceding them

## Installation

1. Clone the repository: 

```bash git clone https://github.com/redsleo02/Bachelorarbeit.git cd synthetic-athlete-data ``` 

2. Create a virtual environment and install the dependencies: 

```bash python -m venv venv source venv/bin/activate # On Windows: venv\Scripts\activate pip install -r requirements.txt ``` 

## Usage 
### Generating Synthetic Data 
To run the full simulation pipeline and generate all datasets: 

```bash python synthetic_data_generation/main.py ``` 

This will generate multiple CSV files in the `simulated_data/` directory: 
- `athletes.csv`: Synthetic athlete profiles 
- `daily_data.csv`: Daily physiological readings 
- `activity_data.csv`: Wearable activity logs 

## Research Context
This framework was developed as part of a thesis on synthetic data generation for sports science applications. It addresses the challenge of limited data accessibility in sports performance research due to privacy concerns and the proprietary nature of athlete monitoring data.

## Acknowledgments
- This project builds on established concepts in sports science
- The simulation parameters were informed by literature on endurance athlete physiological profiles and injury risk factors