"""Constants for the vlbg_wasser integration."""

DOMAIN = "vlbg_wasser"

# API Configuration
API_BASE_URL = "https://vowis.vorarlberg.at/api/"
API_TIMEOUT = 30

# River Stations Configuration
RIVER_STATIONS = [
    {
        "name": "Bangs",
        "id": "200014",
        "river": "Rhein",
        "supports_depth": True,
        "supports_flow": True,
        "supports_temperature": False,
    },
    {
        "name": "Lustenau (Höchster Brücke)",
        "id": "200196",
        "river": "Rhein",
        "supports_depth": True,
        "supports_flow": True,
        "supports_temperature": True,
    },
    {
        "name": "Gisingen",
        "id": "200147",
        "river": "Ill",
        "supports_depth": True,
        "supports_flow": True,
        "supports_temperature": True,
    },
    {
        "name": "Beschling",
        "id": "231688",
        "river": "Ill",
        "supports_depth": True,
        "supports_flow": True,
        "supports_temperature": False,
    }
    # TODO: Populate
]

# Measurement type mappings
MEASUREMENT_TYPES = {
    "w": "depth",         # Water Depth
    "wt": "temperature",  # Water Temperature  
    "q": "flow"           # Water Flow Rate
}

# Default entity configuration
DEFAULT_SCAN_INTERVAL = 300  # 5 minutes in seconds