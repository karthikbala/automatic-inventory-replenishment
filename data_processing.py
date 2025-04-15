"""
Data Processing Module for Automatic Inventory Replenishment System
- Loads and preprocesses historical sales data from CSV
- Validates and logs malformed rows
- Prepares data for Prophet forecasting
- Provides forecasting function using Prophet
"""

import pandas as pd
import logging
from prophet import Prophet


def load_and_validate_csv(csv_path):
    """
    Loads CSV, validates rows, logs malformed rows, returns cleaned DataFrame.
    """
    import csv
    valid_rows = []
    malformed_rows = []
    required_keys = [
        'Company', 'Warehouse', 'Date', 'SKU', 'Sales', 'SOH', 'Open_PO', 'Open_SO',
        'Promotion', 'Festival', 'Min_Days', 'Max_Days'
    ]
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            try:
                for key in required_keys:
                    if row[key] == '' or row[key] is None:
                        raise ValueError(f"Missing value for {key}")
                # Try type conversion for numerics
                float(row['Sales'])
                float(row['SOH'])
                float(row['Open_PO'])
                float(row['Open_SO'])
                float(row['Min_Days'])
                float(row['Max_Days'])
                valid_rows.append(row)
            except Exception as e:
                logging.warning(f"Malformed row {i}: {row} | Error: {e}")
                malformed_rows.append(row)
    logging.info(f"Total rows: {len(valid_rows) + len(malformed_rows)}, Valid: {len(valid_rows)}, Skipped: {len(malformed_rows)}")
    import pandas as pd
    df = pd.DataFrame(valid_rows)
    return df

def preprocess_data(df):
    """
    Preprocesses DataFrame for Prophet:
    - Renames 'Date' to 'ds', 'Sales' to 'y'
    - Converts 'Promotion'/'Festival' to binary
    """
    df = df.copy()
    df['ds'] = pd.to_datetime(df['Date'])
    df['y'] = pd.to_numeric(df['Sales'])
    df['promotion'] = df['Promotion'].map({'YES': 1, 'NO': 0})
    df['festival'] = df['Festival'].map({'YES': 1, 'NO': 0})
    return df[['ds', 'y', 'promotion', 'festival']]

def forecast_sales(df, interval=1):
    """
    Uses Prophet to forecast sales for the given interval.
    Adds 'promotion' and 'festival' as regressors.
    Returns forecasted sales for the interval (sum if interval > 1).
    """
    m = Prophet()
    m.add_regressor('promotion')
    m.add_regressor('festival')
    m.fit(df)
    # Create future dataframe
    future = m.make_future_dataframe(periods=interval)
    for reg in ['promotion', 'festival']:
        if reg in df.columns:
            future[reg] = 0
    forecast = m.predict(future)
    forecasted = forecast.tail(interval)['yhat'].sum()
    logging.info(f"Forecasted sales for next {interval} day(s): {forecasted:.2f}")
    return forecasted