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
git clone https://github.com/ton-utilisateur/logwatch-analyzer.git
cd logwatch-analyzer
```

### 2️⃣ Installer les dépendances
```bash
pip install -r requirements.txt
```

### 3️⃣ Configurer les variables d'environnement
Ajoute ces variables dans `/etc/environment` :
```bash
OPENAI_API_KEY="ta_cle_api"
SMTP_PASSWORD="ton_mot_de_passe"
```
Recharge les variables :
```bash
source /etc/environment
```

### 4️⃣ Configurer `systemd` pour un démarrage automatique
Crée un fichier de service :
```bash
sudo nano /etc/systemd/system/logwatch_analyzer.service
```
Ajoute ceci :
```ini
[Unit]
Description=🚀 Surveillance et analyse des logs serveur
After=network.target

[Service]
ExecStart=/usr/bin/python3 /chemin/vers/logwatch_analyzer.py
WorkingDirectory=/chemin/vers/logwatch-analyzer
Restart=always
User=ton_utilisateur
Environment="OPENAI_API_KEY=${OPENAI_API_KEY}"
Environment="SMTP_PASSWORD=${SMTP_PASSWORD}"

[Install]
WantedBy=multi-user.target
```

### 5️⃣ Activer et démarrer le service
```bash
sudo systemctl daemon-reload
sudo systemctl enable logwatch_analyzer
sudo systemctl start logwatch_analyzer
```

### 6️⃣ Vérifier que le service fonctionne
```bash
sudo systemctl status logwatch_analyzer
```

## 🔍 Logs et Debugging
- 📜 Consulter les logs du service :
```bash
journalctl -u logwatch_analyzer -f
```
- 🔄 Redémarrer le service après modification :
```bash
sudo systemctl restart logwatch_analyzer
```

## ❌ Désinstallation
Désactiver et supprimer le service :
```bash
sudo systemctl stop logwatch_analyzer
sudo systemctl disable logwatch_analyzer
sudo rm /etc/systemd/system/logwatch_analyzer.service
sudo systemctl daemon-reload
```

## 📜 Licence
📝 MIT License
