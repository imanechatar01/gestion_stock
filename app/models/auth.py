import streamlit as st
import hashlib
import sqlite3
from datetime import datetime, timedelta
import re
from pathlib import Path

# Chemin de la base de données (même logique que database.py pour éviter les erreurs d'import)
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "data" / "stock.db"

class AuthManager:
    """Gestionnaire d'authentification qui utilise la même base de données"""
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.init_auth_tables()
    
    def init_auth_tables(self):
        """Ajoute les tables d'authentification à la base existante"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table des utilisateurs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                role TEXT DEFAULT 'user',
                permissions TEXT DEFAULT 'dashboard,produits,inventaire,fournisseurs,rapports,alertes',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Table des tentatives de connexion
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                success BOOLEAN,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Créer admin par défaut
        admin_hash = self.hash_password("admin123")
        try:
            cursor.execute(
                """INSERT INTO users (username, email, password_hash, full_name, role) 
                   VALUES (?, ?, ?, ?, ?)""",
                ("admin", "admin@stockflow.com", admin_hash, "Administrateur", "admin")
            )
        except sqlite3.IntegrityError:
            pass  # Admin existe déjà
        
        # Utilisateur demo
        demo_hash = self.hash_password("demo123")
        try:
            cursor.execute(
                """INSERT INTO users (username, email, password_hash, full_name, role) 
                   VALUES (?, ?, ?, ?, ?)""",
                ("demo", "demo@stockflow.com", demo_hash, "Utilisateur Demo", "user")
            )
        except sqlite3.IntegrityError:
            pass  # Demo existe déjà
        
        conn.commit()
        
        conn.close()
    
    @staticmethod
    def hash_password(password):
        """Hash SHA-256 du mot de passe"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def validate_email(email):
        """Valide le format email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password(password):
        """Valide la force du mot de passe"""
        if len(password) < 6:
            return False, "Minimum 6 caractères requis"
        if not re.search(r'[A-Za-z]', password):
            return False, "Doit contenir au moins une lettre"
        if not re.search(r'[0-9]', password):
            return False, "Doit contenir au moins un chiffre"
        return True, "OK"
    
    def check_attempts(self, username):
        """Vérifie le nombre de tentatives (max 5 en 15 min)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        limit_time = datetime.now() - timedelta(minutes=15)
        cursor.execute(
            """SELECT COUNT(*) FROM login_attempts 
               WHERE username=? AND success=0 AND timestamp > ?""",
            (username, limit_time)
        )
        
        attempts = cursor.fetchone()[0]
        conn.close()
        return attempts < 5
    
    def log_attempt(self, username, success):
        """Enregistre une tentative de connexion"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO login_attempts (username, success) VALUES (?, ?)",
            (username, success)
        )
        conn.commit()
        conn.close()
    
    def authenticate(self, username, password):
        """Authentifie un utilisateur"""
        if not self.check_attempts(username):
            return False, "Trop de tentatives. Réessayez dans 15 minutes."
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        password_hash = self.hash_password(password)
        cursor.execute(
            """SELECT id, username, email, full_name, role, is_active, permissions
               FROM users WHERE username=? AND password_hash=?""",
            (username, password_hash)
        )
        
        user = cursor.fetchone()
        
        if user and user[5]:  # is_active
            cursor.execute(
                "UPDATE users SET last_login=? WHERE id=?",
                (datetime.now(), user[0])
            )
            conn.commit()
            self.log_attempt(username, True)
            
            user_data = {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'full_name': user[3],
                'role': user[4],
                'permissions': user[6].split(',') if user[6] else []
            }
            
            conn.close()
            return True, user_data
        
        self.log_attempt(username, False)
        conn.close()
        return False, "Identifiants incorrects"
    
    def register(self, username, email, password, full_name="", permissions=None):
        """Enregistre un nouvel utilisateur"""
        if len(username) < 3:
            return False, "Nom d'utilisateur trop court (min 3)"
        
        if not self.validate_email(email):
            return False, "Email invalide"
        
        is_valid, msg = self.validate_password(password)
        if not is_valid:
            return False, msg
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Permissions par défaut si non spécifiées
        if permissions is None:
            permissions = "dashboard,produits,inventaire,fournisseurs,rapports,alertes"

        try:
            password_hash = self.hash_password(password)
            cursor.execute(
                """INSERT INTO users (username, email, password_hash, full_name, role, permissions) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (username, email, password_hash, full_name, "user", permissions)
            )
            conn.commit()
            conn.close()
            return True, "Compte créé avec succès !"
        
        except sqlite3.IntegrityError as e:
            conn.close()
            if "username" in str(e):
                return False, "Ce nom d'utilisateur existe déjà"
            return False, "Cet email est déjà utilisé"


def show_login_page():
    """Page de connexion moderne et épurée"""
    
    # CSS pour la page de login
    st.markdown("""
        <style>
        .stApp {
            background-color: #1e1b4b;
        }
        div[data-testid="stForm"] {
            background: white;
            padding: 3.5rem;
            border-radius: 24px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            max-width: 480px;
            margin: 0 auto;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .login-header h1 {
            color: white;
            font-weight: 800;
            letter-spacing: -1px;
            margin-bottom: 0.5rem;
        }
        .stButton > button {
            background-color: #2563eb !important;
            color: white !important;
            border-radius: 12px !important;
            padding: 0.75rem !important;
            font-weight: 600 !important;
            border: none !important;
            height: 50px !important;
        }
        .stTextInput > div > div > input {
            border-radius: 12px !important;
            height: 48px !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Centrer le contenu
    _, col_center, _ = st.columns([1, 2, 1])
    
    with col_center:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        
        # Logo et titre minimalist
        st.markdown("""
            <div class='login-header' style='text-align: center; margin-bottom: 3rem;'>
                <h1 style="color:white; font-size: 2.5rem; margin-bottom:0;">StockFlow Pro</h1>
                <p style='color: rgba(255,255,255,0.6); font-size: 1rem; text-transform: uppercase; letter-spacing: 2px;'>
                    Gestion de Flux Intelligent
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Formulaire de connexion
        auth = AuthManager()
        
        with st.form("login_form", clear_on_submit=False):
            st.markdown("<h3 style='text-align:center; color:#1e293b; margin-bottom:2rem;'>Connexion</h3>", unsafe_allow_html=True)
            
            username = st.text_input(
                "Nom d'utilisateur",
                placeholder="Identifiant"
            )
            
            password = st.text_input(
                "Mot de passe",
                type="password",
                placeholder="••••••••"
            )
            
            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
            
            submit = st.form_submit_button("Se connecter", use_container_width=True)
            
            if submit:
                if not username or not password:
                    st.error("Veuillez remplir tous les champs")
                else:
                    success, result = auth.authenticate(username, password)
                    
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.user = result
                        st.rerun()
                    else:
                        st.error(result)
        
        # Comptes de test discrets
        st.markdown("""
            <div style='text-align: center; margin-top: 2rem; color: rgba(255,255,255,0.4); font-size: 0.8rem;'>
                Accès Test: admin / admin123
            </div>
        """, unsafe_allow_html=True)


def check_authentication():
    """Vérifie si l'utilisateur est authentifié"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        show_login_page()
        st.stop()


def logout():
    """Déconnecte l'utilisateur"""
    st.session_state.authenticated = False
    if 'user' in st.session_state:
        del st.session_state.user
    st.rerun()