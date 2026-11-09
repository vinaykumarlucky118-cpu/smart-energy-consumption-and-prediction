"""
AI-Based Smart Energy Consumption Prediction and Monitoring System
Model Training & Evaluation Pipeline
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_PATH = os.path.join(BASE_DIR, "dataset", "energy_data.csv")
MODEL_DIR = os.path.join(BASE_DIR, "model")
STATIC_IMG_DIR = os.path.join(BASE_DIR, "static", "images")
MODEL_PATH = os.path.join(MODEL_DIR, "energy_model.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")
METRICS_PATH = os.path.join(MODEL_DIR, "metrics.json")

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(STATIC_IMG_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DATASET_PATH), exist_ok=True)

def generate_dataset(n_samples=2000, seed=42):
    """
    Generates a realistic, physically grounded energy consumption dataset.
    Physics:
      P = V * I (Watts)
      E_base = (V * I * t) / 1000 (kWh)
    Non-linear / real-world factors:
      - Standby power of active appliances
      - Temperature-driven HVAC/cooling thermal load
      - Historical consumption momentum
      - Random measurement noise
    """
    print("Generating dataset...", flush=True)
    np.random.seed(seed)
    
    # 1. Voltage: Normal household AC (210V - 250V), centered around 230V
    voltage = np.clip(np.random.normal(loc=230.0, scale=6.5, size=n_samples), 205.0, 255.0)
    
    # 2. Number of Appliances (1 to 15)
    appliances = np.random.randint(1, 16, size=n_samples)
    
    # 3. Current (Amperes): Correlated with appliance count & active load (0.8A to 18A)
    base_current = 0.5 + 0.9 * appliances + np.random.exponential(scale=1.5, size=n_samples)
    current = np.clip(base_current, 0.8, 19.5)
    
    # 4. Usage Hours per day (0.5 to 24 hours)
    usage_hours = np.clip(np.random.gamma(shape=4.0, scale=2.0, size=n_samples), 0.5, 24.0)
    
    # 5. Ambient Temperature (15°C to 45°C)
    temperature = np.clip(np.random.normal(loc=29.0, scale=6.0, size=n_samples), 14.0, 46.0)
    
    # 6. Previous Energy Consumption (historical baseline in kWh)
    estimated_past = (230.0 * current * usage_hours) / 1000.0 * 0.92
    previous_consumption = np.clip(estimated_past + np.random.normal(0, 1.2, size=n_samples), 0.5, 30.0)
    
    # Target: Real-world Energy Consumption in kWh
    e_physics = (voltage * current * usage_hours) / 1000.0 * 0.93
    temp_effect = np.maximum(0, (temperature - 24.0)) ** 1.35 * (usage_hours / 24.0) * 0.12 * (appliances / 5.0)
    appliance_factor = (appliances * 0.035 * usage_hours)
    history_factor = 0.08 * previous_consumption
    noise = np.random.normal(0, 0.25, size=n_samples)
    
    energy_consumption = np.maximum(0.2, e_physics + temp_effect + appliance_factor + history_factor + noise)
    
    df = pd.DataFrame({
        'voltage': np.round(voltage, 2),
        'current': np.round(current, 2),
        'usage_hours': np.round(usage_hours, 2),
        'number_of_appliances': appliances,
        'temperature': np.round(temperature, 1),
        'previous_consumption': np.round(previous_consumption, 2),
        'energy_consumption': np.round(energy_consumption, 2)
    })
    
    df.to_csv(DATASET_PATH, index=False)
    print(f"[Dataset] Generated {n_samples} records saved to {DATASET_PATH}", flush=True)
    return df

def train_and_evaluate():
    # 1. Load or generate dataset
    if not os.path.exists(DATASET_PATH):
        df = generate_dataset()
    else:
        df = pd.read_csv(DATASET_PATH)
        print(f"[Dataset] Loaded {len(df)} records from {DATASET_PATH}", flush=True)
    
    print("\n--- Dataset Summary ---", flush=True)
    print(df.describe().round(2), flush=True)
    
    # 2. Features and Target
    feature_cols = ['voltage', 'current', 'usage_hours', 'number_of_appliances', 'temperature', 'previous_consumption']
    target_col = 'energy_consumption'
    
    X = df[feature_cols]
    y = df[target_col]
    
    # 3. Train/Test Split (80% Train, 20% Test, fixed random state for reproducibility)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)
    
    # 4. Feature Scaling (StandardScaler)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Save Scaler
    joblib.dump(scaler, SCALER_PATH)
    print(f"\n[Artifact] Scaler saved to {SCALER_PATH}", flush=True)
    
    # 5. Model 1: Linear Regression (Baseline)
    print("Training Linear Regression baseline...", flush=True)
    lr_model = LinearRegression()
    lr_model.fit(X_train_scaled, y_train)
    lr_preds = lr_model.predict(X_test_scaled)
    
    lr_mae = mean_absolute_error(y_test, lr_preds)
    lr_rmse = np.sqrt(mean_squared_error(y_test, lr_preds))
    lr_r2 = r2_score(y_test, lr_preds)
    
    # 6. Model 2: Random Forest Regressor (Ensemble / Non-linear)
    print("Training Random Forest Regressor...", flush=True)
    rf_model = RandomForestRegressor(n_estimators=100, max_depth=12, min_samples_split=3, random_state=42, n_jobs=1)
    rf_model.fit(X_train_scaled, y_train)
    rf_preds = rf_model.predict(X_test_scaled)
    
    rf_mae = mean_absolute_error(y_test, rf_preds)
    rf_rmse = np.sqrt(mean_squared_error(y_test, rf_preds))
    rf_r2 = r2_score(y_test, rf_preds)
    
    print("\n================ MODEL EVALUATION RESULTS ================", flush=True)
    print(f"1. Linear Regression (Baseline):", flush=True)
    print(f"   - MAE  : {lr_mae:.4f} kWh", flush=True)
    print(f"   - RMSE : {lr_rmse:.4f} kWh", flush=True)
    print(f"   - R²   : {lr_r2:.4f}", flush=True)
    print(f"\n2. Random Forest Regressor:", flush=True)
    print(f"   - MAE  : {rf_mae:.4f} kWh", flush=True)
    print(f"   - RMSE : {rf_rmse:.4f} kWh", flush=True)
    print(f"   - R²   : {rf_r2:.4f}", flush=True)
    print("==========================================================", flush=True)
    
    # Select Best Model based on R2 and RMSE
    if rf_r2 >= lr_r2:
        best_name = "Random Forest Regressor"
        best_model = rf_model
        best_preds = rf_preds
    else:
        best_name = "Linear Regression"
        best_model = lr_model
        best_preds = lr_preds
        
    print(f"\n>>> Best Model Selected: {best_name} (R² = {max(rf_r2, lr_r2):.4f})", flush=True)
    
    # Save Best Model
    joblib.dump(best_model, MODEL_PATH)
    print(f"[Artifact] Best model saved to {MODEL_PATH}", flush=True)
    
    # Calculate Classification Thresholds based on Dataset Distribution
    low_threshold = float(np.percentile(df['energy_consumption'], 33))
    high_threshold = float(np.percentile(df['energy_consumption'], 67))
    print(f"\n[Classification Thresholds]:", flush=True)
    print(f"   - LOW    : < {low_threshold:.2f} kWh", flush=True)
    print(f"   - NORMAL : {low_threshold:.2f} to {high_threshold:.2f} kWh", flush=True)
    print(f"   - HIGH   : > {high_threshold:.2f} kWh", flush=True)
    
    # Feature Importances / Coefficients
    importances = rf_model.feature_importances_.tolist()
    coefficients = lr_model.coef_.tolist()
    
    # Prepare test sample comparison data for frontend display & charts
    test_samples = []
    # Take 50 representative samples for plotting
    indices = np.argsort(y_test.values)[:50]
    for idx in indices:
        test_samples.append({
            'actual': round(float(y_test.values[idx]), 2),
            'predicted_rf': round(float(rf_preds[idx]), 2),
            'predicted_lr': round(float(lr_preds[idx]), 2)
        })
        
    # Metrics payload for web frontend
    metrics_data = {
        'best_model': best_name,
        'linear_regression': {
            'mae': round(float(lr_mae), 4),
            'rmse': round(float(lr_rmse), 4),
            'r2': round(float(lr_r2), 4),
            'coefficients': [round(c, 4) for c in coefficients]
        },
        'random_forest': {
            'mae': round(float(rf_mae), 4),
            'rmse': round(float(rf_rmse), 4),
            'r2': round(float(rf_r2), 4),
            'feature_importances': [round(i, 4) for i in importances]
        },
        'features': feature_cols,
        'thresholds': {
            'low': round(low_threshold, 2),
            'high': round(high_threshold, 2)
        },
        'dataset_stats': {
            'total_records': len(df),
            'avg_consumption': round(float(df['energy_consumption'].mean()), 2),
            'min_consumption': round(float(df['energy_consumption'].min()), 2),
            'max_consumption': round(float(df['energy_consumption'].max()), 2),
            'std_consumption': round(float(df['energy_consumption'].std()), 2)
        },
        'test_samples': test_samples
    }
    
    with open(METRICS_PATH, 'w') as f:
        json.dump(metrics_data, f, indent=2)
    print(f"[Artifact] Metrics metadata saved to {METRICS_PATH}", flush=True)
    
    # 7. Generate Evaluation Visualizations (Matplotlib)
    generate_plots(y_test, lr_preds, rf_preds, feature_cols, importances, df)
    
    return metrics_data

def generate_plots(y_test, lr_preds, rf_preds, features, importances, df):
    """Generate and save publication-grade plots for model validation and viva."""
    print("Generating evaluation plots...", flush=True)
    
    # Plot 1: Actual vs Predicted Scatter & Line Plot
    plt.figure(figsize=(8, 4.5), dpi=130)
    plt.grid(True, linestyle='--', alpha=0.6)
    
    plt.scatter(y_test, rf_preds, color='#10b981', alpha=0.55, edgecolors='none', label='Random Forest (Test)')
    plt.scatter(y_test, lr_preds, color='#3b82f6', alpha=0.35, edgecolors='none', label='Linear Regression (Test)')
    
    min_val = float(min(y_test.min(), min(rf_preds.min(), lr_preds.min())))
    max_val = float(max(y_test.max(), max(rf_preds.max(), lr_preds.max())))
    plt.plot([min_val, max_val], [min_val, max_val], color='#ef4444', linestyle='--', lw=2, label='Ideal 1:1 Line')
    
    plt.title('Actual vs Predicted Energy Consumption (kWh)', fontsize=12, fontweight='bold', pad=10)
    plt.xlabel('Actual Energy Consumption (kWh)', fontsize=10)
    plt.ylabel('Predicted Energy Consumption (kWh)', fontsize=10)
    plt.legend(frameon=True)
    plt.tight_layout()
    plt.savefig(os.path.join(STATIC_IMG_DIR, 'actual_vs_predicted.png'))
    plt.close()
    
    # Plot 2: Feature Importance Bar Chart
    plt.figure(figsize=(8, 4.5), dpi=130)
    plt.grid(True, linestyle='--', alpha=0.6, axis='x')
    clean_labels = [f.replace('_', ' ').title() for f in features]
    sorted_idx = np.argsort(importances)
    
    plt.barh(np.array(clean_labels)[sorted_idx], np.array(importances)[sorted_idx], color='#059669')
    plt.title('Random Forest Feature Importance Analysis', fontsize=12, fontweight='bold', pad=10)
    plt.xlabel('Relative Importance Weight', fontsize=10)
    plt.tight_layout()
    plt.savefig(os.path.join(STATIC_IMG_DIR, 'feature_importance.png'))
    plt.close()
    
    # Plot 3: Energy Consumption Distribution (EDA)
    plt.figure(figsize=(8, 4.5), dpi=130)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.hist(df['energy_consumption'], bins=35, color='#0284c7', edgecolor='#0369a1', alpha=0.8)
    plt.axvline(float(df['energy_consumption'].mean()), color='#ef4444', linestyle='dashed', linewidth=2, label=f"Mean: {df['energy_consumption'].mean():.2f} kWh")
    plt.title('Historical Energy Consumption Distribution', fontsize=12, fontweight='bold', pad=10)
    plt.xlabel('Energy Consumption (kWh)', fontsize=10)
    plt.ylabel('Frequency', fontsize=10)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(STATIC_IMG_DIR, 'eda_distribution.png'))
    plt.close()
    
    print(f"[Visualizations] Saved plots to {STATIC_IMG_DIR}", flush=True)

if __name__ == '__main__':
    train_and_evaluate()
