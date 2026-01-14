import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)

# CONFIGURATION SMTP (À REMPLIR PAR L'UTILISATEUR)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "chatarimane02@gmail.com"  # À remplacer
SMTP_PASSWORD = "fobu rvrs aima ovmy"  # À remplacer (utiliser un mot de passe d'application)

def send_verification_code(email, code):
    """
    Envoie un code de vérification à l'adresse email spécifiée.
    Note: Si SMTP n'est pas configuré, le code sera affiché dans les logs du terminal.
    """
    subject = "Votre code de vérification - StockFlow Pro"
    body = f"""
    Bonjour,
    
    Vous avez demandé la réinitialisation de votre mot de passe.
    Voici votre code de vérification : {code}
    
    Ce code est valable pendant 15 minutes.
    
    Si vous n'êtes pas à l'origine de cette demande, veuillez ignorer cet email.
    
    L'équipe StockFlow Pro.
    """
    
    # Tentative d'envoi réel
    try:
        msg = MIMEMultipart()
        msg['From'] = "imenchatar1@gmail.com"
        msg['To'] = email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.info(f"Email envoyé avec succès à {email}")
        return True, "Email envoyé !"
    except Exception as e:
        # Fallback pour le développement : Affichage dans la console
        logger.warning(f"Impossible d'envoyer l'email via SMTP: {e}")
        print("\n" + "="*50)
        print(f"📧 SIMULATION EMAIL POUR : {email}")
        print(f"🔑 CODE DE VÉRIFICATION : {code}")
        print("="*50 + "\n")
        return True, "Code généré (Consultez le terminal car SMTP n'est pas configuré)"
