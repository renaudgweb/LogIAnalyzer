from dotenv import load_dotenv
import os
import smtplib
# import openai
from mistralai import Mistral
from email.mime.text import MIMEText

load_dotenv()

# Configuration
LOGWATCH_REPORT_PATH = "/var/log/logwatch_report.log"
API_KEY = os.getenv("API_KEY")
EMAIL_SENDER = "ton_email@gmail.com"
EMAIL_RECEIVER = "destinataire@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


def read_logwatch_report():
    """Lit le rapport Logwatch."""
    if not os.path.exists(LOGWATCH_REPORT_PATH):
        print("Fichier de log introuvable")
        return None
    with open(LOGWATCH_REPORT_PATH, "r") as file:
        return file.read()


def analyze_logs_with_ai(logs):
    """Analyse les logs via AI pour détecter des anomalies."""
    # openai.api_key = API_KEY
    client = Mistral(api_key=API_KEY)
    # response = openai.ChatCompletion.create(
    response = client.chat.complete(
        # model="gpt-4",
        model= "mistral-large-latest",
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
                    f"anomalies détectées :\n{logs}"
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


__name__ == "__main__":
    logs = read_logwatch_report()
    if logs:
        analysis = analyze_logs_with_openai(logs)
        send_email("Analyse des logs :", analysis)

        # Extraire un score de gravité et envoyer un email si nécessaire
        severity_score = [
            int(s) for s in analysis.split()
            if s.isdigit() and 1 <= int(s) <= 10
        ]
        if severity_score and max(severity_score) >= 7:
            send_email("Alerte Logwatch - Anomalie critique", analysis)
