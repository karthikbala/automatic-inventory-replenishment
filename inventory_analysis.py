"""
Inventory Analysis Module for Automatic Inventory Replenishment System
- Computes adjusted stock on hand (SOH)
- Calculates procurement quantities
- Ensures quantities are non-negative
- Computes min/max inventory requirements
"""

import logging


def compute_adjusted_soh(soh, open_po, open_so):
    """
    Adjusts SOH by adding open purchase orders and subtracting open sale orders.
    """
    adjusted = soh + open_po - open_so
    logging.info(f"Adjusted SOH: {adjusted}")
    return adjusted

def compute_min_max_inventory(forecast_qty, min_days, max_days):
    """
    Computes minimum and maximum inventory requirements.
    """
    min_inv = forecast_qty * min_days
    max_inv = forecast_qty * max_days
    logging.info(f"Min inventory: {min_inv}, Max inventory: {max_inv}")
    return min_inv, max_inv

def compute_procurement_quantity(adjusted_soh, max_procurement_level):
    """
    Determines procurement quantity (never negative).
    """
    qty = max(0, max_procurement_level - adjusted_soh)
    logging.info(f"Procurement quantity: {qty}")
    return qty