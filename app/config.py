# app/config.py - Configuration de l'application
import os
from pathlib import Path

# Chemins
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"

# Base de données
DB_PATH = DATA_DIR / "stock.db"

# Paramètres application
APP_NAME = "Gestion Stock Pro"
VERSION = "1.0.0"
AUTHORS = ["IMANE", "DOHA"]

# Paramètres stock
SEUIL_ALERTE_DEFAUT = 5
DEVISE = "€"

# Créer les dossiers nécessaires
for dir_path in [DATA_DIR, STATIC_DIR]:
    dir_path.mkdir(exist_ok=True)

print(f"✅ Configuration chargée - Base: {DB_PATH}")