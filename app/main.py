# app/main.py - Application principale
import streamlit as st
from models import database

# Configuration de la page
st.set_page_config(
    page_title="📦 Gestion de Stock Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Charger le CSS
def load_css():
    try:
        with open("app/static/style.css", "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except:
        st.markdown("""
        <style>
            .main-header { color: #1E3A8A; }
            .metric-card { background: #f8f9fa; padding: 20px; border-radius: 10px; }
        </style>
        """, unsafe_allow_html=True)

# Sidebar Navigation
def show_sidebar():
    with st.sidebar:
        # Logo et titre
        st.image("https://cdn-icons-png.flaticon.com/512/869/869869.png", width=80)
        st.title("📦 StockFlow Pro")
        st.markdown("---")
        
        # Navigation
        page = st.radio(
            "**MENU PRINCIPAL**",
            [
                "🏠 Tableau de Bord",
                "📦 Gestion Produits", 
                "📊 Inventaire & Stock",
                "👥 Fournisseurs",
                "📈 Rapports",
                "⚙️ Paramètres"
            ]
        )
        
        st.markdown("---")
        
        # Statistiques rapides
        stats = database.get_statistiques()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Produits", stats['total_produits'])
        with col2:
            st.metric("Valeur", f"{stats['valeur_totale']:,.0f} €")
        
        st.metric("⚠️ Alertes", stats['alertes'])
        
        st.markdown("---")
        st.caption("Projet LP SIL - Gestion de Stock")
        
        return page

# Pages imports
def load_page(page_name):
    """Charge dynamiquement une page"""
    try:
        if page_name == "🏠 Tableau de Bord":
            import pages.dashboard as page
        elif page_name == "📦 Gestion Produits":
            import pages._Produits as page
        elif page_name == "📊 Inventaire & Stock":
            import pages._Inventaire as page
        elif page_name == "👥 Fournisseurs":
            import pages._Fournisseurs as page
        elif page_name == "📈 Rapports":
            import pages._Rapports as page
        elif page_name == "⚙️ Paramètres":
            import pages._Parameters as page
        else:
            st.error("Page non trouvée")
            return None
        
        return page
    except ImportError as e:
        st.error(f"Erreur de chargement de la page: {e}")
        return None

# Application principale
def main():
    # Charger le CSS
    load_css()
    
    # Navigation
    current_page = show_sidebar()
    
    # Titre principal
    st.markdown(f"<h1 style='color: #1E3A8A;'>{current_page}</h1>", unsafe_allow_html=True)
    
    # Charger et afficher la page
    page_module = load_page(current_page)
    if page_module:
        if hasattr(page_module, 'show'):
            page_module.show()
        else:
            st.error("La page n'a pas de fonction 'show()'")

# Point d'entrée
if __name__ == "__main__":
    main()