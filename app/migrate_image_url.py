import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "data" / "stock.db"

def migrate():
    print(f"Connexion à {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("Ajout de la colonne 'image_url' à la table 'produits'...")
        cursor.execute("ALTER TABLE produits ADD COLUMN image_url TEXT")
        conn.commit()
        print("✅ Migration réussie !")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("ℹ️ La colonne 'image_url' existe déjà.")
        else:
            print(f"❌ Erreur lors de la migration : {e}")
    except Exception as e:
        print(f"❌ Erreur inattendue : {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
