import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "ISI_TOKEN_KAMU")
OWNER_ID = 1056686795
BOT_NAME = "Adik Kecil"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILTER_FILE = os.path.join(BASE_DIR, "filters.json")
CONFESS_FILE = os.path.join(BASE_DIR, "confess_settings.json")
