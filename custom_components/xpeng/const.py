"""Constants for the XPENG Vehicles integration."""

DOMAIN = "xpeng"

# Configuration keys
CONF_VEHICLE_NAME = "vehicle_name"
CONF_VEHICLE_MODEL = "vehicle_model"
CONF_MODE = "mode"
CONF_DATA_DIR = "data_dir"
CONF_APP_ID = "app_id"
CONF_APP_SECRET = "app_secret"
CONF_OPEN_ID = "open_id"
CONF_ACCESS_TOKEN = "access_token"

# Options keys
CONF_CLEANUP_FILES = "cleanup_processed_files"
CONF_HOME_CHARGE_ENABLED = "home_charge_enabled"
CONF_HOME_CHARGE_MIN_POWER = "home_charge_min_power"
CONF_HOME_CHARGE_MAX_POWER = "home_charge_max_power"
CONF_HOME_CHARGE_START_HOUR = "home_charge_start_hour"
CONF_HOME_CHARGE_END_HOUR = "home_charge_end_hour"
CONF_HOME_TRACKER_ENTITY = "home_tracker_entity"
CONF_RESET_ENERGY = "reset_energy"

# Modes
MODE_LOCAL_DIR = "local_dir"
MODE_API = "api"

# Models
MODEL_AUTO = "auto"
XPENG_MODELS = {
    "auto": "Auto-Detect from Vehicle Data",
    "X9": "XPENG X9 (MPV)",
    "G6": "XPENG G6 (Coupe SUV)",
    "G9": "XPENG G9 (Flagship SUV)",
    "P7": "XPENG P7 / P7i (Sedan)",
    "P7+": "XPENG P7+ (AI Sedan)",
    "G3i": "XPENG G3 / G3i (Compact SUV)",
    "M03": "XPENG MONA M03",
    "Other": "Other XPENG Model",
}

# Internal OEM Platform / Project Codes to Commercial Model Names
VMODEL_CODE_MAP = {
    "H93": "X9",
    "F97": "G6",
    "F95": "G9",
    "E28": "P7",
    "F57": "P7+",
    "F59": "MONA M03",
}

# Defaults
DEFAULT_VEHICLE_NAME = "XPENG"
DEFAULT_DATA_DIR = "/config/xpeng"
DEFAULT_CLEANUP_FILES = True
DEFAULT_HOME_CHARGE_ENABLED = True
DEFAULT_HOME_CHARGE_MIN_POWER = 8.0
DEFAULT_HOME_CHARGE_MAX_POWER = 12.0
DEFAULT_HOME_CHARGE_START_HOUR = 20
DEFAULT_HOME_CHARGE_END_HOUR = 7
DEFAULT_HOME_TRACKER_ENTITY = ""

# Platforms
PLATFORMS = ["sensor", "button"]
