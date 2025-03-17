import os
import smtplib
# import openai
from mistralai import Mistral
import time
import datetime
import schedule
from email.mime.text import MIMEText
from concurrent.futures import ThreadPoolExecutor

# Configuration
LOG_FILES = [
                "/var/log/apache2/error.log",
                "/var/log/apache2/access.log",
                "/var/log/auth.log"
            ]
AI_API_KEY = os.getenv("AI_API_KEY")
EMAIL_SENDER = "ton_email@mail.com"
EMAIL_RECEIVER = "destinataire@mail.com"
SMTP_SERVER = "smtp.mail.com"
SMTP_PORT = 587
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
LOG_CHECK_INTERVAL = 300  # Vérification toutes les 5 minutes
AI_TEMPERATURE = 0.5  # Ajuster pour contrôler la créativité des réponses
AI_MAX_TOKENS = 500  # Limiter la longueur des réponses
DAILY_REPORT_FILE = "/var/log/log_analyzer_daily_report.txt"

# Vérifier si le fichier existe, sinon le créer
if not os.path.exists(DAILY_REPORT_FILE):
    try:
        with open(DAILY_REPORT_FILE, "w") as file:
            file.write("📊 Rapport quotidien des logs\n")
        print(f"📄 Fichier {DAILY_REPORT_FILE} créé avec succès.")
    except PermissionError:
        print(f"❌ Permission refusée : Impossible de créer {DAILY_REPORT_FILE}. Exécute le script avec sudo.")


def read_new_logs(log_file, last_position):
    """Lit les nouvelles lignes d'un fichier log depuis la dernière position lue."""
    try:
        with open(log_file, "r") as file:
            file.seek(last_position)
            new_logs = file.readlines()
            last_position = file.tell()
        return new_logs, last_position
    except FileNotFoundError:
        print(f"Fichier non trouvé : {log_file}")
        return [], last_position


def analyze_logs_with_ai(logs):
    """Analyse les logs via IA pour détecter des anomalies."""
    if not logs:
        return "Pas de nouvelles entrées dans les logs."

    # openai.api_key = AI_API_KEY
    client = Mistral(api_key=AI_API_KEY)
    # response = openai.ChatCompletion.create(
    response = client.chat.complete(
        # model="gpt-4",
        model= "mistral-large-latest",
        temperature=AI_TEMPERATURE,
        max_tokens=AI_MAX_TOKENS,
        messages=[
            {
                "role": "system",
                "content": (
                    "Tu es un expert en analyse de logs Linux."
                    "Attribue un score de gravité de 1 à 10 aux anomalies "
                    "détectées."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Analyse ces logs et attribue un score de gravité aux "
                    f"anomalies détectées :\n{''.join(logs)}"
                ),
            }
        ]
    )

    return response["choices"][0]["message"]["content"].strip()


def send_email(subject, body):
    """Envoie un email contenant l’analyse."""
    msg = MIMEText(body)
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = subject
    
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, SMTP_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        print("Email envoyé avec succès")
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email : {e}")


def send_daily_report():
    """Envoie un compte rendu quotidien des analyses de logs."""
    if os.path.exists(DAILY_REPORT_FILE):
        with open(DAILY_REPORT_FILE, "r") as file:
            report_content = file.read()

        if report_content.strip():
            subject = f"📊 Rapport quotidien des logs - {datetime.date.today()}"
            send_email(subject, report_content)

        # Réinitialiser le fichier après envoi
        open(DAILY_REPORT_FILE, "w").close()


def monitor_logs():
    """Surveille les fichiers de logs et analyse les nouvelles lignes à intervalles réguliers."""
    log_positions = {log_file: 0 for log_file in LOG_FILES}

    while True:
        with ThreadPoolExecutor() as executor:
            futures = {}
            for log_file in LOG_FILES:
                futures[log_file] = executor.submit(read_new_logs, log_file, log_positions[log_file])
            
            for log_file, future in futures.items():
                new_logs, new_position = future.result()
                log_positions[log_file] = new_position
                
                if new_logs:
                    analysis = analyze_logs_with_ai(new_logs)
                    print(f"Analyse des logs ({log_file}) :", analysis)

                    # Stocker l'analyse dans le fichier de rapport quotidien
                    with open(DAILY_REPORT_FILE, "a") as report_file:
                        report_file.write(f"\n[{log_file}]\n{analysis}\n")
                    
                    severity_score = [int(s) for s in analysis.split() if s.isdigit() and 1 <= int(s) <= 10]
                    if severity_score and max(severity_score) >= 7:
                        send_email(f"Alerte Log - Anomalie critique dans {log_file}", analysis)
        
        # Vérifier s'il est temps d'envoyer le rapport quotidien
        schedule.run_pending()
        time.sleep(LOG_CHECK_INTERVAL)

# Programmer l'envoi automatique du rapport quotidien à 4h du matin
schedule.every().day.at("04:00").do(send_daily_report)

if __name__ == "__main__":
    monitor_logs()
