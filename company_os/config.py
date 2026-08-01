import json
import os
from typing import Dict, Any

DEFAULT_COMPANY = {
    "name": "Aurora Coffee Co.",
    "industry": "Specialty Coffee Roasting & Retail",
    "description": "Artisanal coffee roaster delivering ethical, single-origin coffees directly to consumers and wholesale partners.",
    "products": [
        "Single-Origin Coffee Beans",
        "Monthly Bean Subscriptions",
        "Cold Brew Craft Packs",
        "Espresso & Brewing Gear"
    ],
    "target_market": "Specialty coffee lovers, remote professionals, local cafes, and corporate offices",
    "team_size": 18,
    "location": "Seattle, WA"
}

def load_company_config(config_path: str = "company.json") -> Dict[str, Any]:
    """Load company config from JSON file, falling back to default if missing."""
    if not os.path.exists(config_path):
        save_company_config(DEFAULT_COMPANY, config_path)
        return DEFAULT_COMPANY.copy()
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_COMPANY.copy()

def save_company_config(config: Dict[str, Any], config_path: str = "company.json") -> None:
    """Save company configuration to JSON file."""
    directory = os.path.dirname(config_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
