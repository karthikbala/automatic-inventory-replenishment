"""
Configuration Module for Automatic Inventory Replenishment System
- Stores configuration parameters, flags, and credentials
"""

# Flag to trigger API calls
default_call_api = False

# Default forecast interval (e.g., next day)
default_forecast_interval = 1

# Multipliers for min/max inventory days
min_days = 1
max_days = 3

# API credentials (to be securely set)
client_id = 'YOUR_CLIENT_ID'
client_secret = 'YOUR_CLIENT_SECRET'