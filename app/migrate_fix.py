import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "data" / "stock.db"

def migrate():
    print(f"Migrating database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Add permissions column to users if it doesn't exist
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN permissions TEXT DEFAULT 'dashboard,produits,inventaire,fournisseurs,rapports,alertes'")
        print("Added 'permissions' column to 'users' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("'permissions' column already exists.")
        else:
            print(f"Error adding 'permissions': {e}")

    # 2. Re-create sessions table if it was deleted by mistake
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    print("Ensured 'sessions' table exists.")

    # 3. Ensure alertes_traitement table exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS alertes_traitement (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alerte_id TEXT NOT NULL,
        date_traitement TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        traite_par TEXT,
        action_prise TEXT,
        notes TEXT
    )
    ''')
    print("Ensured 'alertes_traitement' table exists.")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
