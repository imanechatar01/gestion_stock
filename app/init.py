# app/init.py - Initialisation de l'application
from .config import DB_PATH, DATA_DIR, BACKUP_DIR
import sqlite3
import os

print("=" * 50)
print("🚀 INITIALISATION DU SYSTÈME DE GESTION DE STOCK")
print("=" * 50)

def initialiser_application():
    """Initialise toute l'application"""
    
    # 1. Vérifier la structure
    print("📁 Vérification de la structure des dossiers...")
    for dossier in [DATA_DIR, BACKUP_DIR]:
        if not dossier.exists():
            dossier.mkdir(parents=True, exist_ok=True)
            print(f"  ✅ Créé: {dossier}")
    
    # 2. Initialiser la base de données
    print("\n🗃️  Initialisation de la base de données...")
    from .models.database import init_database, create_demo_data
    init_database()
    
    # 3. Vérifier les données de démo
    print("\n📊 Vérification des données...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Compter les produits
    cursor.execute("SELECT COUNT(*) FROM produits")
    nb_produits = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM categories")
    nb_categories = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM fournisseurs")
    nb_fournisseurs = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"  📦 Produits: {nb_produits}")
    print(f"  🏷️  Catégories: {nb_categories}")
    print(f"  👥 Fournisseurs: {nb_fournisseurs}")
    
    # 4. Message de succès
    print("\n" + "=" * 50)
    print("✅ APPLICATION PRÊTE À L'EMPLOI !")
    print("=" * 50)
    print("\nInstructions:")
    print("1. Lancez l'application: streamlit run app/main.py")
    print("2. Accédez à: http://localhost:8501")
    print("3. Identifiants de démo:")
    print("   - Utilisateur: admin")
    print("   - Mot de passe: admin123")
    print("=" * 50)

# Exécuter l'initialisation si ce fichier est exécuté directement
if __name__ == "__main__":
    initialiser_application()
else:
    # Exécuter automatiquement quand importé
    initialiser_application()