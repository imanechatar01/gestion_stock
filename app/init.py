# app/init.py - Initialisation de l'application
from .config import DB_PATH
import sqlite3

def init_application():
    """Initialise toute l'application"""
    print("🚀 Initialisation de l'application...")
    
    # Initialiser la base de données
    init_database()
    
    # Créer des données de démo si base vide
    if is_database_empty():
        create_demo_data()
    
    print("✅ Application prête !")

def init_database():
    """Crée les tables si elles n'existent pas"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table produits
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reference TEXT UNIQUE NOT NULL,
        nom TEXT NOT NULL,
        description TEXT,
        categorie TEXT DEFAULT 'Divers',
        quantite INTEGER DEFAULT 0 CHECK(quantite >= 0),
        seuil_min INTEGER DEFAULT 5 CHECK(seuil_min >= 0),
        prix_achat REAL DEFAULT 0.0,
        prix_vente REAL DEFAULT 0.0,
        fournisseur_id INTEGER,
        date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Table fournisseurs
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS fournisseurs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        email TEXT,
        telephone TEXT,
        adresse TEXT,
        date_inscription TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Table mouvements
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS mouvements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produit_id INTEGER NOT NULL,
        type TEXT CHECK(type IN ('entree', 'sortie', 'ajustement')),
        quantite INTEGER NOT NULL,
        motif TEXT,
        utilisateur TEXT,
        date_mouvement TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (produit_id) REFERENCES produits(id)
    )
    ''')
    
    # Table utilisateurs (simple)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS utilisateurs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Base de données initialisée")

def is_database_empty():
    """Vérifie si la base de données est vide"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM produits")
    count = cursor.fetchone()[0]
    
    conn.close()
    return count == 0

def create_demo_data():
    """Crée des données de démo pour tester"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Fournisseurs de démo
    fournisseurs = [
        ("TechCorp", "contact@techcorp.com", "01 23 45 67 89", "Paris"),
        ("OfficePlus", "info@officeplus.fr", "09 87 65 43 21", "Lyon"),
        ("ElectroWorld", "sales@electroworld.com", "05 67 89 12 34", "Marseille")
    ]
    
    for fournisseur in fournisseurs:
        cursor.execute(
            "INSERT INTO fournisseurs (nom, email, telephone, adresse) VALUES (?, ?, ?, ?)",
            fournisseur
        )
    
    # Produits de démo
    produits = [
        ("PROD-001", "Clavier Mécanique", "Clavier gaming RGB", "Électronique", 25, 5, 40.0, 89.99, 1),
        ("PROD-002", "Souris Gaming", "Souris 16000 DPI", "Électronique", 18, 3, 25.0, 45.50, 1),
        ("PROD-003", "Écran 24\"", "Écran Full HD", "Informatique", 8, 2, 150.0, 199.99, 3),
        ("PROD-004", "Chaise Bureau", "Chaise ergonomique", "Mobilier", 12, 5, 120.0, 199.99, 2),
        ("PROD-005", "Câble HDMI", "Câble 2m haute qualité", "Câbles", 50, 10, 5.0, 12.99, 3),
        ("PROD-006", "Disque SSD 1TB", "SSD NVMe", "Informatique", 15, 4, 60.0, 89.99, 1),
        ("PROD-007", "Casque Audio", "Casque sans fil", "Électronique", 22, 6, 45.0, 79.99, 1),
        ("PROD-008", "Laptop 15\"", "Laptop gaming", "Informatique", 5, 2, 800.0, 1199.99, 3)
    ]
    
    for produit in produits:
        cursor.execute('''
            INSERT INTO produits 
            (reference, nom, description, categorie, quantite, seuil_min, prix_achat, prix_vente, fournisseur_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', produit)
    
    # Utilisateur admin de démo
    cursor.execute(
        "INSERT INTO utilisateurs (username, password, role) VALUES (?, ?, ?)",
        ("admin", "admin123", "admin")
    )
    
    conn.commit()
    conn.close()
    print("✅ Données de démo créées")

# Exécuter l'initialisation au chargement du module
init_application()