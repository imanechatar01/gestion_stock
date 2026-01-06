import sqlite3
import os

# Use 'stock.db' in the current directory (where auth.py looks by default)
DB_PATH = os.path.join(os.path.dirname(__file__), 'stock.db')

def migrate():
    print(f"Migrating database at {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print("Database not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if permissions column exists
    try:
        cursor.execute("SELECT permissions FROM users LIMIT 1")
        print("Column 'permissions' already exists.")
    except sqlite3.OperationalError:
        print("Adding 'permissions' column...")
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN permissions TEXT DEFAULT 'dashboard,produits,inventaire,fournisseurs,rapports,alertes'")
            conn.commit()
            print("Column added.")
        except Exception as e:
            print(f"Error adding column: {e}")
            return
            
        # Update admin permissions
        print("Updating admin permissions...")
        admin_perms = 'dashboard,produits,inventaire,fournisseurs,rapports,alertes,parametres,utilisateurs'
        cursor.execute("UPDATE users SET permissions = ? WHERE role = 'admin'", (admin_perms,))
        conn.commit()
        print("Migration successful.")
        
    conn.close()

if __name__ == "__main__":
    migrate()
