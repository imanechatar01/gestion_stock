import streamlit as st
from models.auth import AuthManager

def show():
    """Page d'inscription simplifiée avec le même design que la connexion"""
    
    # CSS identique à la page de login (auth.py)
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
        .register-header h1 {
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
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Titre
        st.markdown("""
            <div class='register-header' style='text-align: center; margin-bottom: 2rem;'>
                <h1 style="color:white; font-size: 2.5rem; margin-bottom:0;">StockFlow Pro</h1>
                <p style='color: rgba(255,255,255,0.6); font-size: 0.9rem; text-transform: uppercase; letter-spacing: 2px;'>
                    Créer votre compte employé
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        auth = AuthManager()
        
        with st.form("register_form"):
            st.markdown("<h3 style='text-align:center; color:#1e293b; margin-bottom:2rem;'>Inscription</h3>", unsafe_allow_html=True)
            
            full_name = st.text_input("Nom complet", placeholder="Jean Dupont")
            email = st.text_input("Email professionnelle", placeholder="jean@stock.com")
            username = st.text_input("Nom d'utilisateur", placeholder="jdupont")
            password = st.text_input("Mot de passe", type="password", placeholder="••••••••")
            
            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
            
            submit = st.form_submit_button("S'enregistrer", use_container_width=True)
            
            if submit:
                if not username or not email or not password:
                    st.error("Veuillez remplir les champs obligatoires")
                else:
                    success, msg = auth.register(
                        username=username,
                        email=email,
                        password=password,
                        full_name=full_name,
                        role="user"  # Par défaut, un utilisateur qui s'inscrit lui-même est un simple user
                    )
                    if success:
                        st.success("Compte créé avec succès ! Vous pouvez maintenant vous connecter.")
                        st.balloons()
                    else:
                        st.error(msg)
        
        # Retour à la connexion
        st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
        if st.button("← Retour à la connexion", use_container_width=True):
            if 'mode' in st.session_state:
                del st.session_state.mode
            st.rerun()
