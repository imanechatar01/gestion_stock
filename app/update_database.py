# app/update_database.py - Mise à jour de la structure de la base
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "data" / "stock.db"

def update_database_structure():
    """Met à jour la structure de la base de données"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("🔄 Mise à jour de la structure de la base de données...")
    
    # 1. Ajouter date_modification à produits si elle n'existe pas
    cursor.execute("PRAGMA table_info(produits)")
    colonnes_produits = [col[1] for col in cursor.fetchall()]
    
    if 'date_modification' not in colonnes_produits:
        print("➕ Ajout de 'date_modification' à la table produits...")
        try:
            cursor.execute("ALTER TABLE produits ADD COLUMN date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            print("✅ Colonne ajoutée")
        except Exception as e:
            print(f"⚠️ Impossible d'ajouter la colonne: {e}")
    
    # 2. Vérifier la structure de la table mouvements
    cursor.execute("PRAGMA table_info(mouvements)")
    colonnes_mouvements = [col[1] for col in cursor.fetchall()]
    
    print("\n📋 Structure actuelle de la table 'mouvements':")
    for col in cursor.execute("PRAGMA table_info(mouvements)").fetchall():
        print(f"  • {col[1]} ({col[2]})")
    
    # 3. Ajouter les colonnes manquantes si nécessaire
    colonnes_manquantes = []
    
    if 'quantite_avant' not in colonnes_mouvements:
        colonnes_manquantes.append('quantite_avant INTEGER')
    
    if 'quantite_apres' not in colonnes_mouvements:
        colonnes_manquantes.append('quantite_apres INTEGER')
    
    if 'utilisateur' not in colonnes_mouvements:
        colonnes_manquantes.append('utilisateur TEXT DEFAULT "system"')
    
    if 'document_ref' not in colonnes_mouvements:
        colonnes_manquantes.append('document_ref TEXT')
    
    if colonnes_manquantes:
        print(f"\n➕ Ajout de {len(colonnes_manquantes)} colonnes à la table mouvements...")
        
        # Créer une nouvelle table avec la structure complète
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS mouvements_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produit_id INTEGER NOT NULL,
            type TEXT CHECK(type IN ('entree', 'sortie', 'ajustement', 'inventaire')),
            quantite INTEGER NOT NULL,
            quantite_avant INTEGER,
            quantite_apres INTEGER,
            motif TEXT,
            utilisateur TEXT DEFAULT 'system',
            document_ref TEXT,
            date_mouvement TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (produit_id) REFERENCES produits(id)
        )
        ''')
        
        # Copier les données existantes
        try:
            # Construire dynamiquement la requête INSERT
            colonnes_existantes = [col for col in colonnes_mouvements if col != 'id']
            colonnes_str = ', '.join(colonnes_existantes)
            valeurs_str = ', '.join(['?'] * len(colonnes_existantes))
            
            cursor.execute(f"SELECT {colonnes_str} FROM mouvements")
            anciennes_donnees = cursor.fetchall()
            
            for donnee in anciennes_donnees:
                # Compléter avec valeurs par défaut pour nouvelles colonnes
                nouvelles_valeurs = list(donnee)
                # quantite_avant = quantite actuelle - quantite pour entrées, + quantite pour sorties
                # On simplifie pour l'instant
                nouvelles_valeurs.extend([None, None, 'system', ''])  # quantite_avant, quantite_apres, utilisateur, document_ref
                
                cursor.execute('''
                    INSERT INTO mouvements_new 
                    (produit_id, type, quantite, motif, date_mouvement, 
                     quantite_avant, quantite_apres, utilisateur, document_ref)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', nouvelles_valeurs)
            
            # Remplacer l'ancienne table
            cursor.execute("DROP TABLE mouvements")
            cursor.execute("ALTER TABLE mouvements_new RENAME TO mouvements")
            
            print("✅ Table mouvements mise à jour avec succès!")
            
        except Exception as e:
            print(f"⚠️ Erreur lors de la mise à jour: {e}")
            print("⚠️ Conservation de l'ancienne structure")
            cursor.execute("DROP TABLE IF EXISTS mouvements_new")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Mise à jour terminée!")

def check_current_structure():
    """Affiche la structure actuelle"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n🔍 Structure actuelle:")
    
    # Tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    for table in tables:
        print(f"\n📊 Table: {table[0]}")
        cursor.execute(f"PRAGMA table_info({table[0]})")
        for col in cursor.fetchall():
            print(f"  • {col[1]:20} {col[2]:15} {'NOT NULL' if col[3] else ''}")
    
    conn.close()

if __name__ == "__main__":
    update_database_structure()
    check_current_structure()