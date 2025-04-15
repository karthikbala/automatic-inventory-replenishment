"""
Main Application Entry Point for Automatic Inventory Replenishment System
- CLI interface for user input
- Orchestrates data processing, forecasting, inventory analysis, and API calls
- Configures logging for console and file output
"""

import logging
import pandas as pd
from data_processing import load_and_validate_csv, preprocess_data, forecast_sales
from inventory_analysis import compute_adjusted_soh, compute_min_max_inventory, compute_procurement_quantity
from api_handler import get_access_token, place_purchase_order
import config


def setup_logging():
    """
    Sets up logging to console and file (app.log).
    """
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s [%(levelname)s] %(message)s',
                        handlers=[
                            logging.FileHandler('app.log'),
                            logging.StreamHandler()
                        ])


def main():
    """
    Main workflow: Per-SKU data processing, forecasting, inventory analysis, and API call.
    """
    setup_logging()
    logging.info('Starting Inventory Replenishment System (Per-SKU)')

    # For test: use sample_input.csv, interval=1, call_api=True
    csv_path = 'sample_input.csv'
    forecast_interval = 1
    call_api = True

    df = load_and_validate_csv(csv_path)
    if df.empty:
        logging.error("No valid data to process.")
        return

    # Ensure numeric columns are correct type
    for col in ['Sales', 'SOH', 'Open_PO', 'Open_SO', 'Min_Days', 'Max_Days']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    sku_list = df['SKU'].unique()
    logging.info(f"Processing {len(sku_list)} unique SKUs: {sku_list}")

    summary_rows = []

    for sku in sku_list:
        sku_df = df[df['SKU'] == sku].copy()
        if sku_df.empty:
            logging.warning(f"No data for SKU {sku}, skipping.")
            continue
        processed_df = preprocess_data(sku_df)
        forecast_qty = forecast_sales(processed_df, interval=forecast_interval)

        # Use last row for inventory values for this SKU
        last = sku_df.iloc[-1]
        soh = float(last['SOH'])
        open_po = float(last['Open_PO'])
        open_so = float(last['Open_SO'])
        min_days = float(last['Min_Days'])
        max_days = float(last['Max_Days'])

        min_inv, max_inv = compute_min_max_inventory(forecast_qty, min_days, max_days)
        adjusted_soh = compute_adjusted_soh(soh, open_po, open_so)

        # Only procure if adjusted_soh < min_inventory
        if adjusted_soh < min_inv:
            procurement_qty = max(0, max_inv - adjusted_soh)
            procurement_reason = f"Adjusted SOH {adjusted_soh} < Min Inventory {min_inv}"
        else:
            procurement_qty = 0
            procurement_reason = f"Adjusted SOH {adjusted_soh} >= Min Inventory {min_inv}"        

        # Collect summary info for this SKU
        summary_rows.append({
            'SKU': sku,
            'Forecast': round(forecast_qty, 2),
            'SOH': soh,
            'Adjusted SOH': round(adjusted_soh, 2),
            'Open PO': open_po,
            'Open SO': open_so,
            'Procurement Qty': round(procurement_qty, 2)
        })

        logging.info(f"SKU: {sku} | Forecast: {forecast_qty:.2f} | SOH: {soh} | Open_PO: {open_po} | Open_SO: {open_so} | Min_Days: {min_days} | Max_Days: {max_days} | Min_Inv: {min_inv:.2f} | Max_Inv: {max_inv:.2f} | Adjusted SOH: {adjusted_soh:.2f} | Procurement Qty: {procurement_qty} | Reason: {procurement_reason}")

        if call_api and procurement_qty > 0:
            token = get_access_token('dummy_id', 'dummy_secret')
            payload = {
                'sku': sku,
                'quantity': procurement_qty,
                'company': last['Company'],
                'warehouse': last['Warehouse']
            }
            place_purchase_order('https://dummy.api/purchase_order', token, payload)
        else:
            logging.info(f"No procurement needed or API call not requested for SKU {sku}.")

    # Log summary table (pretty print)
    used_fallback = False
    try:
        from rich.console import Console
        from rich.table import Table
        console = Console()
        table = Table(title="Summary Table", show_lines=True)
        columns = ['SKU', 'Forecast', 'SOH', 'Adjusted SOH', 'Open PO', 'Open SO', 'Procurement Qty']
        for col in columns:
            table.add_column(col, style="bold")
        for r in summary_rows:
            table.add_row(
                str(r['SKU']), str(r['Forecast']), str(r['SOH']), str(r['Adjusted SOH']), str(r['Open PO']), str(r['Open SO']), str(r['Procurement Qty'])
            )
        # Print to stdout directly (not logging)
        console.print(table)
        logging.info("Summary Table printed above using rich.")
    except ImportError:
        try:
            from tabulate import tabulate
            table = tabulate(
                [
                    [r['SKU'], r['Forecast'], r['SOH'], r['Adjusted SOH'], r['Open PO'], r['Open SO'], r['Procurement Qty']]
                    for r in summary_rows
                ],
                headers=['SKU', 'Forecast', 'SOH', 'Adjusted SOH', 'Open PO', 'Open SO', 'Procurement Qty'],
                tablefmt='fancy_grid'
            )
            logging.info("\nSummary Table (fancy_grid):\n" + table)
        except ImportError:
            # Fallback manual formatting
            used_fallback = True
            header = f"{'SKU':<10} {'Forecast':<10} {'SOH':<10} {'Adj SOH':<12} {'Open PO':<10} {'Open SO':<10} {'Proc Qty':<12}"
            logging.info("\nSummary Table:\n" + header)
            for r in summary_rows:
                row = f"{r['SKU']:<10} {r['Forecast']:<10} {r['SOH']:<10} {r['Adjusted SOH']:<12} {r['Open PO']:<10} {r['Open SO']:<10} {r['Procurement Qty']:<12}"
                logging.info(row)
    if used_fallback:
        logging.info("Install 'rich' or 'tabulate' for prettier summary tables.")

    logging.info("Workflow complete.")

if __name__ == '__main__':
    main()