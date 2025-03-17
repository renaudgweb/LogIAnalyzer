import os
import smtplib
# import openai
from mistralai import Mistral
import time
import datetime
import schedule
from email.mime.text import MIMEText
from concurrent.futures import ThreadPoolExecutor
from configparser import ConfigParser

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

# Vérifier si le fichier existe, sinon le créer
if not os.path.exists(DAILY_REPORT_FILE):
    try:
        with open(DAILY_REPORT_FILE, "w") as file:
            file.write("📊 Rapport quotidien des logs\n")
        print(f"📄 Fichier {DAILY_REPORT_FILE} créé avec succès.")
    except PermissionError:
        print(f"❌ Permission refusée : Impossible de créer "
              f"{DAILY_REPORT_FILE}. Exécute le script avec sudo.")


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
        messages = [
            {
                "role": "system",
                "content": (
                    "Tu es un expert en cybersécurité et en analyse "
                    "de logs Linux. "
                    "Pour chaque anomalie détectée, attribue un score "
                    "de gravité de 1 à 10, où 1 signifie une anomalie "
                    "bénigne et 10 représente une situation critique "
                    "qui nécessite une action immédiate. "
                    "En plus du score, si possible, propose une action "
                    "ou une recommandation pour résoudre ou atténuer "
                    "l'anomalie. Sois précis et clair dans ton analyse."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Analyse les logs suivants et attribue un score de "
                    f"gravité aux anomalies détectées, en suivant les "
                    f"critères ci-dessus. Pour chaque anomalie, propose "
                    f"une solution ou une recommandation si possible :"
                    f"\n{''.join(logs)}"
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
