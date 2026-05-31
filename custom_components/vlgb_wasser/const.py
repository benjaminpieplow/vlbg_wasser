"""Constants for the vlgb_wasser integration."""

from homeassistant.components.sensor import SensorDeviceClass

DOMAIN = "vlbg_wasser"

# API Configuration
API_BASE_URL = "https://vowis.vorarlberg.at/api/"
API_BODENSEE_URL = "https://vowis.vorarlberg.at/api/see"
API_TIMEOUT = 30

# River Stations Configuration
RIVER_STATIONS = [
    # Flussgebiet: Rhein
    {"name": "Bangs",                              "id": "200014", "river": "Rhein"},
    {"name": "Lustenau (Höchster Brücke)",         "id": "200196", "river": "Rhein"},
    # Flussgebiet: Ill
    {"name": "Gisingen",                           "id": "200147", "river": "Ill"},
    {"name": "Beschling",                          "id": "231688", "river": "Ill"},
    {"name": "Lorüns-Äule",                        "id": "231662", "river": "Ill"},
    {"name": "Ludesch_HW",                         "id": "200113", "river": "Lutz"},
    {"name": "Garsella",                           "id": "200105", "river": "Lutz"},
    {"name": "Schruns (Vonbunweg)",                "id": "200048", "river": "Litz"},
    {"name": "Lorüns (Restwasser)",                "id": "200659", "river": "Alfenz"},
    {"name": "Klösterle (ÖBB)",                    "id": "200592", "river": "Alfenz"},
    {"name": "Bürs Judavollastraße",               "id": "298073", "river": "Alvier"},
    {"name": "Amerlügen",                          "id": "200501", "river": "Samina"},
    # Flussgebiet: Bregenzerach
    {"name": "Kennelbach",                         "id": "200329", "river": "Bregenzerach"},
    {"name": "Bozenau",                            "id": "231795", "river": "Bregenzerach"},
    {"name": "Egg (Wehr)",                         "id": "298080", "river": "Bregenzerach"},
    {"name": "Mellau",                             "id": "200261", "river": "Bregenzerach"},
    {"name": "Au",                                 "id": "200253", "river": "Bregenzerach"},
    {"name": "Hopfreben",                          "id": "200246", "river": "Bregenzerach"},
    {"name": "Reuthe",                             "id": "200493", "river": "Bizauerbach"},
    {"name": "Hittisau (Vorarlberger Kraftwerke AG)", "id": "200451", "river": "Bolgenach"},
    {"name": "Kälberweide",                        "id": "200584", "river": "Leckenbach"},
    {"name": "Schönenbach (Hengstig)",             "id": "200287", "river": "Subersach"},
    {"name": "Krumbach-Zwing",                     "id": "200303", "river": "Weißach"},
    {"name": "Thal (Martinsbrücke)",               "id": "200311", "river": "Rotach"},
    # Flussgebiet: Dornbirnerach
    {"name": "Lauterach",                          "id": "200410", "river": "Dornbirnerach"},
    {"name": "Hoher Steg",                         "id": "200212", "river": "Dornbirnerach"},
    {"name": "Enz",                                "id": "200204", "river": "Dornbirnerach"},
    {"name": "Schwarzach",                         "id": "200428", "river": "Schwarzach"},
    {"name": "Lustenau (Hofsteig)",                "id": "200220", "river": "Rheintalbinnenkanal"},
    {"name": "Altach (Zippersfeld)",               "id": "200469", "river": "Gießenbach"},
    {"name": "Hohenems",                           "id": "200576", "river": "Emsbach"},
    {"name": "Dornbirn/Fischbach",                 "id": "200709", "river": "Fischbach"},
    {"name": "Wolfurt",                            "id": "200717", "river": "Rickenbach"},
    # Flussgebiet: Frutz
    {"name": "Sulz",                               "id": "200642", "river": "Frutz"},
    {"name": "Laterns",                            "id": "200154", "river": "Frutz"},
    {"name": "Meiningen (Güfel)",                  "id": "200162", "river": "Ehbach"},
    {"name": "Brederis",                           "id": "200527", "river": "Ehbach"},
    # Flussgebiet: Leiblach
    {"name": "Unterhochsteg",                      "id": "200352", "river": "Leiblach"},
    # Flussgebiet: Bodenseezuflüsse
    {"name": "Hard (Mühlestrasse)",                "id": "200675", "river": "Lauterachbach"},
    {"name": "Lochau",                             "id": "200345", "river": "Ruggbach"},
    {"name": "Lustenau (Bahngasse)",               "id": "200477", "river": "Lustenauer Kanal"},
    {"name": "St.Margrethen - Rheintalbinnenkanal","id": "298042", "river": "Rheintaler Binnenkanal (CH)"},
    # Flussgebiet: Breitach
    {"name": "Tiefenbach - Breitach",              "id": "298060", "river": "Breitach"},
    # Flussgebiet: Lech
    {"name": "Lech (Tannbergbrücke)",              "id": "200378", "river": "Lech"},
    {"name": "Lech",                               "id": "200360", "river": "Zürsbach"},
]

# Measurement type mappings
MEASUREMENT_TYPES = {
    "w": "depth",
    "wt": "temperature",
    "q": "flow",
}

ALL_MEASUREMENT_TYPES = ("w", "q", "wt")

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
