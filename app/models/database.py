# app/models/database.py - Gestion complète de la base de données
"""
Système de gestion de base de données SQLite pour l'application de gestion de stock
Version fonctionnelle (sans POO complexe)
"""

import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
import logging
import os

# ============================================================================
# CONFIGURATION
# ============================================================================

# Chemin de la base de données
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "data" / "stock.db"
BACKUP_DIR = BASE_DIR / "data" / "backup"

# Créer les dossiers si nécessaire
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# FONCTIONS DE CONNEXION ET UTILITAIRES
# ============================================================================

def get_connection():
    """Retourne une connexion à la base de données SQLite"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Retourne des dictionnaires
    return conn

def execute_query(query, params=()):
    """Exécute une requête SQL (INSERT, UPDATE, DELETE)"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        conn.commit()
        return cursor
    except Exception as e:
        conn.rollback()
        logger.error(f"Erreur SQL: {e}")
        raise
    finally:
        conn.close()

def fetch_all(query, params=()):
    """Récupère tous les résultats d'une requête SELECT"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

def fetch_one(query, params=()):
    """Récupère un seul résultat d'une requête SELECT"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def to_dataframe(query, params=()):
    """Convertit le résultat SQL en DataFrame pandas"""
    conn = get_connection()
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df
    finally:
        conn.close()

# ============================================================================
# INITIALISATION DE LA BASE
# ============================================================================

def init_database():
    """Initialise la base de données avec toutes les tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Table catégories
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT UNIQUE NOT NULL,
        couleur TEXT DEFAULT '#3B82F6',
        date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Table fournisseurs
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS fournisseurs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        email TEXT,
        telephone TEXT,
        date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Table produits
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reference TEXT UNIQUE NOT NULL,
        nom TEXT NOT NULL,
        description TEXT,
        categorie_id INTEGER,
        fournisseur_id INTEGER,
        quantite INTEGER DEFAULT 0,
        seuil_min INTEGER DEFAULT 5,
        prix_achat REAL DEFAULT 0.0,
        prix_vente REAL DEFAULT 0.0,
        date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (categorie_id) REFERENCES categories(id),
        FOREIGN KEY (fournisseur_id) REFERENCES fournisseurs(id)
    )
    ''')
    
    # Table mouvements
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS mouvements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produit_id INTEGER NOT NULL,
        type TEXT CHECK(type IN ('entree', 'sortie')),
        quantite INTEGER NOT NULL,
        motif TEXT,
        date_mouvement TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (produit_id) REFERENCES produits(id)
    )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("✅ Base de données initialisée")
    
    # Créer des données de démo si base vide
    if is_database_empty():
        create_demo_data()

def is_database_empty():
    """Vérifie si la base de données est vide"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM produits")
    count = cursor.fetchone()[0]
    conn.close()
    return count == 0

def create_demo_data():
    """Crée des données de démo"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Catégories
    categories = [
        ("Électronique", "#FF6B6B"),
        ("Informatique", "#4ECDC4"),
        ("Bureau", "#FFD166"),
        ("Mobilier", "#06D6A0"),
        ("Câbles", "#118AB2"),
        ("Divers", "#073B4C")
    ]
    
    for nom, couleur in categories:
        cursor.execute("INSERT INTO categories (nom, couleur) VALUES (?, ?)", (nom, couleur))
    
    # Fournisseurs
    fournisseurs = [
        ("TechCorp", "contact@techcorp.com", "01 23 45 67 89"),
        ("OfficePlus", "info@officeplus.fr", "09 87 65 43 21"),
        ("ElectroWorld", "sales@electroworld.com", "05 67 89 12 34")
    ]
    
    for nom, email, tel in fournisseurs:
        cursor.execute("INSERT INTO fournisseurs (nom, email, telephone) VALUES (?, ?, ?)", (nom, email, tel))
    
    # Produits
    produits = [
        ("PROD-001", "Clavier Mécanique", "Clavier gaming RGB", 1, 1, 25, 5, 40.0, 89.99),
        ("PROD-002", "Souris Gaming", "Souris 16000 DPI", 1, 1, 18, 3, 25.0, 45.50),
        ("PROD-003", "Écran 24\"", "Écran Full HD", 2, 3, 8, 2, 150.0, 199.99),
        ("PROD-004", "Chaise Bureau", "Chaise ergonomique", 4, 2, 12, 5, 120.0, 199.99),
        ("PROD-005", "Câble HDMI 2m", "Câble haute qualité", 5, 3, 50, 10, 5.0, 12.99)
    ]
    
    for ref, nom, desc, cat_id, four_id, qte, seuil, prix_a, prix_v in produits:
        cursor.execute('''
            INSERT INTO produits 
            (reference, nom, description, categorie_id, fournisseur_id, quantite, seuil_min, prix_achat, prix_vente)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (ref, nom, desc, cat_id, four_id, qte, seuil, prix_a, prix_v))
    
    conn.commit()
    conn.close()
    logger.info("✅ Données de démo créées")

# ============================================================================
# FONCTIONS CATÉGORIES
# ============================================================================

def get_all_categories():
    """Récupère toutes les catégories"""
    return fetch_all("SELECT * FROM categories ORDER BY nom")

def get_categorie_by_id(categorie_id):
    """Récupère une catégorie par son ID"""
    return fetch_one("SELECT * FROM categories WHERE id = ?", (categorie_id,))

def add_categorie(nom, couleur="#3B82F6"):
    """Ajoute une nouvelle catégorie"""
    cursor = execute_query("INSERT INTO categories (nom, couleur) VALUES (?, ?)", (nom, couleur))
    return cursor.lastrowid

# ============================================================================
# FONCTIONS PRODUITS
# ============================================================================

def get_all_produits():
    """Récupère tous les produits avec leurs catégories et fournisseurs"""
    return fetch_all("""
        SELECT 
            p.*,
            c.nom as categorie_nom,
            c.couleur as categorie_couleur,
            f.nom as fournisseur_nom
        FROM produits p
        LEFT JOIN categories c ON p.categorie_id = c.id
        LEFT JOIN fournisseurs f ON p.fournisseur_id = f.id
        ORDER BY p.nom
    """)

def get_produits_dataframe():
    """Récupère les produits en DataFrame"""
    return to_dataframe("""
        SELECT 
            p.*,
            c.nom as categorie_nom,
            c.couleur as categorie_couleur,
            f.nom as fournisseur_nom
        FROM produits p
        LEFT JOIN categories c ON p.categorie_id = c.id
        LEFT JOIN fournisseurs f ON p.fournisseur_id = f.id
        ORDER BY p.nom
    """)

def get_produit_by_id(produit_id):
    """Récupère un produit par son ID"""
    return fetch_one("SELECT * FROM produits WHERE id = ?", (produit_id,))

def add_produit(reference, nom, description, categorie_id, fournisseur_id, quantite, seuil_min, prix_achat, prix_vente):
    """Ajoute un nouveau produit"""
    cursor = execute_query('''
        INSERT INTO produits 
        (reference, nom, description, categorie_id, fournisseur_id, quantite, seuil_min, prix_achat, prix_vente)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (reference, nom, description, categorie_id, fournisseur_id, quantite, seuil_min, prix_achat, prix_vente))
    return cursor.lastrowid

def update_stock(produit_id, quantite, type_mouvement, motif=""):
    """Met à jour le stock d'un produit et enregistre le mouvement"""
    # Mettre à jour le stock
    if type_mouvement == 'entree':
        execute_query("UPDATE produits SET quantite = quantite + ? WHERE id = ?", (quantite, produit_id))
    elif type_mouvement == 'sortie':
        execute_query("UPDATE produits SET quantite = quantite - ? WHERE id = ?", (quantite, produit_id))
    
    # Enregistrer le mouvement
    execute_query('''
        INSERT INTO mouvements (produit_id, type, quantite, motif)
        VALUES (?, ?, ?, ?)
    ''', (produit_id, type_mouvement, quantite, motif))
    
    return True

def get_produits_en_alerte():
    """Récupère les produits dont le stock est faible"""
    return fetch_all("""
        SELECT 
            p.*,
            c.nom as categorie_nom,
            f.nom as fournisseur_nom
        FROM produits p
        LEFT JOIN categories c ON p.categorie_id = c.id
        LEFT JOIN fournisseurs f ON p.fournisseur_id = f.id
        WHERE p.quantite <= p.seuil_min
        ORDER BY p.quantite ASC
    """)

# ============================================================================
# FONCTIONS STATISTIQUES
# ============================================================================

def get_statistiques():
    """Récupère les statistiques principales"""
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # Total produits
    cursor.execute("SELECT COUNT(*) FROM produits")
    stats['total_produits'] = cursor.fetchone()[0]
    
    # Valeur totale
    cursor.execute("SELECT SUM(quantite * prix_vente) FROM produits")
    stats['valeur_totale'] = cursor.fetchone()[0] or 0
    
    # Alertes
    cursor.execute("SELECT COUNT(*) FROM produits WHERE quantite <= seuil_min")
    stats['alertes'] = cursor.fetchone()[0]
    
    # Épuisés
    cursor.execute("SELECT COUNT(*) FROM produits WHERE quantite = 0")
    stats['epuises'] = cursor.fetchone()[0]
    
    # Fournisseurs
    cursor.execute("SELECT COUNT(*) FROM fournisseurs")
    stats['total_fournisseurs'] = cursor.fetchone()[0]
    
    # Catégories
    cursor.execute("SELECT COUNT(*) FROM categories")
    stats['total_categories'] = cursor.fetchone()[0]
    
    conn.close()
    return stats

# ============================================================================
# FONCTIONS FOURNISSEURS
# ============================================================================

def get_all_fournisseurs():
    """Récupère tous les fournisseurs"""
    return fetch_all("SELECT * FROM fournisseurs ORDER BY nom")

def add_fournisseur(nom, email="", telephone=""):
    """Ajoute un nouveau fournisseur"""
    cursor = execute_query(
        "INSERT INTO fournisseurs (nom, email, telephone) VALUES (?, ?, ?)",
        (nom, email, telephone)
    )
    return cursor.lastrowid

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def backup_database():
    """Crée une sauvegarde de la base"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"backup_{timestamp}.db"
    
    import shutil
    shutil.copy2(DB_PATH, backup_path)
    
    logger.info(f"✅ Backup créé: {backup_path}")
    return str(backup_path)

def export_to_csv(table_name):
    """Exporte une table en CSV"""
    df = to_dataframe(f"SELECT * FROM {table_name}")
    csv_path = f"export_{table_name}_{datetime.now().strftime('%Y%m%d')}.csv"
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    return csv_path

# Initialiser la base au chargement du module
init_database()