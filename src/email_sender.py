"""
Module de gestion de l'envoi d'emails
"""
import os
import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailSenderError(Exception):
    """Exception levée en cas d'erreur d'envoi d'email"""
    pass


def send_email(subject, body, config, html=False):
    """
    Envoie un email
    
    Args:
        subject (str): Sujet de l'email
        body (str): Corps de l'email
        config (dict): Configuration contenant les paramètres SMTP
        html (bool): Si True, envoie en format HTML
        
    Returns:
        bool: True si l'envoi a réussi
        
    Raises:
        EmailSenderError: En cas d'erreur d'envoi
    """
    try:
        # Créer le message
        if html:
            msg = MIMEMultipart('alternative')
            msg.attach(MIMEText(body, 'plain'))
            msg.attach(MIMEText(body, 'html'))
        else:
            msg = MIMEText(body, 'plain', 'utf-8')
        
        msg['From'] = config['email_sender']
        msg['To'] = config['email_receiver']
        msg['Subject'] = subject
        msg['Date'] = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
        
        # Connexion et envoi
        with smtplib.SMTP(config['smtp_server'], config['smtp_port'], timeout=30) as server:
            server.starttls()
            server.login(config['email_sender'], config['smtp_password'])
            server.sendmail(
                config['email_sender'],
                config['email_receiver'],
                msg.as_string()
            )
        
        print(f"✅ Email envoyé avec succès : {subject}")
        return True
    
    except smtplib.SMTPAuthenticationError:
        error_msg = "Erreur d'authentification SMTP - Vérifiez vos identifiants"
        print(f"❌ {error_msg}")
        raise EmailSenderError(error_msg)
    
    except smtplib.SMTPException as e:
        error_msg = f"Erreur SMTP : {e}"
        print(f"❌ {error_msg}")
        raise EmailSenderError(error_msg)
    
    except Exception as e:
        error_msg = f"Erreur lors de l'envoi de l'email : {e}"
        print(f"❌ {error_msg}")
        raise EmailSenderError(error_msg)


def send_alert_email(log_file, analysis, severity_score, config):
    """
    Envoie un email d'alerte pour une anomalie détectée
    
    Args:
        log_file (str): Nom du fichier de log concerné
        analysis (str): Analyse de l'anomalie
        severity_score (int): Score de gravité (1-10)
        config (dict): Configuration
        
    Returns:
        bool: True si l'envoi a réussi
    """
    severity_emoji = {
        range(1, 4): "⚠️",
        range(4, 7): "🔶",
        range(7, 11): "🚨"
    }
    
    emoji = "🚨"
    for score_range, emoj in severity_emoji.items():
        if severity_score in score_range:
            emoji = emoj
            break
    
    subject = f"{emoji} Alerte Log - Anomalie critique dans {os.path.basename(log_file)} (Score: {severity_score})"
    
    body = f"""
Alerte de sécurité - Log Analyzer
{"="*60}

Fichier concerné : {log_file}
Score de gravité : {severity_score}/10
Date et heure : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

{"="*60}
ANALYSE DE L'ANOMALIE
{"="*60}

{analysis}

{"="*60}

Cet email a été généré automatiquement par Log Analyzer.
Pour plus d'informations, consultez le rapport quotidien.
"""
    
    try:
        return send_email(subject, body, config)
    except EmailSenderError as e:
        print(f"⚠️  Impossible d'envoyer l'alerte : {e}")
        return False


def send_daily_report(config):
    """
    Envoie le rapport quotidien des analyses de logs
    
    Args:
        config (dict): Configuration
        
    Returns:
        bool: True si l'envoi a réussi ou si aucun rapport à envoyer
    """
    daily_report_file = config['daily_report_file']
    
    try:
        if not os.path.exists(daily_report_file):
            print("ℹ️  Aucun fichier de rapport quotidien trouvé")
            return True
        
        with open(daily_report_file, "r", encoding='utf-8') as file:
            report_content = file.read()
        
        # Vérifier si le rapport contient du contenu utile
        if not report_content.strip() or report_content.strip() == "📊 Rapport quotidien des logs":
            print("ℹ️  Aucune activité à rapporter aujourd'hui")
            _reset_daily_report(daily_report_file)
            return True
        
        # Envoyer le rapport
        subject = f"📊 Rapport quotidien des logs - {datetime.date.today()}"
        success = send_email(subject, report_content, config)
        
        if success:
            print(f"📧 Rapport quotidien envoyé pour le {datetime.date.today()}")
            
            # Archiver l'ancien rapport
            _archive_report(daily_report_file, report_content)
            
            # Réinitialiser le fichier
            _reset_daily_report(daily_report_file)
        
        return success
    
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi du rapport quotidien : {e}")
        return False


def _archive_report(report_file, content):
    """Archive le rapport quotidien"""
    try:
        archive_dir = os.path.join(os.path.dirname(report_file), "archives")
        os.makedirs(archive_dir, exist_ok=True)
        
        archive_name = os.path.join(
            archive_dir,
            f"rapport_{datetime.date.today()}.txt"
        )
        
        with open(archive_name, "w", encoding='utf-8') as archive:
            archive.write(content)
        
        print(f"📦 Rapport archivé : {archive_name}")
    except Exception as e:
        print(f"⚠️  Impossible d'archiver le rapport : {e}")


def _reset_daily_report(report_file):
    """Réinitialise le fichier de rapport quotidien"""
    try:
        with open(report_file, "w", encoding='utf-8') as file:
            file.write("📊 Rapport quotidien des logs\n")
    except Exception as e:
        print(f"⚠️  Impossible de réinitialiser le rapport : {e}")


def test_email_configuration(config):
    """
    Teste la configuration email en envoyant un email de test
    
    Args:
        config (dict): Configuration
        
    Returns:
        bool: True si le test a réussi
    """
    subject = "🧪 Test de configuration - Log Analyzer"
    body = f"""
Ceci est un email de test envoyé par Log Analyzer.

Configuration testée :
- Serveur SMTP : {config['smtp_server']}:{config['smtp_port']}
- Expéditeur : {config['email_sender']}
- Destinataire : {config['email_receiver']}
- Date et heure : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Si vous recevez cet email, votre configuration est correcte ! ✅
"""
    
    try:
        return send_email(subject, body, config)
    except EmailSenderError:
        return False


if __name__ == "__main__":
    """Test du module d'envoi d'emails"""
    from config_loader import load_configuration
    
    try:
        config = load_configuration()
        print("🧪 Test de la configuration email...")
        
        if test_email_configuration(config):
            print("✅ Test réussi ! Vérifiez votre boîte de réception.")
        else:
            print("❌ Test échoué. Vérifiez votre configuration.")
    
    except Exception as e:
        print(f"❌ Erreur : {e}")