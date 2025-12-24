from pydantic import BaseModel, Field, conint, confloat, field_validator
from typing import List, Optional, Dict, Any

class DataGenerationSchema(BaseModel):
    n_athletes: int = Field(default=100, ge=1, le=5000)
    simulation_year: int = Field(default=2024, ge=2000, le=2030)
    random_seed: int = Field(default=42)
    injury_config: Optional[Dict[str, Any]] = None

class PreprocessingSchema(BaseModel):
    dataset_id: str
    split_strategy: str = Field(default='athlete_based')
    split_ratio: float = Field(default=0.2, ge=0.05, le=0.5)
    prediction_window: int = Field(default=7, ge=1, le=30)
    random_seed: int = Field(default=42)

    @field_validator('split_strategy')
    @classmethod
    def validate_strategy(cls, v: str) -> str:
        if v not in ['athlete_based', 'time_based']:
            raise ValueError('split_strategy must be athlete_based or time_based')
        return v

class TrainingSchema(BaseModel):
    split_id: str
    models: List[str] = Field(default_factory=lambda: ['random_forest'])
    hyperparameters: Optional[Dict[str, Dict[str, Any]]] = None

    @field_validator('models')
    @classmethod
    def validate_models(cls, v: List[str]) -> List[str]:
        valid_types = ['lasso', 'random_forest', 'xgboost']
        for mt in v:
            if mt not in valid_types:
                raise ValueError(f'Invalid model type: {mt}. Valid types: {valid_types}')
        return v

class IngestionSchema(BaseModel):
    dataset_id: str
    data_type: str = Field(default='garmin_csv')

