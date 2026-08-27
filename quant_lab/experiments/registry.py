"""
Experiment Registry and Model Tracking.
"""
import os
import pandas as pd
from datetime import datetime

class ExperimentRegistry:
    def __init__(self, registry_file: str):
        self.registry_file = registry_file
        
    def log_experiment(self, experiment_data: dict):
        df_new = pd.DataFrame([experiment_data])
        if os.path.exists(self.registry_file):
            df_existing = pd.read_csv(self.registry_file)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_combined = df_new
        df_combined.to_csv(self.registry_file, index=False)
