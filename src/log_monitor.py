"""
Log Monitor - Surveillance et analyse automatique des logs avec IA
"""
import os
import re
import signal
import sys
import time
import datetime
import schedule
from mistralai import Mistral
from concurrent.futures import ThreadPoolExecutor

# Imports locaux
from config_loader import load_configuration, print_configuration_summary, validate_configuration
from email_sender import send_alert_email, send_daily_report

# Variable globale pour arrêt propre
shutdown_flag = False


def signal_handler(sig, frame):
    """Gestionnaire de signal pour arrêt propre"""
    global shutdown_flag
    print("\n🛑 Arrêt du monitoring en cours...")
    shutdown_flag = True


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def read_new_logs(log_file, last_position):
    """
    Lit les nouvelles lignes d'un fichier log depuis la dernière position lue

    Args:
        log_file (str): Chemin du fichier de log
        last_position (int): Position du dernier octet lu

    Returns:
        tuple: (nouvelles_lignes, nouvelle_position)
    """
    try:
        with open(log_file, "r", encoding='utf-8', errors='ignore') as file:
            file.seek(last_position)
            new_logs = file.readlines()
            last_position = file.tell()
        return new_logs, last_position

    except FileNotFoundError:
        print(f"⚠️  Fichier non trouvé : {log_file}")
        return [], last_position

    except PermissionError:
        print(f"❌ Permission refusée pour lire : {log_file}")
        return [], last_position

    except Exception as e:
        print(f"❌ Erreur lors de la lecture de {log_file} : {e}")
        return [], last_position


def analyze_logs_with_ai(logs, config):
    """
    Analyse les logs via IA pour détecter des anomalies

    Args:
        logs (list): Liste des lignes de logs à analyser
        config (dict): Configuration contenant les paramètres IA

    Returns:
        str: Analyse générée par l'IA
    """
    if not logs:
        return "SEVERITY_SCORE: 0\nPas de nouvelles entrées dans les logs."

    try:
        client = Mistral(api_key=config['ai_api_key'])

        # Log du modèle utilisé (pour debug)
        model = config.get('ai_model', 'mistral-medium-latest')

        response = client.chat.complete(
            model=model,
            temperature=config['ai_temperature'],
            max_tokens=config['ai_max_tokens'],
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

        return response.choices[0].message.content.strip()

    except Exception as e:
        error_msg = f"❌ Erreur lors de l'analyse IA (modèle: {config.get('ai_model', 'unknown')}): {e}"
        print(error_msg)
        return f"SEVERITY_SCORE: 0\nErreur d'analyse IA - Impossible de traiter les logs.\nDétails: {e}"


def extract_severity_score(analysis):
    """
    Extrait le score de gravité de l'analyse

    Args:
        analysis (str): Texte d'analyse contenant le score

    Returns:
        int: Score de gravité entre 0 et 10
    """
    match = re.search(r'SEVERITY_SCORE:\s*(\d+)', analysis)
    if match:
        score = int(match.group(1))
        return max(0, min(10, score))
    return 0


def save_analysis_to_report(log_file, analysis, config):
    """
    Sauvegarde l'analyse dans le fichier de rapport quotidien

    Args:
        log_file (str): Nom du fichier de log analysé
        analysis (str): Résultat de l'analyse
        config (dict): Configuration
    """
    try:
        with open(config['daily_report_file'], "a", encoding='utf-8') as report_file:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            report_file.write(f"\n[{timestamp}] [{log_file}]\n{analysis}\n")
    except PermissionError:
        print(f"❌ Permission refusée pour écrire dans {config['daily_report_file']}")
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde du rapport : {e}")


def process_log_file(log_file, last_position, config):
    """
    Traite un fichier de log : lecture, analyse et alertes

    Args:
        log_file (str): Chemin du fichier de log
        last_position (int): Position du dernier octet lu
        config (dict): Configuration

    Returns:
        int: Nouvelle position dans le fichier
    """
    new_logs, new_position = read_new_logs(log_file, last_position)

    if new_logs:
        print(f"🔍 Analyse de {len(new_logs)} nouvelles lignes dans {log_file}...")
        analysis = analyze_logs_with_ai(new_logs, config)

        # Sauvegarder dans le rapport quotidien
        save_analysis_to_report(log_file, analysis, config)

        # Extraire et vérifier le score de gravité
        severity_score = extract_severity_score(analysis)

        if severity_score >= 7:
            print(f"🚨 ALERTE CRITIQUE (Score: {severity_score}) détectée dans {log_file}")
            send_alert_email(log_file, analysis, severity_score, config)
        elif severity_score > 0:
            print(f"⚠️  Anomalie détectée (Score: {severity_score}) dans {log_file}")
        else:
            print(f"✅ Aucune anomalie dans {log_file}")

    return new_position


def initialize_daily_report(config):
    """
    Initialise le fichier de rapport quotidien s'il n'existe pas

    Args:
        config (dict): Configuration
    """
    daily_report_file = config['daily_report_file']

    if not os.path.exists(daily_report_file):
        try:
            # Créer le répertoire parent si nécessaire
            os.makedirs(os.path.dirname(daily_report_file), exist_ok=True)

            with open(daily_report_file, "w", encoding='utf-8') as file:
                file.write("📊 Rapport quotidien des logs\n")
            print(f"📄 Fichier {daily_report_file} créé avec succès.")
        except PermissionError:
            print(f"❌ Permission refusée : Impossible de créer {daily_report_file}")
            print("   Exécutez le script avec les permissions appropriées.")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Erreur lors de la création du fichier de rapport : {e}")
            sys.exit(1)


def monitor_logs(config):
    """
    Surveille les fichiers de logs et analyse les nouvelles lignes à intervalles réguliers

    Args:
        config (dict): Configuration complète du système
    """
    log_positions = {log_file: 0 for log_file in config['log_files']}

    print(f"🚀 Démarrage du monitoring des logs...")
    print(f"📁 Fichiers surveillés : {', '.join(config['log_files'])}")
    print(f"⏱️  Intervalle de vérification : {config['log_check_interval']}s")
    print(f"📧 Alertes envoyées à : {config['email_receiver']}")
    print(f"🕓 Rapport quotidien programmé à 04:00\n")

    # Initialiser le fichier de rapport
    initialize_daily_report(config)

    # Créer le ThreadPoolExecutor une seule fois
    with ThreadPoolExecutor(max_workers=len(config['log_files'])) as executor:
        while not shutdown_flag:
            try:
                futures = {}
                for log_file in config['log_files']:
                    futures[log_file] = executor.submit(
                        process_log_file,
                        log_file,
                        log_positions[log_file],
                        config
                    )

                for log_file, future in futures.items():
                    try:
                        log_positions[log_file] = future.result(timeout=60)
                    except Exception as e:
                        print(f"❌ Erreur lors du traitement de {log_file} : {e}")

                # Vérifier s'il est temps d'envoyer le rapport quotidien
                schedule.run_pending()

                # Attendre avant la prochaine vérification
                time.sleep(config['log_check_interval'])

            except Exception as e:
                print(f"❌ Erreur dans la boucle principale : {e}")
                time.sleep(config['log_check_interval'])

    print("✅ Monitoring arrêté proprement")


def main():
    """Point d'entrée principal du programme"""
    print("="*60)
    print("  🔍 LOG ANALYZER WITH AI")
    print("  Surveillance et analyse automatique des logs Linux")
    print("="*60 + "\n")

    try:
        # Charger la configuration
        config = load_configuration()

        # Valider la configuration
        is_valid, errors = validate_configuration(config)
        if not is_valid:
            print("❌ Configuration invalide :")
            for error in errors:
                print(f"   - {error}")
            sys.exit(1)

        # Afficher le résumé de la configuration
        print_configuration_summary(config)

        # Programmer le rapport quotidien
        schedule.every().day.at("04:00").do(send_daily_report, config)

        # Démarrer le monitoring
        monitor_logs(config)

    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé par l'utilisateur")
        sys.exit(0)

    except Exception as e:
        print(f"❌ Erreur fatale : {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()