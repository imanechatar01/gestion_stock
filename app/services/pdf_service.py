from fpdf import FPDF
from datetime import datetime

class PDFReport(FPDF):
    def header(self):
        # Logo placeholder or Icon
        self.set_font('helvetica', 'B', 20)
        self.set_text_color(30, 64, 175) # Navy blue
        self.cell(0, 10, 'StockFlow Pro', ln=True, align='C')
        self.set_font('helvetica', 'I', 10)
        self.set_text_color(100)
        self.cell(0, 10, 'Rapport de Gestion de Stock', ln=True, align='C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()} | Généré le {datetime.now().strftime("%d/%m/%Y %H:%M")}', align='C')

def generate_stock_report(stats, movements, period_name="Général"):
    pdf = PDFReport()
    pdf.add_page()
    
    # Title
    pdf.set_font('helvetica', 'B', 16)
    pdf.set_text_color(0)
    pdf.cell(0, 10, f'Rapport {period_name}', ln=True)
    pdf.ln(5)
    
    # Statistics Summary
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_fill_color(240, 242, 246)
    pdf.cell(0, 10, ' Résumé des indicateurs', ln=True, fill=True)
    pdf.ln(2)
    
    pdf.set_font('helvetica', '', 10)
    col_width = pdf.epw / 2
    
    pdf.cell(col_width, 8, f"Total Produits: {stats.get('total_produits', 0)}")
    pdf.cell(col_width, 8, f"Valeur Totale: {stats.get('valeur_totale', 0):,.2f} DH", ln=True)
    
    pdf.set_text_color(220, 38, 38) # Red for alerts
    pdf.cell(col_width, 8, f"Alertes Stock: {stats.get('alertes', 0)}")
    pdf.set_text_color(0)
    pdf.cell(col_width, 8, f"Produits Épuisés: {stats.get('epuises', 0)}", ln=True)
    
    pdf.cell(col_width, 8, f"Fournisseurs: {stats.get('total_fournisseurs', 0)}")
    pdf.cell(col_width, 8, f"Catégories: {stats.get('total_categories', 0)}", ln=True)
    pdf.ln(10)
    
    # Movements Table
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_fill_color(240, 242, 246)
    pdf.cell(0, 10, ' Historique des mouvements', ln=True, fill=True)
    pdf.ln(2)
    
    if not movements:
        pdf.set_font('helvetica', 'I', 10)
        pdf.cell(0, 10, 'Aucun mouvement enregistré pour cette période.', ln=True)
    else:
        # Table Header
        pdf.set_font('helvetica', 'B', 9)
        pdf.set_fill_color(30, 64, 175)
        pdf.set_text_color(255)
        
        headers = ['Date', 'Produit', 'Type', 'Qté', 'Motif']
        widths = [35, 60, 20, 15, 60]
        
        for i in range(len(headers)):
            pdf.cell(widths[i], 8, headers[i], border=1, align='C', fill=True)
        pdf.ln()
        
        # Table Rows
        pdf.set_font('helvetica', '', 8)
        pdf.set_text_color(0)
        
        for m in movements[:50]: # Limit to 50 for performance/space
            date_str = m.get('date_mouvement', '')[:16]
            # Ensure truncation if too long
            prod_nom = str(m.get('produit_nom', ''))[:30]
            motif = str(m.get('motif', ''))[:35]
            
            pdf.cell(widths[0], 7, date_str, border=1)
            pdf.cell(widths[1], 7, prod_nom, border=1)
            
            # Color coding for type
            m_type = m.get('type', '').upper()
            if m_type == 'ENTREE':
                pdf.set_text_color(16, 185, 129)
            elif m_type == 'SORTIE':
                pdf.set_text_color(239, 68, 68)
            
            pdf.cell(widths[2], 7, m_type, border=1, align='C')
            pdf.set_text_color(0)
            
            pdf.cell(widths[3], 7, str(m.get('quantite', 0)), border=1, align='C')
            pdf.cell(widths[4], 7, motif, border=1)
            pdf.ln()
            
        if len(movements) > 50:
            pdf.set_font('helvetica', 'I', 8)
            pdf.cell(0, 10, f'... et {len(movements) - 50} autres mouvements.', align='C')

    return bytes(pdf.output())
