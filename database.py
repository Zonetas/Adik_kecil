import json
import os
from config import FILTER_FILE, CONFESS_FILE

def load_json(file):
    if not os.path.exists(file):
        return {}
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

filters_db = load_json(FILTER_FILE)
confess_settings = load_json(CONFESS_FILE)
confess_cooldown = {}