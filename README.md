# 🚀 LogIAnalyzer

<p align="center">
  <a href="https://github.com/renaudgweb/LogIAnalyzer/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python version"></a>
</p>

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
User=root  # Sinon, remplace par l’utilisateur qui a accès aux logs
ExecStart=/usr/bin/python3 /chemin/vers/logianalyzer.py
WorkingDirectory=/chemin/vers/LogIAnalyzer
Restart=always
User=ton_utilisateur
Environment="AI_API_KEY=${AI_API_KEY}"
Environment="SMTP_PASSWORD=${SMTP_PASSWORD}"

[Install]
WantedBy=multi-user.target
```

### (Ajouter l’utilisateur au groupe "adm", qui a accès aux logs, si besoin)
```bash
sudo usermod -aG adm myuser # Remplace par l’utilisateur qui a accès aux logs
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

LogIAnalyzer is released under the [MIT License](LICENSE).

```
MIT License

Copyright (c) 2025 RenaudG

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
