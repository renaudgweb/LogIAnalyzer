"""
Module de chargement de la configuration
"""
import os
import sys
from configparser import ConfigParser
from dotenv import load_dotenv


class ConfigurationError(Exception):
    """Exception levée en cas d'erreur de configuration"""
    pass


def load_configuration():
    """
    Charge la configuration depuis config.ini et .env

    Returns:
        dict: Dictionnaire contenant toute la configuration

    Raises:
        ConfigurationError: Si la configuration ne peut pas être chargée
    """
    # Charger les variables d'environnement
    env_paths = [
        '/etc/log_analyzer/.env',
        os.path.join(os.path.dirname(__file__), '../config/.env'),
        './.env'
    ]

    env_loaded = False
    for env_path in env_paths:
        if os.path.exists(env_path):
            load_dotenv(env_path)
            env_loaded = True
            print(f"🔑 Variables d'environnement chargées depuis : {env_path}")
            break

    if not env_loaded:
        print("⚠️  Aucun fichier .env trouvé, utilisation des variables système")

    # Charger config.ini
    config = ConfigParser()
    config_paths = [
        '/etc/log_analyzer/config.ini',
        os.path.join(os.path.dirname(__file__), '../config/config.ini'),
        './config.ini'
    ]

    config_loaded = False
    loaded_path = None
    for config_path in config_paths:
        if os.path.exists(config_path):
            config.read(config_path)
            config_loaded = True
            loaded_path = config_path
            print(f"📄 Configuration chargée depuis : {config_path}")
            break

    if not config_loaded:
        raise ConfigurationError(
            f"Aucun fichier config.ini trouvé dans : {config_paths}"
        )

    # Valider et construire la configuration
    try:
        configuration = {
            'log_files': [f.strip() for f in config.get('Settings', 'log_files').split(',')],
            'email_sender': config.get('Settings', 'email_sender'),
            'email_receiver': config.get('Settings', 'email_receiver'),
            'smtp_server': config.get('Settings', 'smtp_server'),
            'smtp_port': config.getint('Settings', 'smtp_port'),
            'log_check_interval': config.getint('Settings', 'log_check_interval'),
            'ai_model': config.get('Settings', 'ai_model', fallback='mistral-medium-latest'),
            'ai_temperature': config.getfloat('Settings', 'ai_temperature'),
            'ai_max_tokens': config.getint('Settings', 'ai_max_tokens'),
            'daily_report_file': config.get('Settings', 'daily_report_file'),
            'ai_api_key': os.getenv('AI_API_KEY'),
            'smtp_password': os.getenv('SMTP_PASSWORD'),
            'config_path': loaded_path
        }
    except Exception as e:
        raise ConfigurationError(f"Erreur lors de la lecture de la configuration : {e}")

    # Valider les credentials
    if not configuration['ai_api_key']:
        raise ConfigurationError("AI_API_KEY manquante dans les variables d'environnement")

    if not configuration['smtp_password']:
        raise ConfigurationError("SMTP_PASSWORD manquante dans les variables d'environnement")

    # Valider les fichiers de logs
    for log_file in configuration['log_files']:
        if not os.path.exists(log_file):
            print(f"⚠️  Attention : Le fichier {log_file} n'existe pas")

    return configuration


def validate_configuration(config):
    """
    Valide la configuration complète

    Args:
        config (dict): Configuration à valider

    Returns:
        tuple: (bool, list) - (est_valide, liste_erreurs)
    """
    errors = []

    # Vérifier les champs requis
    required_fields = [
        'log_files', 'email_sender', 'email_receiver', 'smtp_server',
        'smtp_port', 'ai_api_key', 'smtp_password'
    ]

    for field in required_fields:
        if not config.get(field):
            errors.append(f"Champ requis manquant : {field}")

    # Vérifier les emails
    if config.get('email_sender') and '@' not in config['email_sender']:
        errors.append("Format email_sender invalide")

    if config.get('email_receiver') and '@' not in config['email_receiver']:
        errors.append("Format email_receiver invalide")

    # Vérifier les valeurs numériques
    if config.get('smtp_port') and not (1 <= config['smtp_port'] <= 65535):
        errors.append("smtp_port doit être entre 1 et 65535")

    if config.get('ai_temperature') and not (0 <= config['ai_temperature'] <= 2):
        errors.append("ai_temperature doit être entre 0 et 2")

    if config.get('log_check_interval') and config['log_check_interval'] < 1:
        errors.append("log_check_interval doit être >= 1")

    return len(errors) == 0, errors


def print_configuration_summary(config):
    """Affiche un résumé de la configuration chargée"""
    print("\n" + "="*50)
    print("📊 RÉSUMÉ DE LA CONFIGURATION")
    print("="*50)
    print(f"📁 Fichiers surveillés : {len(config['log_files'])}")
    for log_file in config['log_files']:
        status = "✓" if os.path.exists(log_file) else "✗"
        print(f"   {status} {log_file}")
    print(f"📧 Email expéditeur : {config['email_sender']}")
    print(f"📧 Email destinataire : {config['email_receiver']}")
    print(f"🔧 Serveur SMTP : {config['smtp_server']}:{config['smtp_port']}")
    print(f"⏱️  Intervalle de vérification : {config['log_check_interval']}s")
    print(f"🤖 Température IA : {config['ai_temperature']}")
    print(f"🤖 Tokens max : {config['ai_max_tokens']}")
    print(f"📄 Rapport quotidien : {config['daily_report_file']}")
    print(f"🔑 Clé API IA : {'✓ Configurée' if config['ai_api_key'] else '✗ Manquante'}")
    print(f"🔑 Mot de passe SMTP : {'✓ Configuré' if config['smtp_password'] else '✗ Manquant'}")
    print("="*50 + "\n")


if __name__ == "__main__":
    """Test du chargement de configuration"""
    try:
        config = load_configuration()
        is_valid, errors = validate_configuration(config)

        print_configuration_summary(config)

        if is_valid:
            print("✅ Configuration valide !")
        else:
            print("❌ Erreurs de configuration :")
            for error in errors:
                print(f"   - {error}")
            sys.exit(1)

    except ConfigurationError as e:
        print(f"❌ Erreur : {e}")
        sys.exit(1)