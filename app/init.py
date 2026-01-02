# app/init.py - Initialisation de l'application
from models import database

def init_app():
    """Initialise toute l'application"""
    print("🚀 Initialisation de l'application Gestion de Stock...")
    
    # La base est déjà initialisée dans database.py
    # via l'appel à init_database()
    
    print("✅ Application prête à être utilisée")

# Exécuter au chargement
init_app()