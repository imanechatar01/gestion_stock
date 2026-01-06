# app/models/auth.py - Système d'authentification intégré
import streamlit as st
import hashlib
import sqlite3
from datetime import datetime, timedelta
import re
import uuid

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

        # Table des sessions persistantes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
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
    
    def create_session(self, user_id):
        """Crée une nouvelle session persistante"""
        token = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(days=7)  # Valide 7 jours
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
            (token, user_id, expires_at)
        )
        conn.commit()
        conn.close()
        return token

    def delete_session(self, token):
        """Supprime une session"""
        if not token:
            return
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
        conn.close()

    def validate_token(self, token):
        """Vérifie si un token est valide et retourne l'utilisateur associé"""
        if not token:
            return None
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT u.id, u.username, u.email, u.full_name, u.role 
               FROM sessions s 
               JOIN users u ON s.user_id = u.id 
               WHERE s.token = ? AND s.expires_at > ?""",
            (token, datetime.now())
        )
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'full_name': user[3],
                'role': user[4]
            }
        return None

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
    
    def authenticate(self, username, password, remember=False):
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
            
            token = None
            if remember:
                token = self.create_session(user[0])
            
            conn.close()
            return True, (user_data, token)
        
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
        /* Import Font */
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Poppins', sans-serif;
        }

        /* Modern Background */
        .stApp {
            background-image: 
                radial-gradient(at 0% 0%, hsla(253,16%,7%,1) 0, transparent 50%), 
                radial-gradient(at 50% 0%, hsla(225,39%,30%,1) 0, transparent 50%), 
                radial-gradient(at 100% 0%, hsla(339,49%,30%,1) 0, transparent 50%);
            background-size: cover;
            background-attachment: fixed;
            background-color: #0f172a;
        }
        
        /* Glassmorphism Card */
        div[data-testid="stForm"] {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            border-radius: 24px;
            padding: 3rem;
            color: white;
        }

        /* Input Fields Styling */
        div[data-baseweb="input"] {
            background-color: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 12px !important;
            color: white !important;
        }
        
        div[data-baseweb="input"] > div {
            background-color: transparent !important;
            color: white !important;
        }
        
        /* Input Text Color */
        input {
            color: white !important;
        }

        /* Labels */
        .stMarkdown label, p, h1, h2, h3 {
            color: white !important;
        }
        
        /* Button Styling */
        button[kind="secondaryFormSubmit"] {
            background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%);
            border: none;
            color: white !important;
            font-weight: 600;
            padding: 0.75rem 1.5rem;
            border-radius: 12px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(124, 58, 237, 0.4);
        }
        
        button[kind="secondaryFormSubmit"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(124, 58, 237, 0.5);
            background: linear-gradient(90deg, #4338ca 0%, #6d28d9 100%);
        }
        
        /* Tabs Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 20px;
            background-color: transparent;
        }

        .stTabs [data-baseweb="tab"] {
            height: 50px;
            background-color: rgba(255,255,255,0.05);
            border-radius: 10px;
            color: white;
            border: none;
            padding: 0 20px;
        }

        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: rgba(255,255,255,0.2);
            font-weight: bold;
        }

        /* Checkbox */
        label[data-baseweb="checkbox"] {
            color: white !important;
        }
        
        /* Remove default Streamlit top padding */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0rem !important;
        }
        
        /* Hide header elements if present */
        header[data-testid="stHeader"] {
            background-color: transparent;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Centrer le contenu
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Logo et titre
        st.markdown("""
            <div style='text-align: center; margin-bottom: 3rem; margin-top: 2rem;'>
                <div style='
                    background: rgba(255,255,255,0.1); 
                    width: 120px; 
                    height: 120px; 
                    border-radius: 50%; 
                    display: flex; 
                    align-items: center; 
                    justify-content: center; 
                    margin: 0 auto 1.5rem auto;
                    backdrop-filter: blur(10px);
                    box-shadow: 0 8px 32px rgba(0,0,0,0.2);
                    border: 1px solid rgba(255,255,255,0.2);
                '>
                    <img src='https://cdn-icons-png.flaticon.com/512/869/869869.png' width='70' style='filter: drop-shadow(0 4px 6px rgba(0,0,0,0.1));'>
                </div>
                <h1 style='
                    color: white; 
                    font-size: 2.5rem; 
                    font-weight: 700; 
                    margin-bottom: 0.5rem;
                    background: linear-gradient(to right, #fff, #a5b4fc);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                '>
                    StockFlow Pro
                </h1>
                <p style='color: #94a3b8 !important; font-size: 1.1rem; margin-top: 0;'>
                    Système de Gestion de Stock Avancé
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
                    st.markdown("[ ](#)")
                
                submit = st.form_submit_button("🚀 Se connecter", use_container_width=True)
                
                if submit:
                    if not username or not password:
                        st.error("❌ Veuillez remplir tous les champs")
                    else:
                        success, result = auth.authenticate(username, password, remember)
                        
                        if success:
                            user_data, token = result
                            st.session_state.authenticated = True
                            st.session_state.user = user_data
                            
                            # Sauvegarder le token si "Se souvenir de moi" est coché
                            if token:
                                try:
                                    st.query_params["token"] = token
                                except AttributeError:
                                    st.experimental_set_query_params(token=token)
                            
                            st.success(f"✅ Bienvenue {user_data['full_name'] or user_data['username']} !")
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
    
    # Vérification du token si non connecté
    if not st.session_state.authenticated:
        # Compatibilité Streamlit < 1.30
        try:
            query_params = st.query_params
            token = query_params.get("token")
        except AttributeError:
            query_params = st.experimental_get_query_params()
            token = query_params.get("token", [None])[0]
        
        if token:
            auth = AuthManager()
            user = auth.validate_token(token)
            if user:
                st.session_state.authenticated = True
                st.session_state.user = user
                st.rerun()
    
    if not st.session_state.authenticated:
        show_login_page()
        st.stop()


def logout():
    """Déconnecte l'utilisateur"""
    # Supprimer le token si présent
    try:
        # Nouveau Streamlit
        token = st.query_params.get("token")
        if token:
            auth = AuthManager()
            auth.delete_session(token)
            if "token" in st.query_params:
                del st.query_params["token"]
    except AttributeError:
        # Ancien Streamlit
        params = st.experimental_get_query_params()
        token = params.get("token", [None])[0]
        if token:
            auth = AuthManager()
            auth.delete_session(token)
            st.experimental_set_query_params()  # Clear all params
            
    st.session_state.authenticated = False
    if 'user' in st.session_state:
        del st.session_state.user
    st.rerun()