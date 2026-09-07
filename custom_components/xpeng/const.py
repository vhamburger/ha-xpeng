"""Constants for the XPENG Vehicles integration."""

DOMAIN = "xpeng"

# Configuration keys
CONF_VEHICLE_NAME = "vehicle_name"
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

# Modes
MODE_LOCAL_DIR = "local_dir"
MODE_API = "api"

# Defaults
DEFAULT_VEHICLE_NAME = "XPENG"
DEFAULT_DATA_DIR = "/config/xpeng"
DEFAULT_CLEANUP_FILES = True
DEFAULT_HOME_CHARGE_ENABLED = True
DEFAULT_HOME_CHARGE_MIN_POWER = 8.0
DEFAULT_HOME_CHARGE_MAX_POWER = 12.0
DEFAULT_HOME_CHARGE_START_HOUR = 20
DEFAULT_HOME_CHARGE_END_HOUR = 7

# Platforms
PLATFORMS = ["sensor", "button"]
