"""Constants for the vlgb_wasser integration."""

from homeassistant.components.sensor import SensorDeviceClass

DOMAIN = "vlbg_wasser"

# API Configuration
API_BASE_URL = "https://vowis.vorarlberg.at/api/"
API_BODENSEE_URL = "https://vowis.vorarlberg.at/api/see"
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
    },
]

# Measurement type mappings
MEASUREMENT_TYPES = {
    "w": "depth",
    "wt": "temperature",
    "q": "flow",
}

# Default entity configuration
DEFAULT_SCAN_INTERVAL = 300  # 5 minutes in seconds

BODENSEE_SENSORS = [
    {"key": "bodensee_pegelnullpunkt",  "path": ["pegelnullpunkt"],              "unit": "m",   "device_class": None,                             "icon": "mdi:altimieter"},
    {"key": "bodensee_luftfeuchte",     "path": ["luftfeuchte", "wert"],         "unit": "%",   "device_class": SensorDeviceClass.HUMIDITY,       "icon": "mdi:water-percent"},
    {"key": "bodensee_lufttemp",        "path": ["lufttemperatur", "wert"],      "unit": "°C",  "device_class": SensorDeviceClass.TEMPERATURE,    "icon": "mdi:thermometer"},
    {"key": "bodensee_wasserstand",     "path": ["wasserstand", "wert"],         "unit": "cm",  "device_class": SensorDeviceClass.DISTANCE,       "icon": "mdi:wave"},
    {"key": "bodensee_wasser_temp_05",  "path": ["wtMilli05", "wert"],           "unit": "°C",  "device_class": SensorDeviceClass.TEMPERATURE,    "icon": "mdi:thermometer-chevron-down"},
    {"key": "bodensee_wasser_temp_25",  "path": ["wtMilli25", "wert"],           "unit": "°C",  "device_class": SensorDeviceClass.TEMPERATURE,    "icon": "mdi:thermometer-chevron-down"},
    {"key": "bodensee_wind_gesw",       "path": ["windgeschwindigkeit", "wert"], "unit": "m/s", "device_class": SensorDeviceClass.WIND_SPEED,     "icon": "mdi:weather-windy"},
    {"key": "bodensee_wind_richtung",   "path": ["windrichtung", "wert"],        "unit": "°",   "device_class": SensorDeviceClass.WIND_DIRECTION, "icon": "mdi:compass"},
    {"key": "bodensee_wind_boe",        "path": ["windboe", "wert"],             "unit": "m/s", "device_class": SensorDeviceClass.WIND_SPEED,     "icon": "mdi:tailwind"},
    {"key": "bodensee_stand_nied",      "path": ["nnw", "wert"],                 "unit": "cm",  "device_class": SensorDeviceClass.DISTANCE,       "icon": "mdi:wave-arrow-down"},
    {"key": "bodensee_stand_hoch",      "path": ["hhw", "wert"],                 "unit": "cm",  "device_class": SensorDeviceClass.DISTANCE,       "icon": "mdi:wave-arrow-up"},
]
