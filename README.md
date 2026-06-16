# Market Anomaly Detector

**Author:** Madhushanka T.

A Python‑based end‑to‑end pipeline for detecting anomalies in Colombo Stock Exchange (CSE) historical data.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Data Pipeline](#data-pipeline)
- [Model Training](#model-training)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

### Overview
This repository contains a full data‑engineering and machine‑learning workflow:
1. **Raw data cleaning** – removes duplicate header rows, normalises dates and numeric columns.
2. **Feature engineering** – calculates returns, moving averages, RSI, MACD, volatility, volume/turnover ratios and target variables.
3. **Training dataset creation** – concatenates all stocks into a single training CSV.
4. **Model training** – trains a binary classification XGBoost model to predict whether the price will increase over the next 30 days.

All scripts are written in pure Python using `pandas`, `numpy` and `xgboost` and are fully reproducible.

### Features
- Robust CSV cleaning for the irregular CSE files.
- Technical indicator suite (SMA, RSI, MACD, volatility, etc.).
- Forward‑looking target (`future_return_30`) and binary label (`target_up`).
- Automated dataset builder.
- Simple training script with time‑based train/test split.

### Installation
```bash
# Clone the repo (once pushed to GitHub)
git clone https://github.com/your-username/market-anomaly-detector.git
cd market-anomaly-detector

# Create a virtual environment
python -m venv .venv
source .venv/Scripts/activate   # Windows PowerShell

# Install dependencies
pip install -r requirements.txt
```

### Data Pipeline
```bash
# Clean raw CSV files and generate processed feature files
python -m ml.src.data_pipeline

# Build the master training dataset
python -m ml.src.build_dataset
```

### Model Training
```bash
python -m ml.src.train_model
```
The script will output `train_df.csv`, `test_df.csv` and a serialized model `stock_model.pkl` under `ml/models/`.

### Usage
Import the trained model in your own Python code:
```python
import joblib
model = joblib.load('ml/models/stock_model.pkl')
# Predict on a new DataFrame `X_new`
preds = model.predict(X_new)
```

### Project Structure
```
market-anomaly-detector/
│   README.md
│   LICENSE
│   .gitignore
│   requirements.txt
│
├───ml/
│   ├───data/
│   │   ├───raw/            # Original CSVs (ignored by git)
│   │   ├───clean_raw/      # Cleaned CSVs (generated)
│   │   ├───processed/      # Feature CSVs (generated)
│   │   └───training/       # Master training dataset (generated)
│   ├───src/
│   │   ├───data_pipeline.py
│   │   ├───feature_engineering.py
│   │   ├───build_dataset.py
│   │   └───train_model.py
│   └───models/            # Trained model files
│
└───app/ … (service code)
```

### Contributing
Feel free to open Issues or Pull Requests. Please follow the existing code style and run the CI workflow before submitting.

### License
This project is licensed under the MIT License – see the `LICENSE` file for details.
