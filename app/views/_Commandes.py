# app/pages/_Commandes.py
import streamlit as st
import pandas as pd
from datetime import datetime
from models import database

def show():
    # Remove default Streamlit top padding
    st.markdown("""
        <style>
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0rem !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("📑 Générateur de Commandes")
    
    # Récupérer le produit à commander s'il a été passé en paramètre
    produit_id_w = st.session_state.get('commande_produit')
    
    # Nettoyer l'état pour ne pas rester bloqué sur ce produit si on recharge
    # On le garde juste pour l'init du formulaire
    
    st.markdown("""
    Créez rapidement des bons de commande professionnels au format PDF/Imprimable.
    """)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("1. Configuration")
        
        with st.form("config_commande"):
            # Sélection du fournisseur
            fournisseurs = database.get_all_fournisseurs()
            fourn_dict = {f['id']: f['nom'] for f in fournisseurs}
            
            # Tenter de trouver le fournisseur du produit pré-sélectionné
            default_fourn_index = 0
            produit_info = None
            
            if produit_id_w:
                produit_info = database.get_produit_by_id(produit_id_w)
                if produit_info and produit_info['fournisseur_id'] in fourn_dict:
                    # Trouver l'index dans la liste des keys
                    keys_list = list(fourn_dict.keys())
                    if produit_info['fournisseur_id'] in keys_list:
                        default_fourn_index = keys_list.index(produit_info['fournisseur_id'])

            fournisseur_id = st.selectbox(
                "Fournisseur", 
                options=list(fourn_dict.keys()),
                format_func=lambda x: fourn_dict[x],
                index=default_fourn_index
            )
            
            date_commande = st.date_input("Date de commande", datetime.today())
            num_commande = st.text_input("N° Commande", value=f"CMD-{datetime.now().strftime('%Y%m%d')}-001")
            
            st.divider()
            st.caption("Produits à commander")
            
            # Interface simple : un seul produit pour l'instant (MVP)
            # Ou liste de produits
            produits = database.get_all_produits()
            prod_dict = {p['id']: f"{p['nom']} (Réf: {p['reference']})" for p in produits}
            
            # Default product selection
            default_prod_index = 0
            if produit_id_w and produit_id_w in prod_dict:
                 keys_list_p = list(prod_dict.keys())
                 if produit_id_w in keys_list_p:
                     default_prod_index = keys_list_p.index(produit_id_w)
            
            selected_prod = st.selectbox(
                "Ajouter un produit", 
                options=list(prod_dict.keys()),
                format_func=lambda x: prod_dict[x],
                index=default_prod_index
            )
            
            # Recup prix d'achat
            p_data = next((p for p in produits if p['id'] == selected_prod), None)
            prix_achat_def = p_data['prix_achat'] if p_data else 0.0
            
            # Quantité recommandée = Seuil - Stock actuel + Marge (ex: 10)
            qte_def = 10
            if produit_info and selected_prod == produit_id_w:
                if produit_info['quantite'] <= produit_info['seuil_min']:
                    qte_def = (produit_info['seuil_min'] - produit_info['quantite']) + 10
            
            qte = st.number_input("Quantité", min_value=1, value=int(qte_def))
            prix_u = st.number_input("Prix Unitaire HT", value=float(prix_achat_def))
            
            tva = st.number_input("TVA (%)", value=20.0)
            
            generate = st.form_submit_button("Générer le Bon de Commande", type="primary")

    with col2:
        st.subheader("2. Aperçu du Bon de Commande")
        
        if generate:
            # Récupérer les infos complètes
            fourn = next((f for f in fournisseurs if f['id'] == fournisseur_id), None)
            prod = next((p for p in produits if p['id'] == selected_prod), None)
            
            if fourn and prod:
                total_ht = qte * prix_u
                montant_tva = total_ht * (tva / 100)
                total_ttc = total_ht + montant_tva
                
                # Template HTML simple pour l'impression
                html_invoice = f"""
                <div style="background-color: white; padding: 40px; border: 1px solid #ddd; border-radius: 5px; color: black;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 40px;">
                        <div>
                            <h1 style="color: #1E40AF; margin: 0;">BON DE COMMANDE</h1>
                            <p><strong>N° {num_commande}</strong><br>Date: {date_commande.strftime('%d/%m/%Y')}</p>
                        </div>
                        <div style="text-align: right;">
                            <h3 style="margin: 0;">VOTRE ENTREPRISE</h3>
                            <p>123 Avenue du Stock<br>75000 Paris<br>Tél: 01 02 03 04 05</p>
                        </div>
                    </div>
                    
                    <div style="display: flex; justify-content: space-between; margin-bottom: 40px; border-top: 2px solid #eee; padding-top: 20px;">
                        <div style="width: 45%;">
                            <h4 style="color: #666;">FOURNISSEUR</h4>
                            <p><strong>{fourn['nom']}</strong><br>
                            {fourn['email'] or ''}<br>
                            {fourn['telephone'] or ''}</p>
                        </div>
                        <div style="width: 45%;">
                            <h4 style="color: #666;">LIVRER À</h4>
                            <p><strong>Entrepôt Principal</strong><br>Quai de réception N°1</p>
                        </div>
                    </div>
                    
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
                        <thead>
                            <tr style="background-color: #f8f9fa; text-align: left;">
                                <th style="padding: 12px; border-bottom: 2px solid #ddd;">Réf</th>
                                <th style="padding: 12px; border-bottom: 2px solid #ddd;">Désignation</th>
                                <th style="padding: 12px; border-bottom: 2px solid #ddd; text-align: right;">Qté</th>
                                <th style="padding: 12px; border-bottom: 2px solid #ddd; text-align: right;">P.U. HT</th>
                                <th style="padding: 12px; border-bottom: 2px solid #ddd; text-align: right;">Total HT</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="padding: 12px; border-bottom: 1px solid #eee;">{prod['reference']}</td>
                                <td style="padding: 12px; border-bottom: 1px solid #eee;">{prod['nom']}</td>
                                <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: right;">{qte}</td>
                                <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: right;">{prix_u:.2f} DH</td>
                                <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: right;">{total_ht:.2f} DH</td>
                            </tr>
                        </tbody>
                    </table>
                    
                    <div style="display: flex; justify-content: flex-end;">
                        <div style="width: 300px;">
                            <div style="display: flex; justify-content: space-between; padding: 5px 0;">
                                <span>Total HT:</span>
                                <span>{total_ht:.2f} DH</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; padding: 5px 0;">
                                <span>TVA ({tva}%):</span>
                                <span>{montant_tva:.2f} DH</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; padding: 10px 0; border-top: 2px solid #ddd; font-weight: bold; font-size: 1.2em;">
                                <span>TOTAL TTC:</span>
                                <span>{total_ttc:.2f} DH</span>
                            </div>
                        </div>
                    </div>
                    
                    <div style="margin-top: 50px; border-top: 1px dashed #ccc; padding-top: 20px; text-align: center; color: #888; font-style: italic;">
                        Merci de confirmer la réception de cette commande sous 48h.
                    </div>
                </div>
                """
                
                st.markdown(html_invoice, unsafe_allow_html=True)
                
                # Instructions pour imprimer
                st.info("💡 Astuce : Faites Ctrl+P (ou Cmd+P) pour imprimer cette page ou l'enregistrer en PDF.")
                
            else:
                st.warning("Informations manquantes pour générer le bon.")
        
        else:
            st.info("👈 Configurez la commande à gauche et cliquez sur 'Générer' pour voir l'aperçu ici.")

if __name__ == "__main__":
    show()
