# app/models/auth.py - Système d'authentification intégré
import streamlit as st
import hashlib
import sqlite3
from datetime import datetime, timedelta
import re

class AuthManager:
    """Gestionnaire d'authentification qui utilise la même base de données"""
    
    def __init__(self, db_path="stock.db"):
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
        try:
            admin_hash = self.hash_password("admin123")
            cursor.execute(
                """INSERT INTO users (username, email, password_hash, full_name, role) 
                   VALUES (?, ?, ?, ?, ?)""",
                ("admin", "admin@stockflow.com", admin_hash, "Administrateur", "admin")
            )
            
            # Utilisateur demo
            demo_hash = self.hash_password("demo123")
            cursor.execute(
                """INSERT INTO users (username, email, password_hash, full_name, role) 
                   VALUES (?, ?, ?, ?, ?)""",
                ("demo", "demo@stockflow.com", demo_hash, "Utilisateur Demo", "user")
            )
            
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        
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
            """SELECT id, username, email, full_name, role, is_active 
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
                'role': user[4]
            }
            
            conn.close()
            return True, user_data
        
        self.log_attempt(username, False)
        conn.close()
        return False, "Identifiants incorrects"
    
    def register(self, username, email, password, full_name=""):
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
        
        try:
            password_hash = self.hash_password(password)
            cursor.execute(
                """INSERT INTO users (username, email, password_hash, full_name, role) 
                   VALUES (?, ?, ?, ?, ?)""",
                (username, email, password_hash, full_name, "user")
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
    """Page de connexion moderne"""
    
    # CSS pour la page de login
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        div[data-testid="stForm"] {
            background: white;
            padding: 3rem;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 450px;
            margin: 0 auto;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Centrer le contenu
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Logo et titre
        st.markdown("""
            <div style='text-align: center; margin-bottom: 2rem;'>
                <img src='https://cdn-icons-png.flaticon.com/512/869/869869.png' width='100'>
                <h1 style='color: white; margin-top: 1rem; text-shadow: 0 2px 4px rgba(0,0,0,0.2);'>
                    StockFlow Pro
                </h1>
                <p style='color: rgba(255,255,255,0.9); font-size: 1.1rem;'>
                    Système de Gestion de Stock
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Tabs pour Login / Register
        tab1, tab2 = st.tabs(["🔐 Connexion", "📝 Inscription"])
        
        auth = AuthManager()
        
        # TAB CONNEXION
        with tab1:
            with st.form("login_form", clear_on_submit=False):
                st.markdown("### Connectez-vous à votre compte")
                
                username = st.text_input(
                    "👤 Nom d'utilisateur",
                    placeholder="Entrez votre nom d'utilisateur"
                )
                
                password = st.text_input(
                    "🔒 Mot de passe",
                    type="password",
                    placeholder="Entrez votre mot de passe"
                )
                
                col_a, col_b = st.columns(2)
                with col_a:
                    remember = st.checkbox("Se souvenir de moi")
                with col_b:
                    st.markdown("[Mot de passe oublié ?](#)")
                
                submit = st.form_submit_button("🚀 Se connecter", use_container_width=True)
                
                if submit:
                    if not username or not password:
                        st.error("❌ Veuillez remplir tous les champs")
                    else:
                        success, result = auth.authenticate(username, password)
                        
                        if success:
                            st.session_state.authenticated = True
                            st.session_state.user = result
                            st.success(f"✅ Bienvenue {result['full_name'] or result['username']} !")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(f"❌ {result}")
            
            # Comptes de test
            st.info("""
                **🧪 Comptes de test :**
                - Admin : `admin` / `admin123`
                - Demo : `demo` / `demo123`
            """)
        
        # TAB INSCRIPTION
        with tab2:
            with st.form("register_form", clear_on_submit=True):
                st.markdown("### Créer un nouveau compte")
                
                new_fullname = st.text_input(
                    "👤 Nom complet",
                    placeholder="Ex: Jean Dupont"
                )
                
                new_username = st.text_input(
                    "🆔 Nom d'utilisateur",
                    placeholder="Ex: jdupont"
                )
                
                new_email = st.text_input(
                    "📧 Email",
                    placeholder="exemple@email.com"
                )
                
                new_password = st.text_input(
                    "🔒 Mot de passe",
                    type="password",
                    placeholder="Min 6 caractères, 1 lettre, 1 chiffre",
                    help="Le mot de passe doit contenir au moins 6 caractères, une lettre et un chiffre"
                )
                
                new_password_confirm = st.text_input(
                    "🔒 Confirmer le mot de passe",
                    type="password",
                    placeholder="Répétez le mot de passe"
                )
                
                accept_terms = st.checkbox("J'accepte les conditions d'utilisation")
                
                submit_register = st.form_submit_button("✨ Créer mon compte", use_container_width=True)
                
                if submit_register:
                    if not all([new_username, new_email, new_password, new_password_confirm]):
                        st.error("❌ Veuillez remplir tous les champs")
                    elif new_password != new_password_confirm:
                        st.error("❌ Les mots de passe ne correspondent pas")
                    elif not accept_terms:
                        st.error("❌ Veuillez accepter les conditions d'utilisation")
                    else:
                        success, message = auth.register(
                            new_username, 
                            new_email, 
                            new_password,
                            new_fullname
                        )
                        
                        if success:
                            st.success(f"✅ {message}")
                            st.info("Vous pouvez maintenant vous connecter avec vos identifiants")
                        else:
                            st.error(f"❌ {message}")


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