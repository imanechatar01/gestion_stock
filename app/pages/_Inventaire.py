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
                        utilisateur="admin",
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
    with tab3:
        st.header("📋 Historique des Mouvements")
        st.markdown("Consultez l'historique complet des entrées et sorties")
        
        # Filtres
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Filtre par date
            periode = st.selectbox(
                "Période",
                ["7 derniers jours", "30 derniers jours", "3 derniers mois", "Toutes"]
            )
            
            # Calcul des dates en fonction de la période
            aujourdhui = datetime.now()
            if periode == "7 derniers jours":
                date_debut = aujourdhui - timedelta(days=7)
            elif periode == "30 derniers jours":
                date_debut = aujourdhui - timedelta(days=30)
            elif periode == "3 derniers mois":
                date_debut = aujourdhui - timedelta(days=90)
            else:
                date_debut = None
        
        with col2:
            # Filtre par type de mouvement
            type_mouvement = st.selectbox(
                "Type de mouvement",
                ["Tous", "Entrées", "Sorties"]
            )
        
        with col3:
            # Filtre par produit
            produits = database.get_all_produits()
            produits_liste = ["Tous"] + [f"{p['id']}: {p['nom']}" for p in produits]
            produit_filtre = st.selectbox("Produit", produits_liste)
        
        # Bouton d'actualisation
        if st.button("🔍 Appliquer les filtres", use_container_width=True):
            st.rerun()
        
        st.markdown("---")
        
        # Récupération des mouvements depuis la base
        # Note: Il faudrait ajouter une fonction get_mouvements() dans database.py
        # Pour l'instant, on simule avec un message
        
        st.info("""
        **Fonctionnalité en développement**
        
        L'historique des mouvements nécessite l'ajout de la fonction `get_mouvements()` 
        dans le module `database.py`.
        
        Pour l'instant, vous pouvez voir les mouvements en temps réel dans les onglets 
        "Entrées" et "Sorties".
        """)
        
        # Code pour afficher l'historique (à décommenter quand la fonction sera disponible)
        """
        # Exemple de code quand get_mouvements() sera implémenté
        mouvements = database.get_mouvements(
            date_debut=date_debut,
            type_mouvement=type_mouvement.lower() if type_mouvement != "Tous" else None,
            produit_id=int(produit_filtre.split(":")[0]) if produit_filtre != "Tous" else None
        )
        
        if mouvements:
            df_mouvements = pd.DataFrame(mouvements)
            
            # Formatage des dates
            df_mouvements['date_mouvement'] = pd.to_datetime(df_mouvements['date_mouvement'])
            df_mouvements['date_formatee'] = df_mouvements['date_mouvement'].dt.strftime('%d/%m/%Y %H:%M')
            
            # Affichage sous forme de tableau
            st.dataframe(
                df_mouvements[['date_formatee', 'type', 'quantite', 'motif', 'utilisateur']],
                column_config={
                    "date_formatee": "Date",
                    "type": "Type",
                    "quantite": "Quantité",
                    "motif": "Motif",
                    "utilisateur": "Utilisateur"
                },
                use_container_width=True,
                height=400
            )
            
            # Statistiques
            col1, col2, col3 = st.columns(3)
            with col1:
                total_entrees = df_mouvements[df_mouvements['type'] == 'entree']['quantite'].sum()
                st.metric("Total entrées", f"{total_entrees} unités")
            
            with col2:
                total_sorties = df_mouvements[df_mouvements['type'] == 'sortie']['quantite'].sum()
                st.metric("Total sorties", f"{total_sorties} unités")
            
            with col3:
                solde = total_entrees - total_sorties
                st.metric("Solde net", f"{solde} unités", delta=f"{solde:+d}")
        else:
            st.info("Aucun mouvement trouvé pour les critères sélectionnés")
        """
    
    # ============================================
    # TAB 4 : INVENTAIRE PHYSIQUE
    # ============================================
    with tab4:
        st.header("🔄 Inventaire Physique")
        st.markdown("Ajustez les stocks suite à un inventaire physique")
        
        # Mode d'inventaire
        mode = st.radio(
            "Mode d'inventaire",
            ["Inventaire complet", "Ajustement par produit"],
            horizontal=True
        )
        
        if mode == "Inventaire complet":
            st.subheader("📝 Saisie de l'inventaire complet")
            
            # Récupérer tous les produits
            produits = database.get_all_produits()
            
            if produits:
                st.info(f"📊 **{len(produits)} produits à inventorier**")
                
                # Formulaire pour chaque produit
                with st.form("form_inventaire_complet"):
                    ajustements = []
                    
                    for produit in produits:
                        with st.container():
                            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                            
                            with col1:
                                st.write(f"**{produit['nom']}**")
                                st.caption(f"Réf: {produit['reference']} | Cat: {produit['categorie_nom']}")
                            
                            with col2:
                                st.metric("Stock théorique", f"{produit['quantite']}")
                            
                            with col3:
                                quantite_reelle = st.number_input(
                                    "Stock physique",
                                    min_value=0,
                                    value=produit['quantite'],
                                    step=1,
                                    key=f"inv_{produit['id']}"
                                )
                            
                            with col4:
                                difference = quantite_reelle - produit['quantite']
                                if difference > 0:
                                    st.success(f"+{difference}")
                                elif difference < 0:
                                    st.error(f"{difference}")
                                else:
                                    st.info("✓")
                            
                            st.divider()
                            
                            # Stocker l'ajustement
                            if quantite_reelle != produit['quantite']:
                                ajustements.append({
                                    'produit_id': produit['id'],
                                    'quantite_reelle': quantite_reelle,
                                    'difference': difference,
                                    'produit_nom': produit['nom']
                                })
                    
                    motif_inventaire = st.text_input(
                        "Motif de l'inventaire",
                        placeholder="Ex: Inventaire de fin d'année 2024..."
                    )
                    
                    submitted = st.form_submit_button(
                        "✅ Valider l'inventaire complet",
                        type="primary",
                        use_container_width=True
                    )
                    
                    if submitted:
                        if ajustements:
                            st.success(f"""
                            **Résumé de l'inventaire :**
                            - Produits ajustés: **{len(ajustements)}**
                            - Motif: {motif_inventaire}
                            
                            **Cliquez sur 'Confirmer' pour appliquer les ajustements.**
                            """)
                            
                            # Afficher le détail des ajustements
                            with st.expander("🔍 Détail des ajustements"):
                                for ajust in ajustements:
                                    st.write(f"**{ajust['produit_nom']}** : {ajust['difference']:+d} unités")
                            
                            # Bouton de confirmation
                            if st.button("✅ Confirmer et appliquer les ajustements", type="primary"):
                                try:
                                    for ajust in ajustements:
                                        database.update_stock(
                                            produit_id=ajust['produit_id'],
                                            quantite=ajust['quantite_reelle'],
                                            type_mouvement="inventaire",
                                            motif=f"Inventaire physique: {motif_inventaire}",
                                            utilisateur="admin"
                                        )
                                    
                                    st.success("🎉 Inventaire complété avec succès !")
                                    st.balloons()
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"❌ Erreur: {str(e)}")
                        else:
                            st.info("✅ Aucun écart détecté. Les stocks théoriques correspondent aux stocks physiques.")
            
            else:
                st.warning("Aucun produit à inventorier")
        
        else:  # Mode ajustement par produit
            st.subheader("🔧 Ajustement de stock ponctuel")
            
            with st.form("form_ajustement_ponctuel"):
                # Sélection du produit
                produits = database.get_all_produits()
                if produits:
                    produits_dict = {p['id']: f"{p['reference']} - {p['nom']}" for p in produits}
                    
                    produit_id = st.selectbox(
                        "Produit à ajuster *",
                        options=list(produits_dict.keys()),
                        format_func=lambda x: produits_dict[x]
                    )
                    
                    if produit_id:
                        produit_info = next((p for p in produits if p['id'] == produit_id), None)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Stock actuel", f"{produit_info['quantite']} unités")
                        
                        with col2:
                            nouvelle_quantite = st.number_input(
                                "Nouveau stock *",
                                min_value=0,
                                value=produit_info['quantite'],
                                step=1
                            )
                        
                        difference = nouvelle_quantite - produit_info['quantite']
                        
                        if difference != 0:
                            st.info(f"""
                            **Ajustement :** {difference:+d} unités
                            ({produit_info['quantite']} → {nouvelle_quantite})
                            """)
                        
                        motif = st.text_area(
                            "Motif de l'ajustement *",
                            placeholder="Ex: Erreur de saisie, perte constatée, inventaire partiel...",
                            height=100
                        )
                        
                        submitted = st.form_submit_button(
                            "✅ Appliquer l'ajustement",
                            type="primary",
                            use_container_width=True
                        )
                        
                        if submitted and produit_id and motif:
                            try:
                                success = database.update_stock(
                                    produit_id=produit_id,
                                    quantite=nouvelle_quantite,
                                    type_mouvement="ajustement",
                                    motif=motif,
                                    utilisateur="admin"
                                )
                                
                                if success:
                                    st.success(f"""
                                    ✅ Ajustement appliqué avec succès !
                                    
                                    **{produit_info['nom']}**
                                    - Ancien stock: **{produit_info['quantite']}**
                                    - Nouveau stock: **{nouvelle_quantite}**
                                    - Variation: **{difference:+d} unités**
                                    - Motif: {motif}
                                    """)
                                    st.rerun()
                                    
                            except Exception as e:
                                st.error(f"❌ Erreur: {str(e)}")
                        elif submitted:
                            st.error("❌ Veuillez remplir tous les champs obligatoires")
                
                else:
                    st.warning("Aucun produit disponible")
    
    # ============================================
    # SECTION COMMUNE : ALERTES STOCK
    # ============================================
    st.markdown("---")
    
    # Section alertes (affichée dans tous les onglets)
    with st.expander("⚠️ **Produits nécessitant une attention**", expanded=True):
        produits_alerte = database.get_produits_en_alerte()
        
        if produits_alerte:
            st.warning(f"**{len(produits_alerte)} produits en alerte de stock**")
            
            for produit in produits_alerte:
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.write(f"**{produit['nom']}**")
                    st.caption(f"{produit['categorie_nom']}")
                
                with col2:
                    st.metric(
                        "Stock actuel",
                        f"{produit['quantite']}",
                        f"Seuil: {produit['seuil_min']}",
                        delta_color="inverse"
                    )
                
                with col3:
                    # Bouton rapide pour commander
                    if st.button("📥 Commander", key=f"cmd_{produit['id']}", use_container_width=True):
                        st.session_state['commande_produit'] = produit['id']
                        st.success(f"Commande initiée pour {produit['nom']}")
                
                with col4:
                    # Bouton rapide pour ajuster
                    if st.button("✏️ Ajuster", key=f"ajust_{produit['id']}", use_container_width=True):
                        st.session_state['ajuster_produit'] = produit['id']
                
                st.divider()
        else:
            st.success("✅ Tous les produits ont un stock suffisant")

# Test de la page
if __name__ == "__main__":
    show()