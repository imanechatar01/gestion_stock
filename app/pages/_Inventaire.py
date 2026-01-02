# app/pages/_Inventaire.py - Gestion des mouvements de stock
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from models import database

def show():
    st.title("📊 Gestion des Stocks et Inventaire")
    
    # Onglets pour les différentes fonctionnalités
    tab1, tab2, tab3, tab4 = st.tabs([
        "📥 Entrées Stock", 
        "📤 Sorties Stock", 
        "📋 Historique", 
        "🔄 Inventaire"
    ])
    
    # ============================================
    # TAB 1 : ENTREES DE STOCK
    # ============================================
    with tab1:
        st.header("📥 Entrées de Stock")
        st.markdown("Enregistrez les nouvelles arrivées de marchandises")
        
        # Formulaire d'entrée
        with st.form("form_entree_stock", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                # Sélection du produit
                produits = database.get_all_produits()
                if produits:
                    produits_dict = {p['id']: f"{p['reference']} - {p['nom']} (Stock: {p['quantite']})" 
                                   for p in produits}
                    
                    produit_id = st.selectbox(
                        "Produit *",
                        options=list(produits_dict.keys()),
                        format_func=lambda x: produits_dict[x],
                        help="Sélectionnez le produit à réapprovisionner"
                    )
                else:
                    st.warning("Aucun produit disponible. Créez d'abord des produits.")
                    produit_id = None
            
            with col2:
                quantite = st.number_input(
                    "Quantité *",
                    min_value=1,
                    value=1,
                    step=1,
                    help="Nombre d'unités à ajouter au stock"
                )
                
                # Récupérer le produit sélectionné pour info
                if produit_id:
                    produit_info = next((p for p in produits if p['id'] == produit_id), None)
                    if produit_info:
                        st.metric(
                            "Stock actuel",
                            f"{produit_info['quantite']} unités",
                            f"+{quantite}"
                        )
            
            # Champs supplémentaires
            motif = st.selectbox(
                "Motif de l'entrée *",
                [
                    "Réapprovisionnement normal",
                    "Commande fournisseur", 
                    "Retour client",
                    "Inventaire corrigé",
                    "Transfert interne",
                    "Autre"
                ]
            )
            
            motif_detail = st.text_area(
                "Détails supplémentaires",
                placeholder="N° commande, nom fournisseur, observations...",
                height=80
            )
            
            reference_doc = st.text_input(
                "Référence document",
                placeholder="Ex: CMD-2024-001, BL-1234..."
            )
            
            col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])
            with col_btn1:
                submitted = st.form_submit_button(
                    "✅ Enregistrer l'entrée de stock",
                    type="primary",
                    use_container_width=True
                )
            
            if submitted and produit_id:
                try:
                    # Récupérer le stock avant
                    produit_avant = database.get_produit_by_id(produit_id)
                    stock_avant = produit_avant['quantite']
                    
                    # Mettre à jour le stock
                    success = database.update_stock(
                        produit_id=produit_id,
                        quantite=quantite,
                        type_mouvement="entree",
                        motif=f"{motif}: {motif_detail}" if motif_detail else motif,
                        #utilisateur="admin",
                        document_ref=reference_doc
                    )
                    
                    if success:
                        # Récupérer le stock après
                        produit_apres = database.get_produit_by_id(produit_id)
                        stock_apres = produit_apres['quantite']
                        
                        st.success(f"""
                        ✅ Entrée de stock enregistrée avec succès !
                        
                        **Détails :**
                        - Produit: {produits_dict[produit_id]}
                        - Quantité ajoutée: **{quantite} unités**
                        - Stock avant: **{stock_avant}** → Stock après: **{stock_apres}**
                        - Motif: {motif}
                        """)
                        
                        # Réinitialiser le formulaire
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ Erreur: {str(e)}")
            elif submitted:
                st.error("❌ Veuillez sélectionner un produit")
    
    # ============================================
    # TAB 2 : SORTIES DE STOCK
    # ============================================
    with tab2:
        st.header("📤 Sorties de Stock")
        st.markdown("Enregistrez les sorties de marchandises (ventes, pertes, etc.)")
        
        with st.form("form_sortie_stock", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                # Sélection du produit
                produits = database.get_all_produits()
                if produits:
                    # Filtrer les produits avec stock > 0
                    produits_dispo = [p for p in produits if p['quantite'] > 0]
                    
                    if produits_dispo:
                        produits_dict = {p['id']: f"{p['reference']} - {p['nom']} (Stock: {p['quantite']})" 
                                       for p in produits_dispo}
                        
                        produit_id = st.selectbox(
                            "Produit *",
                            options=list(produits_dict.keys()),
                            format_func=lambda x: produits_dict[x],
                            key="sortie_produit",
                            help="Sélectionnez le produit à sortir"
                        )
                    else:
                        st.warning("⚠️ Aucun produit en stock disponible")
                        produit_id = None
                else:
                    st.warning("Aucun produit disponible")
                    produit_id = None
            
            with col2:
                quantite = st.number_input(
                    "Quantité *",
                    min_value=1,
                    value=1,
                    step=1,
                    key="sortie_quantite",
                    help="Nombre d'unités à retirer du stock"
                )
                
                # Vérification du stock disponible
                if produit_id:
                    produit_info = next((p for p in produits if p['id'] == produit_id), None)
                    if produit_info:
                        stock_dispo = produit_info['quantite']
                        
                        if quantite > stock_dispo:
                            st.error(f"❌ Stock insuffisant! Disponible: {stock_dispo}")
                        else:
                            st.metric(
                                "Stock après sortie",
                                f"{stock_dispo - quantite} unités",
                                f"-{quantite}",
                                delta_color="inverse"
                            )
            
            # Champs supplémentaires
            motif = st.selectbox(
                "Motif de la sortie *",
                [
                    "Vente client",
                    "Échantillon/démonstration",
                    "Perte/casse",
                    "Utilisation interne",
                    "Retour fournisseur",
                    "Inventaire corrigé",
                    "Autre"
                ],
                key="sortie_motif"
            )
            
            motif_detail = st.text_area(
                "Détails supplémentaires",
                placeholder="N° client, raison de la sortie, observations...",
                height=80,
                key="sortie_detail"
            )
            
            client_fournisseur = st.text_input(
                "Client/Fournisseur",
                placeholder="Nom du client ou fournisseur concerné",
                key="sortie_client"
            )
            
            col_btn1, col_btn2 = st.columns([3, 1])
            with col_btn1:
                submitted = st.form_submit_button(
                    "✅ Enregistrer la sortie de stock",
                    type="primary",
                    use_container_width=True
                )
            
            if submitted and produit_id:
                try:
                    # Vérifier le stock disponible
                    produit_info = next((p for p in produits if p['id'] == produit_id), None)
                    if produit_info and quantite <= produit_info['quantite']:
                        
                        # Récupérer le stock avant
                        stock_avant = produit_info['quantite']
                        
                        # Mettre à jour le stock
                        success = database.update_stock(
                            produit_id=produit_id,
                            quantite=quantite,
                            type_mouvement="sortie",
                            motif=f"{motif}: {motif_detail}" if motif_detail else motif,
                            utilisateur="admin"
                        )
                        
                        if success:
                            # Récupérer le stock après
                            produit_apres = database.get_produit_by_id(produit_id)
                            stock_apres = produit_apres['quantite']
                            
                            st.success(f"""
                            ✅ Sortie de stock enregistrée avec succès !
                            
                            **Détails :**
                            - Produit: {produits_dict[produit_id]}
                            - Quantité retirée: **{quantite} unités**
                            - Stock avant: **{stock_avant}** → Stock après: **{stock_apres}**
                            - Motif: {motif}
                            - Client/Fournisseur: {client_fournisseur or 'Non spécifié'}
                            """)
                            
                            st.rerun()
                    else:
                        st.error("❌ Quantité demandée supérieure au stock disponible")
                        
                except Exception as e:
                    st.error(f"❌ Erreur: {str(e)}")
            elif submitted:
                st.error("❌ Veuillez sélectionner un produit valide")
    
    # ============================================
    # TAB 3 : HISTORIQUE DES MOUVEMENTS
    # ============================================
        # ============================================
    # TAB 3 : HISTORIQUE DES MOUVEMENTS (FONCTIONNEL)
    # ============================================
    with tab3:
        st.header("📋 Historique des Mouvements")
        st.markdown("Consultez l'historique complet des entrées et sorties")
        
        # Filtres avancés
        with st.expander("🔍 Filtres avancés", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Période
                periode = st.selectbox(
                    "Période",
                    ["7 derniers jours", "30 derniers jours", "3 derniers mois", "Personnalisée", "Toutes"],
                    key="hist_periode"
                )
                
                # Dates personnalisées
                if periode == "Personnalisée":
                    date_debut = st.date_input("Date début")
                    date_fin = st.date_input("Date fin")
                else:
                    date_debut = None
                    date_fin = None
            
            with col2:
                # Type de mouvement
                type_mouvement = st.selectbox(
                    "Type de mouvement",
                    ["Tous", "entree", "sortie", "ajustement", "inventaire"],
                    key="hist_type"
                )
                
                # Utilisateur
                utilisateur = st.text_input(
                    "Utilisateur",
                    placeholder="Filtrer par utilisateur...",
                    key="hist_user"
                )
            
            with col3:
                # Produit
                produits = database.get_all_produits()
                produits_liste = ["Tous"] + [f"{p['id']} - {p['nom']}" for p in produits]
                produit_filtre = st.selectbox(
                    "Produit", 
                    produits_liste,
                    key="hist_produit"
                )
                
                # Limite de résultats
                limite = st.number_input(
                    "Nombre max de résultats",
                    min_value=10,
                    max_value=1000,
                    value=100,
                    step=10,
                    key="hist_limit"
                )
        
        # Boutons d'action
        col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])
        with col_btn1:
            if st.button("🔍 Appliquer les filtres", type="primary", use_container_width=True):
                st.rerun()
        
        with col_btn2:
            if st.button("📥 Exporter", use_container_width=True):
                st.info("Export en cours de développement...")
        
        with col_btn3:
            if st.button("🔄 Actualiser", use_container_width=True):
                st.rerun()
        
        st.markdown("---")
        
        # Préparation des filtres pour la base de données
        filtres = {'limit': limite}
        
        # Gestion de la période
        from datetime import datetime, timedelta
        aujourdhui = datetime.now()
        
        if periode == "7 derniers jours":
            filtres['date_debut'] = (aujourdhui - timedelta(days=7)).strftime('%Y-%m-%d')
        elif periode == "30 derniers jours":
            filtres['date_debut'] = (aujourdhui - timedelta(days=30)).strftime('%Y-%m-%d')
        elif periode == "3 derniers mois":
            filtres['date_debut'] = (aujourdhui - timedelta(days=90)).strftime('%Y-%m-%d')
        elif periode == "Personnalisée" and date_debut and date_fin:
            filtres['date_debut'] = date_debut.strftime('%Y-%m-%d')
            filtres['date_fin'] = date_fin.strftime('%Y-%m-%d')
        
        # Autres filtres
        if type_mouvement != "Tous":
            filtres['type_mouvement'] = type_mouvement
        
        if produit_filtre != "Tous":
            produit_id = int(produit_filtre.split(" - ")[0])
            filtres['produit_id'] = produit_id
        
        if utilisateur:
            filtres['utilisateur'] = utilisateur
        
        # Récupération des mouvements
        try:
            mouvements = database.get_mouvements(filtres)
            
            if mouvements:
                # Conversion en DataFrame pour l'affichage
                df_mouvements = pd.DataFrame(mouvements)
                
                # Formatage des dates
                if 'date_mouvement' in df_mouvements.columns:
                    df_mouvements['date_mouvement'] = pd.to_datetime(df_mouvements['date_mouvement'])
                    df_mouvements['date_formatee'] = df_mouvements['date_mouvement'].dt.strftime('%d/%m/%Y %H:%M')
                
                # Ajout d'une colonne pour l'icône du type
                def get_icon_mouvement(type_mvt):
                    icons = {
                        'entree': '📥',
                        'sortie': '📤',
                        'ajustement': '🔄',
                        'inventaire': '📊',
                        'annulation': '🗑️'
                    }
                    return icons.get(type_mvt, '📝')
                
                df_mouvements['icone'] = df_mouvements['type'].apply(get_icon_mouvement)
                
                # Calcul des statistiques
                total_entrees = df_mouvements[df_mouvements['type'] == 'entree']['quantite'].sum()
                total_sorties = df_mouvements[df_mouvements['type'] == 'sortie']['quantite'].sum()
                solde_net = total_entrees - total_sorties
                
                # Affichage des statistiques
                col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                with col_stat1:
                    st.metric("Mouvements", len(df_mouvements))
                with col_stat2:
                    st.metric("Entrées", f"{total_entrees} unités")
                with col_stat3:
                    st.metric("Sorties", f"{total_sorties} unités")
                with col_stat4:
                    st.metric("Solde net", f"{solde_net} unités", delta=f"{solde_net:+d}")
                
                st.markdown("---")
                
                # Affichage du tableau des mouvements
                st.subheader("📄 Détail des mouvements")
                
                # Sélection des colonnes à afficher
                columns_config = {
                    "icone": " ",
                    "date_formatee": "Date",
                    "produit_nom": "Produit",
                    "type": "Type",
                    "quantite": "Quantité",
                    "quantite_avant": "Avant",
                    "quantite_apres": "Après",
                    "motif": "Motif",
                    "utilisateur": "Utilisateur"
                }
                
                # Filtrer les colonnes existantes
                existing_columns = {k: v for k, v in columns_config.items() 
                                  if k in df_mouvements.columns}
                
                # Affichage avec configuration
                st.dataframe(
                    df_mouvements[list(existing_columns.keys())],
                    column_config=existing_columns,
                    use_container_width=True,
                    height=400
                )
                
                # Options d'export
                with st.expander("💾 Options d'export"):
                    col_exp1, col_exp2 = st.columns(2)
                    with col_exp1:
                        if st.button("📊 Exporter en CSV", use_container_width=True):
                            csv = df_mouvements.to_csv(index=False, encoding='utf-8-sig')
                            st.download_button(
                                label="Télécharger CSV",
                                data=csv,
                                file_name=f"historique_mouvements_{datetime.now().strftime('%Y%m%d')}.csv",
                                mime="text/csv"
                            )
                    
                    with col_exp2:
                        if st.button("📈 Exporter en Excel", use_container_width=True):
                            excel_path = f"historique_mouvements_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                            df_mouvements.to_excel(excel_path, index=False)
                            st.success(f"Exporté vers: {excel_path}")
                
                # Graphique d'évolution
                st.markdown("---")
                st.subheader("📈 Évolution des mouvements")
                
                if 'date_mouvement' in df_mouvements.columns:
                    # Préparation des données pour le graphique
                    df_graph = df_mouvements.copy()
                    df_graph['date'] = df_graph['date_mouvement'].dt.date
                    
                    # Agrégation par date et type
                    df_agg = df_graph.groupby(['date', 'type']).agg({
                        'quantite': 'sum'
                    }).reset_index()
                    
                    # Pivot pour avoir les types en colonnes
                    df_pivot = df_agg.pivot(index='date', columns='type', values='quantite').fillna(0)
                    
                    # Affichage du graphique
                    if not df_pivot.empty:
                        st.line_chart(df_pivot)
                    else:
                        st.info("Données insuffisantes pour générer le graphique")
                
            else:
                st.info("📭 Aucun mouvement trouvé pour les critères sélectionnés")
                
                # Suggestions
                st.caption("Suggestions :")
                st.caption("• Élargissez la période de recherche")
                st.caption("• Vérifiez les filtres appliqués")
                st.caption("• Effectuez des mouvements de stock pour alimenter l'historique")
                
        except Exception as e:
            st.error(f"❌ Erreur lors de la récupération de l'historique: {str(e)}")
            st.info("Assurez-vous que la fonction `get_mouvements()` est bien implémentée dans database.py")