# 🚀 LogIAnalyzer

## 📌 Description
Ce script analyse en continu les logs des requêtes arrivant sur le serveur web (Nginx/Apache) et détecte des anomalies à l'aide de l'API OpenAI. Il envoie une alerte par e-mail en cas de problème critique.

## ✅ Prérequis
- 🐍 Python 3
- 🔑 Un compte OpenAI avec une clé API
- 📧 Un serveur SMTP pour l'envoi d'e-mails
- 📂 Un accès aux fichiers logs du serveur web

## 🔧 Installation

### 1️⃣ Cloner le dépôt
```bash
git clone https://github.com/ton-utilisateur/LogIAnalyzer.git
cd LogIAnalyzer
```

### 2️⃣ Installer les dépendances
```bash
pip install -r requirements.txt
```

### 3️⃣ Configurer les variables d'environnement
Ajoute ces variables dans `/etc/environment` :
```bash
AI_API_KEY="ta_cle_api"
SMTP_PASSWORD="ton_mot_de_passe"
```
Recharge les variables :
```bash
source /etc/environment
```

### 4️⃣ Configurer `systemd` pour un démarrage automatique
Crée un fichier de service :
```bash
sudo nano /etc/systemd/system/logianalyzer.service
```
Ajoute ceci :
```ini
[Unit]
Description=🚀 Surveillance et analyse des logs serveur
After=network.target

[Service]
ExecStart=/usr/bin/python3 /chemin/vers/logianalyzer.py
WorkingDirectory=/chemin/vers/LogIAnalyzer
Restart=always
User=ton_utilisateur
Environment="AI_API_KEY=${AI_API_KEY}"
Environment="SMTP_PASSWORD=${SMTP_PASSWORD}"

[Install]
WantedBy=multi-user.target
```

### 5️⃣ Activer et démarrer le service
```bash
sudo systemctl daemon-reload
sudo systemctl enable logianalyzer
sudo systemctl start logianalyzer
```

### 6️⃣ Vérifier que le service fonctionne
```bash
sudo systemctl status logianalyzer
```

## 🔍 Logs et Debugging
- 📜 Consulter les logs du service :
```bash
journalctl -u logianalyzer -f
```
- 🔄 Redémarrer le service après modification :
```bash
sudo systemctl restart logianalyzer
```

## ❌ Désinstallation
Désactiver et supprimer le service :
```bash
sudo systemctl stop logianalyzer
sudo systemctl disable logianalyzer
sudo rm /etc/systemd/system/logianalyzer.service
sudo systemctl daemon-reload
```

## 📜 Licence
📝 MIT License
