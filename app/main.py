# app/main.py - Version sécurisée avec authentification
import streamlit as st
from models import database
from models.auth import check_authentication, logout

st.set_page_config(
    page_title="📦 Gestion de Stock Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# VÉRIFICATION DE L'AUTHENTIFICATION
# Cette ligne bloque l'accès si l'utilisateur n'est pas connecté
check_authentication()

# Chargement du CSS adaptatif
def load_css():
    from pathlib import Path
    css_dir = Path(__file__).parent / "static" / "css"
    
    # Charger style.css
    try:
        style_path = css_dir / "style.css"
        with open(style_path, encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except Exception as e:
        # Fallback CSS si le fichier n'existe pas
        st.markdown("""<style>
        [data-theme="dark"] .stApp { background: #0f172a; color: #f1f5f9; }
        [data-theme="dark"] h1, [data-theme="dark"] h2, [data-theme="dark"] h3 { color: #f1f5f9; }
        </style>
        """, unsafe_allow_html=True)
        
    # Charger theme.css
    try:
        theme_path = css_dir / "theme.css"
        with open(theme_path, encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except Exception as e:
        pass

# Charger le CSS
load_css()

def show_sidebar():
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/869/869869.png", width=80)
        st.title("📦 StockFlow Pro")
        
        # Informations utilisateur
        if 'user' in st.session_state:
            user = st.session_state.user
            st.markdown(f"""
                <div style='background: rgba(255,255,255,0.1); 
                            padding: 1rem; 
                            border-radius: 10px; 
                            margin-bottom: 1rem;
                            text-align: center;'>
                    <p style='margin: 0; color: rgba(255,255,255,0.7); font-size: 0.8rem;'>
                        Connecté en tant que
                    </p>
                    <h4 style='margin: 0.5rem 0; color: white;'>
                        {user.get('full_name') or user['username']}
                    </h4>
                    <span style='background: {'#4F46E5' if user['role'] == 'admin' else '#06B6D4'}; 
                                 padding: 0.25rem 0.75rem; 
                                 border-radius: 20px; 
                                 font-size: 0.75rem;
                                 color: white;'>
                        {'👑 Admin' if user['role'] == 'admin' else '👤 Utilisateur'}
                    </span>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Menu principal
        menu_items = [
            "🏠 Tableau de Bord",
            "📦 Gestion Produits", 
            "📊 Inventaire & Stock",
            "👥 Fournisseurs",
            "📈 Rapports",
        ]
        
        # Ajouter Paramètres seulement pour les admins
        if st.session_state.user.get('role') == 'admin':
            menu_items.append("⚙️ Paramètres")
            menu_items.append("👥 Gestion Utilisateurs")
            
        page = st.radio(
            "**MENU PRINCIPAL**",
            menu_items,
            key="main_navigation"
        )
        
        st.markdown("---")
        
        # Statistiques
        try:
            stats = database.get_statistiques()
            col1, col2 = st.columns(2)
            with col1: 
                st.metric("Produits", stats['total_produits'])
            with col2: 
                st.metric("Valeur", f"{stats['valeur_totale']:,.0f} DH")
            st.metric("⚠️ Alertes", stats['alertes'])
        except Exception as e:
            st.error(f"Erreur stats: {e}")
        
        st.markdown("---")
        
        # Bouton de déconnexion
        if st.button("🚪 Déconnexion", use_container_width=True):
            logout()
        
        st.caption("Projet LP SIL - Version 1.0")
        
        return page

def main():
    current_page = show_sidebar()
    
    # Titre principal
    st.title(current_page)
    
    # Chargement des pages
    try:
        if current_page == "🏠 Tableau de Bord":
            from views._dashboard import show
            show()
            
        elif current_page == "📦 Gestion Produits":
            from views._Produits import show
            show()
            
        elif current_page == "📊 Inventaire & Stock":
            from views._Inventaire import show
            show()
            
        elif current_page == "👥 Fournisseurs":
            from views._Fournisseurs import show
            show()
            
        elif current_page == "📈 Rapports":
            from views._Rapports import show
            show()
            
        elif current_page == "⚙️ Paramètres":
            # Vérifier si admin
            if st.session_state.user.get('role') != 'admin':
                st.error("❌ Accès refusé : réservé aux administrateurs")
            else:
                from views._Parameters import show
                show()
        
        elif current_page == "👥 Gestion Utilisateurs":
            # Vérifier si admin
            if st.session_state.user.get('role') != 'admin':
                st.error("❌ Accès refusé : réservé aux administrateurs")
            else:
                from views._Utilisateurs import show
                show()
            
    except ImportError as e:
        st.error(f"❌ Erreur d'import: {e}")
        st.code(f"""Vérifiez que le fichier existe et contient:
1. Le fichier views/{current_page.replace(' ', '_')}.py existe
2. Il a une fonction 'def show():'
3. Pas d'erreur de syntaxe dans le fichier""")
        
    except Exception as e:
        st.error(f"❌ Erreur d'exécution: {e}")
        import traceback
        st.code(traceback.format_exc())


if __name__ == "__main__":
    main()