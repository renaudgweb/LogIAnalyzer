import os
import smtplib
import re
import signal
import sys
from mistralai import Mistral
import time
import datetime
import schedule
from email.mime.text import MIMEText
from concurrent.futures import ThreadPoolExecutor
from configparser import ConfigParser
from dotenv import load_dotenv

load_dotenv()

# Load configuration from a file
config = ConfigParser()
config.read('config.ini')

# Read configuration values
LOG_FILES = config.get('Settings', 'log_files').split(', ')
EMAIL_SENDER = config.get('Settings', 'email_sender')
EMAIL_RECEIVER = config.get('Settings', 'email_receiver')
SMTP_SERVER = config.get('Settings', 'smtp_server')
SMTP_PORT = config.getint('Settings', 'smtp_port')
LOG_CHECK_INTERVAL = config.getint('Settings', 'log_check_interval')
AI_TEMPERATURE = config.getfloat('Settings', 'ai_temperature')
AI_MAX_TOKENS = config.getint('Settings', 'ai_max_tokens')
DAILY_REPORT_FILE = config.get('Settings', 'daily_report_file')

# Environment variables for sensitive data
AI_API_KEY = os.getenv("AI_API_KEY")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# Variable globale pour arrêt propre
shutdown_flag = False

# Gestionnaire de signal pour arrêt propre
def signal_handler(sig, frame):
    global shutdown_flag
    print("\n🛑 Arrêt du monitoring en cours...")
    shutdown_flag = True


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# Vérifier si le fichier existe, sinon le créer
if not os.path.exists(DAILY_REPORT_FILE):
    try:
        with open(DAILY_REPORT_FILE, "w") as file:
            file.write("📊 Rapport quotidien des logs\n")
        print(f"📄 Fichier {DAILY_REPORT_FILE} créé avec succès.")
    except PermissionError:
        print(f"❌ Permission refusée : Impossible de créer "
              f"{DAILY_REPORT_FILE}. Exécute le script avec sudo.")
        sys.exit(1)


def read_new_logs(log_file, last_position):
    """Lit les nouvelles lignes d'un fichier log depuis la dernière position lue."""
    try:
        with open(log_file, "r") as file:
            file.seek(last_position)
            new_logs = file.readlines()
            last_position = file.tell()
        return new_logs, last_position
    except FileNotFoundError:
        print(f"⚠️ Fichier non trouvé : {log_file}")
        return [], last_position
    except PermissionError:
        print(f"❌ Permission refusée pour lire : {log_file}")
        return [], last_position


def analyze_logs_with_ai(logs):
    """Analyse les logs via IA pour détecter des anomalies."""
    if not logs:
        return "Pas de nouvelles entrées dans les logs."

    try:
        client = Mistral(api_key=AI_API_KEY)
        response = client.chat.complete(
            model="mistral-large-latest",
            temperature=AI_TEMPERATURE,
            max_tokens=AI_MAX_TOKENS,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es un expert en cybersécurité et en analyse de logs Linux. "
                        "Pour chaque anomalie détectée, commence OBLIGATOIREMENT ta réponse par : "
                        "'SEVERITY_SCORE: X' où X est un nombre entre 1 et 10 (1=bénin, 10=critique). "
                        "Ensuite, décris les anomalies détectées et propose des recommandations claires. "
                        "Si aucune anomalie n'est détectée, indique 'SEVERITY_SCORE: 0'."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Analyse les logs suivants et attribue un score de gravité. "
                        f"Pour chaque anomalie, propose une solution ou une recommandation :"
                        f"\n{''.join(logs)}"
                    ),
                }
            ]
        )
        
        # Correction : accès à l'objet response
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse IA : {e}")
        return "SEVERITY_SCORE: 0\nErreur d'analyse IA - Impossible de traiter les logs."


def extract_severity_score(analysis):
    """Extrait le score de gravité de l'analyse."""
    match = re.search(r'SEVERITY_SCORE:\s*(\d+)', analysis)
    if match:
        score = int(match.group(1))
        return max(0, min(10, score))  # S'assurer que le score est entre 0 et 10
    return 0


def send_email(subject, body):
    """Envoie un email contenant l'analyse."""
    msg = MIMEText(body)
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = subject

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, SMTP_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        print("✅ Email envoyé avec succès")
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi de l'email : {e}")


def send_daily_report():
    """Envoie un compte rendu quotidien des analyses de logs."""
    try:
        if os.path.exists(DAILY_REPORT_FILE):
            with open(DAILY_REPORT_FILE, "r") as file:
                report_content = file.read()

            if report_content.strip() and report_content.strip() != "📊 Rapport quotidien des logs":
                subject = f"📊 Rapport quotidien des logs - {datetime.date.today()}"
                send_email(subject, report_content)
                print(f"📧 Rapport quotidien envoyé pour le {datetime.date.today()}")
            else:
                print("ℹ️ Aucune activité à rapporter aujourd'hui")

            # Archiver l'ancien rapport (optionnel)
            archive_name = f"rapport_{datetime.date.today()}.txt"
            if report_content.strip() and report_content.strip() != "📊 Rapport quotidien des logs":
                try:
                    with open(archive_name, "w") as archive:
                        archive.write(report_content)
                except Exception as e:
                    print(f"⚠️ Impossible d'archiver le rapport : {e}")

            # Réinitialiser le fichier après envoi
            with open(DAILY_REPORT_FILE, "w") as file:
                file.write("📊 Rapport quotidien des logs\n")
    
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi du rapport quotidien : {e}")


def monitor_logs():
    """Surveille les fichiers de logs et analyse les nouvelles lignes à intervalles réguliers."""
    log_positions = {log_file: 0 for log_file in LOG_FILES}
    
    print(f"🚀 Démarrage du monitoring des logs...")
    print(f"📁 Fichiers surveillés : {', '.join(LOG_FILES)}")
    print(f"⏱️ Intervalle de vérification : {LOG_CHECK_INTERVAL}s")
    print(f"📧 Alertes envoyées à : {EMAIL_RECEIVER}")
    print(f"🕓 Rapport quotidien programmé à 04:00\n")

    # Créer le ThreadPoolExecutor une seule fois
    with ThreadPoolExecutor(max_workers=len(LOG_FILES)) as executor:
        while not shutdown_flag:
            try:
                futures = {}
                for log_file in LOG_FILES:
                    futures[log_file] = executor.submit(
                        read_new_logs, log_file, log_positions[log_file]
                    )

                for log_file, future in futures.items():
                    try:
                        new_logs, new_position = future.result(timeout=30)
                        log_positions[log_file] = new_position

                        if new_logs:
                            print(f"🔍 Analyse de {len(new_logs)} nouvelles lignes dans {log_file}...")
                            analysis = analyze_logs_with_ai(new_logs)
                            
                            # Stocker l'analyse dans le fichier de rapport quotidien
                            try:
                                with open(DAILY_REPORT_FILE, "a") as report_file:
                                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    report_file.write(f"\n[{timestamp}] [{log_file}]\n{analysis}\n")
                            except PermissionError:
                                print(f"❌ Permission refusée pour écrire dans {DAILY_REPORT_FILE}")

                            # Extraire et vérifier le score de gravité
                            severity_score = extract_severity_score(analysis)
                            
                            if severity_score >= 7:
                                print(f"🚨 ALERTE CRITIQUE (Score: {severity_score}) détectée dans {log_file}")
                                send_email(
                                    f"🚨 Alerte Log - Anomalie critique dans {log_file} (Score: {severity_score})", 
                                    analysis
                                )
                            elif severity_score > 0:
                                print(f"⚠️ Anomalie détectée (Score: {severity_score}) dans {log_file}")
                            else:
                                print(f"✅ Aucune anomalie dans {log_file}")
                    
                    except Exception as e:
                        print(f"❌ Erreur lors du traitement de {log_file} : {e}")

                # Vérifier s'il est temps d'envoyer le rapport quotidien
                schedule.run_pending()
                
                # Attendre avant la prochaine vérification
                time.sleep(LOG_CHECK_INTERVAL)
            
            except Exception as e:
                print(f"❌ Erreur dans la boucle principale : {e}")
                time.sleep(LOG_CHECK_INTERVAL)

    print("✅ Monitoring stopé")


# Programmer l'envoi automatique du rapport quotidien à 4h du matin
schedule.every().day.at("04:00").do(send_daily_report)

if __name__ == "__main__":
    monitor_logs()
