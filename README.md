# 🕵️‍♂️ LogIAnalyzer - Surveillance et Analyse des Logs avec IA

<p align="center">
  <img src="logianalyzer.jpg" alt="LogIAnalyzer Logo" width="600"/>
</p>

<p align="center">
  <a href="https://github.com/renaudgweb/LogIAnalyzer/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python version"></a>
</p>

Système automatisé de surveillance et d'analyse de logs Linux utilisant l'intelligence artificielle (Mistral AI) pour détecter les anomalies de sécurité et générer des alertes en temps réel.

## 🌟 Fonctionnalités

- **Surveillance en temps réel** des fichiers de logs système
- **Analyse intelligente** via Mistral AI pour détecter les anomalies
- **Système de scoring** de gravité (1-10) pour prioriser les alertes
- **Alertes email** automatiques pour les incidents critiques (score ≥ 7)
- **Rapport quotidien** automatique envoyé à 04h00
- **Architecture sécurisée** avec utilisateur système dédié
- **Recommandations automatiques** pour résoudre les problèmes détectés

## 📋 Prérequis

- **OS** : Linux (Ubuntu 20.04+, Debian 11+, ou compatible)
- **Python** : 3.8 ou supérieur
- **Permissions** : Accès root/sudo pour l'installation
- **Compte Mistral AI** : [console.mistral.ai](https://console.mistral.ai/)
- **Compte email** : Gmail, Outlook, ou autre serveur SMTP

## 🚀 Installation rapide

### 1. Cloner le repository

```bash
git clone https://github.com/renaudgweb/log-analyzer.git
cd log-analyzer
```

### 2. Rendre les scripts exécutables

```bash
chmod +x scripts/*.sh
```

### 3. Installer le système

```bash
sudo ./scripts/setup-log-analyzer.sh
```

### 4. Configurer les paramètres

```bash
# Éditer la configuration principale
sudo nano /etc/log_analyzer/config.ini

# Ajouter les secrets (clés API, mots de passe)
sudo nano /etc/log_analyzer/.env
```

### 5. Démarrer le service

```bash
sudo systemctl start log-analyzer
sudo systemctl enable log-analyzer  # Pour démarrage automatique
```

## 📁 Structure du projet

```
log-analyzer/
├── src/
│   ├── __init__.py              # Package Python
│   ├── log_monitor.py           # Script principal
│   ├── config_loader.py         # Chargement de configuration
│   └── email_sender.py          # Gestion des emails
├── config/
│   ├── config.ini.example       # Template de configuration
│   └── .env.example             # Template des secrets
├── systemd/
│   └── log-analyzer.service     # Service systemd
├── scripts/
│   ├── setup-log-analyzer.sh    # Installation
│   ├── uninstall-log-analyzer.sh # Désinstallation
│   └── test-config.sh           # Test de configuration
├── docs/
│   ├── installation.md
│   ├── configuration.md
│   └── troubleshooting.md
├── requirements.txt
├── README.md
└── .gitignore
```

## ⚙️ Configuration

### Fichier config.ini

```ini
[Settings]
log_files = /var/log/apache2/error.log, /var/log/auth.log
email_sender = votre_email@gmail.com
email_receiver = destinataire@gmail.com
smtp_server = smtp.gmail.com
smtp_port = 587
log_check_interval = 300
ai_temperature = 0.5
ai_max_tokens = 4096
daily_report_file = /var/log/log_analyzer/daily_report.txt
```

### Fichier .env

```bash
AI_API_KEY=votre_clé_mistral
SMTP_PASSWORD=votre_mot_de_passe_app_gmail
```

## 🔧 Commandes utiles

### Gestion du service

```bash
# Démarrer
sudo systemctl start log-analyzer

# Arrêter
sudo systemctl stop log-analyzer

# Redémarrer
sudo systemctl restart log-analyzer

# Statut
sudo systemctl status log-analyzer

# Activer au démarrage
sudo systemctl enable log-analyzer

# Désactiver au démarrage
sudo systemctl disable log-analyzer
```

### Consultation des logs

```bash
# Logs en temps réel
sudo journalctl -u log-analyzer -f

# Dernières 100 lignes
sudo journalctl -u log-analyzer -n 100

# Logs d'aujourd'hui
sudo journalctl -u log-analyzer --since today

# Logs avec priorité error ou supérieur
sudo journalctl -u log-analyzer -p err
```

### Tests

```bash
# Tester la configuration
./scripts/test-config.sh

# Tester le chargement de config Python
python3 src/config_loader.py

# Tester l'envoi d'email
python3 src/email_sender.py
```

## 📧 Configuration Gmail

Pour utiliser Gmail, vous devez créer un **mot de passe d'application** :

1. Activez la validation en 2 étapes sur votre compte Google
2. Allez sur [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Sélectionnez "Mail" et "Autre appareil"
4. Copiez le mot de passe de 16 caractères généré
5. Utilisez-le dans votre fichier `.env`

## 🔐 Sécurité

Le système est conçu avec les meilleures pratiques de sécurité :

- **Utilisateur dédié** sans shell interactif
- **Permissions minimales** (principe du moindre privilège)
- **Isolation complète** via systemd
- **Secrets protégés** (permissions 400 sur .env)
- **Restrictions système** (NoNewPrivileges, ProtectSystem, etc.)

## 📊 Système de scoring

Les anomalies sont notées de 1 à 10 :

- **1-3** : Anomalie bénigne (log uniquement)
- **4-6** : Anomalie modérée (log et rapport quotidien)
- **7-10** : Anomalie critique (log, rapport ET alerte email immédiate)

## 🐛 Dépannage

### Le service ne démarre pas

```bash
# Vérifier les logs d'erreur
sudo journalctl -u log-analyzer -n 50

# Vérifier les permissions
ls -la /etc/log_analyzer/
ls -la /opt/log_analyzer/
```

### Pas d'accès aux fichiers de logs

```bash
# Vérifier les groupes de l'utilisateur
id log_analyzer

# Doit afficher "adm" dans les groupes
# Sinon, ajouter manuellement :
sudo usermod -aG adm log_analyzer
sudo systemctl restart log-analyzer
```

### Emails non reçus

```bash
# Tester la configuration email
python3 src/email_sender.py

# Vérifier les logs SMTP
sudo journalctl -u log-analyzer | grep -i smtp
```

## 📚 Documentation

- [Guide d'installation](docs/installation.md)
- [Guide de configuration](docs/configuration.md)
- [Résolution de problèmes](docs/troubleshooting.md)

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :

- Signaler des bugs
- Proposer des nouvelles fonctionnalités
- Améliorer la documentation
- Soumettre des pull requests

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 👤 Auteur

renaudG

## 🙏 Remerciements

- [Mistral AI](https://mistral.ai/) pour l'API d'analyse
- La communauté open source pour les bibliothèques utilisées

---

**⚠️ Note de sécurité** : Ne commettez JAMAIS vos fichiers `.env` ou `config.ini` avec des vraies valeurs. Utilisez toujours les fichiers `.example` comme templates.
