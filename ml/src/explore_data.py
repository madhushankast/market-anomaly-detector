import os
import glob
import pandas as pd
import json

def create_notebook_for_csv(csv_path, notebook_path):
    # Convert backslashes to forward slashes for the notebook string literal
    csv_path_str = csv_path.replace('\\', '/')
    filename = os.path.basename(csv_path)
    notebook_content = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"# Data Exploration for {filename}\n",
                    "This notebook automatically loads and explores the dataset."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import pandas as pd\n",
                    f"df = pd.read_csv('{csv_path_str}', on_bad_lines='skip')\n",
                    "df.head()"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "df.info()"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "df.isnull().sum()"
                ]
            }
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.8.0"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }
    
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(notebook_content, f, indent=4)

def main():
    raw_dir = r'd:\Projects\2026.06.11 market-anomaly-detector\market-anomaly-detector\ml\data\raw'
    notebook_dir = r'd:\Projects\2026.06.11 market-anomaly-detector\market-anomaly-detector\ml\notebooks'
    
    os.makedirs(notebook_dir, exist_ok=True)
    
    csv_files = glob.glob(os.path.join(raw_dir, '*.csv'))
    
    total_stocks = len(csv_files)
    print(f"Number of stocks: {total_stocks}")
    print("-" * 40)
    
    for csv_file in csv_files:
        stock_name = os.path.basename(csv_file).replace('.csv', '')
        df = pd.read_csv(csv_file, on_bad_lines='skip')
        
        rows = len(df)
        
        # Check if Date exists
        date_col = None
        for col in ['TRADING_DATE', 'Date', 'date', 'TRADING DATE']:
            if col in df.columns:
                date_col = col
                break
                
        if date_col:
            date_range = f"{df[date_col].min()} to {df[date_col].max()}"
        else:
            date_range = "Date column not found"
            
        missing = df.isnull().sum().sum()
        
        print(f"Stock: {stock_name}")
        print(f"Rows: {rows}")
        print(f"Date range: {date_range}")
        print(f"Total missing values: {missing}")
        print("-" * 40)
        
        # Create a notebook for this stock
        notebook_path = os.path.join(notebook_dir, f"{stock_name}_explore.ipynb")
        create_notebook_for_csv(csv_file, notebook_path)
        print(f"Created notebook: {notebook_path}\n")

if __name__ == '__main__':
    main()
