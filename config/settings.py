APP_SETTINGS_RELATIVE_PATH = ("config", "app_settings.json")
APP_SETTINGS_SCHEMA_VERSION = 1

DEFAULT_APP_SETTINGS = {
    "schema_version": APP_SETTINGS_SCHEMA_VERSION,
    "license_id": "",
    "device_role": "",
    "last_mcd_export_dir": "",
    "last_mcd_import_dir": "",
    "display_settings": {
        "always_on_top": True,
        "transparent_mode": False,
        "font_size": 36,
        "text_color": "#FFFFFF",
        "background_color": "#000000",
        "opacity": 0.85,
    },
    "output_settings": {
        "last_output_dir": "",
        "default_format": "csv",
    },
}

VALID_DEVICE_ROLES = {"", "master", "viewer"}
