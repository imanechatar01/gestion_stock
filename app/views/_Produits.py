# app/pages/_Produits.py
import streamlit as st
from models import database
import os
from pathlib import Path
import base64
import shutil

# Chemin de stockage des images
BASE_DIR = Path(__file__).parent.parent
IMG_DIR = BASE_DIR / "static" / "img" / "products"
IMG_DIR.mkdir(parents=True, exist_ok=True)

def get_image_base64(image_path):
    """Convertit une image en base64 pour l'affichage HTML"""
    if not image_path:
        return None
    
    full_path = BASE_DIR / image_path
    if not full_path.exists():
        return None
        
    try:
        with open(full_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except Exception:
        return None

def save_uploaded_image(uploaded_file, product_ref):
    """Sauvegarde l'image uploadée"""
    if uploaded_file is None:
        return None
        
    # Extension du fichier
    file_ext = os.path.splitext(uploaded_file.name)[1]
    filename = f"{product_ref}{file_ext}"
    
    # Chemin relatif pour la DB
    db_path = f"static/img/products/{filename}"
    
    # Chemin absolu pour la sauvegarde
    save_path = IMG_DIR / filename
    
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    return db_path

# =======================
# CSS personnalisé & Système de Design
# =======================
def show():
    # CSS Premium pour la gestion des produits
    st.markdown("""
    <style>
    /* Main Layout */
    .product-header-section {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 25px;
        padding-bottom: 15px;
        border-bottom: 1px solid #E2E8F0;
    }
    
    /* Search & Filter Bar */
    .control-bar {
        background: white;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin-bottom: 25px;
        border: 1px solid #F1F5F9;
    }
    
    /* Product Card Styling */
    .card-container {
        perspective: 1000px;
    }
    
    .produit-card-premium {
        background: white;
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid #F1F5F9;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    
    .produit-card-premium:hover {
        transform: translateY(-8px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.1);
        border-color: #E2E8F0;
    }
    
    /* Image Container - Slightly larger for 3-column layout */
    .img-wrapper {
        width: 100%;
        height: 180px;
        background: #F8FAFC;
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 5px;
        border-bottom: 1px solid #F1F5F9;
    }
    
    /* Badges */
    .badge-cat {
        position: absolute;
        top: 8px;
        right: 8px;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 9px;
        font-weight: 700;
        text-transform: uppercase;
        color: white;
        z-index: 2;
    }
    
    .badge-stock {
        position: absolute;
        bottom: 8px;
        left: 8px;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 10px;
        font-weight: 600;
        background: white;
        border: 1px solid #E2E8F0;
        z-index: 3;
    }
    
    /* Stock Colors */
    .stock-sain { color: #10B981; }
    .stock-faible { color: #F59E0B; }
    .stock-critique { color: #EF4444; }
    
    /* Content - Centered */
    .card-content {
        padding: 15px 10px;
        flex-grow: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        background: white;
    }
    
    /* Custom Streamlit Button Styling (Direct injection) */
    div.stButton > button[kind="primary"] {
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    div.stButton > button[kind="primary"]:hover {
        background-color: #1D4ED8 !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
        transform: translateY(-1px);
    }
    
    .card-title {
        color: #4338CA; /* Deep Indigo */
        font-size: 14px;
        font-weight: 700;
        margin-bottom: 4px;
        line-height: 1.2;
    }
    
    .card-ref {
        color: #94A3B8;
        font-size: 10px;
        font-weight: 500;
        margin-bottom: 10px;
    }
    
    .card-footer {
        margin-top: auto;
        width: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        padding-top: 10px;
        border-top: 1px solid #F8FAFC;
    }
    
    .card-price {
        color: #1E293B;
        font-size: 18px;
        font-weight: 800;
    }
    
    .price-unit {
        font-size: 11px;
        color: #64748B;
        margin-left: 2px;
    }

    </style>
    """, unsafe_allow_html=True)

    # Session State
    if 'refresh' not in st.session_state:
        st.session_state['refresh'] = False

    # Tabs
    tab1, tab2 = st.tabs(["Catalogue Produits", "Nouvel Article"])

    # =======================
    # TAB 1: LISTE (CARDS MODERNE)
    # =======================
    with tab1:
        # Zone de recherche et filtres
        st.markdown("<div class='control-bar'>", unsafe_allow_html=True)
        fc1, fc2, fc3 = st.columns([2, 1, 1])
        
        with fc1:
            search_term = st.text_input("Recherche rapide", placeholder="Nom ou référence du produit...")
        
        with fc2:
            all_cats = database.get_all_categories()
            cat_options = ["Toutes les catégories"] + [c['nom'] for c in all_cats]
            selected_cat = st.selectbox("Catégorie", options=cat_options)
            
        with fc3:
            sort_options = ["Alphabétique", "Stock croissant", "Stock décroissant", "Prix croissant", "Prix décroissant"]
            sort_by = st.selectbox("Trier par", options=sort_options)
        st.markdown("</div>", unsafe_allow_html=True)

        try:
            produits = database.get_all_produits()
            
            # FILTRAGE
            if search_term:
                term = search_term.lower()
                produits = [p for p in produits if term in p['nom'].lower() or term in p['reference'].lower()]
            
            if selected_cat != "Toutes les catégories":
                produits = [p for p in produits if p['categorie_nom'] == selected_cat]
                
            # TRI
            if sort_by == "Alphabétique":
                produits = sorted(produits, key=lambda x: x['nom'].lower())
            elif sort_by == "Stock croissant":
                produits = sorted(produits, key=lambda x: x['quantite'])
            elif sort_by == "Stock décroissant":
                produits = sorted(produits, key=lambda x: x['quantite'], reverse=True)
            elif sort_by == "Prix croissant":
                produits = sorted(produits, key=lambda x: x['prix_vente'])
            elif sort_by == "Prix décroissant":
                produits = sorted(produits, key=lambda x: x['prix_vente'], reverse=True)

            if produits:
                cols_per_row = 3 # Retour à 3 colonnes pour une meilleure visibilité
                for i in range(0, len(produits), cols_per_row):
                    rows = st.columns(cols_per_row, gap="medium")
                    for j, p in enumerate(produits[i:i+cols_per_row]):
                        with rows[j]:
                            # Préparation des badges de stock
                            stock_status = "stock-sain"
                            stock_label = "En Stock"
                            if p['quantite'] <= 0:
                                stock_status = "stock-critique"
                                stock_label = "Rupture"
                            elif p['quantite'] <= p['seuil_min']:
                                stock_status = "stock-faible"
                                stock_label = "Faible"
                            
                            # Rendu de la carte
                            img_base64 = get_image_base64(p.get('image_url'))
                            img_content = f'<img src="data:image/png;base64,{img_base64}" style="width: 100%; height: 100%; object-fit: cover; transition: transform 0.3s ease;">' if img_base64 else f'<span style="font-size: 60px; opacity: 0.1; color:{p["categorie_couleur"]}">P</span>'
                            
                            st.markdown(f"""
                            <div class="produit-card-premium">
                                <div class="img-wrapper">
                                    <div class="badge-cat" style="background: {p['categorie_couleur'] or '#3B82F6'}">{p['categorie_nom'] or 'Général'}</div>
                                    {img_content}
                                    <div class="badge-stock {stock_status}">
                                        {stock_label}: {p['quantite']}
                                    </div>
                                </div>
                                <div class="card-content">
                                    <div class="card-title">{p['nom']}</div>
                                    <div class="card-ref">{p['reference']}</div>
                                    <div class="card-footer">
                                        <div class="card-price">{p['prix_vente']}<span class="price-unit">DH</span></div>
                                        <div style="font-size: 10px; color: #94A3B8; font-weight: 500;">{p['fournisseur_nom'] or '—'}</div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Bouton de suppression petit, gris et sans icone
                            _, btn_col, _ = st.columns([1, 2, 1])
                            with btn_col:
                                if st.button("Supprimer", key=f"del_{p['id']}", help="", use_container_width=True, type="primary"):
                                    if database.delete_produit(p['id']):
                                        st.toast(f"{p['nom']} retiré !")
                                        st.rerun()
            else:
                st.info("Aucun produit ne correspond aux critères.")

        except Exception as e:
            st.error(f"Erreur d'affichage : {e}")

    # =======================
    # TAB 2: AJOUT
    # =======================
    with tab2:
        st.subheader("Nouveau Produit")
        
        with st.form("ajout_produit", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                reference = st.text_input("Référence *")
                nom = st.text_input("Nom *")
                
                # Charger catégories
                cats = database.get_all_categories()
                if cats:
                    cats_dict = {c['id']: c['nom'] for c in cats}
                    categorie_id = st.selectbox("Catégorie *", options=list(cats_dict.keys()), format_func=lambda x: cats_dict[x])
                else:
                    st.warning("Aucune catégorie disponible. Veuillez en créer une dans Catégorie.")
                    categorie_id = None

            with col2:
                # Charger fournisseurs
                fours = database.get_all_fournisseurs()
                if fours:
                    fours_dict = {f['id']: f['nom'] for f in fours}
                    fournisseur_id = st.selectbox("Fournisseur", options=[None]+list(fours_dict.keys()), format_func=lambda x: fours_dict[x] if x else "Aucun")
                else:
                    fournisseur_id = None
                
                quantite = st.number_input("Quantité initiale", min_value=0, value=0)
                seuil_min = st.number_input("Seuil d'alerte", min_value=0, value=5)

            col3, col4 = st.columns(2)
            with col3:
                prix_achat = st.number_input("Prix d'achat (DH)", min_value=0.0, step=1.0)
            with col4:
                prix_vente = st.number_input("Prix de vente (DH)", min_value=0.0, step=1.0)
            
            description = st.text_area("Description", height=80)
            uploaded_image = st.file_uploader("Image du produit", type=['png', 'jpg', 'jpeg'])
            
            submitted = st.form_submit_button("Enregistrer le produit", use_container_width=True)

            if submitted:
                if not reference or not nom or not categorie_id:
                    st.error("Veuillez remplir les champs obligatoires (*).")
                else:
                    try:
                        # Sauvegarde de l'image
                        image_path = None
                        if uploaded_image:
                            image_path = save_uploaded_image(uploaded_image, reference)

                        database.add_produit({
                            "reference": reference,
                            "nom": nom,
                            "description": description,
                            "categorie_id": categorie_id,
                            "fournisseur_id": fournisseur_id,
                            "quantite": quantite,
                            "seuil_min": seuil_min,
                            "prix_achat": prix_achat,
                            "prix_vente": prix_vente,
                            "image_url": image_path
                        })
                        st.toast(f"Produit '{nom}' ajouté avec succès !")
                    except ValueError as ve:
                        st.warning(str(ve))
                    except Exception as e:
                        st.error(f"Erreur technique : {e}")
