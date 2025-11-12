#!/bin/bash
# Script d'installation du Log Analyzer avec utilisateur dédié
# À exécuter avec sudo

set -e  # Arrêter en cas d'erreur

echo "🚀 Installation du Log Analyzer avec utilisateur dédié"
echo "=================================================="

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Vérifier si exécuté en tant que root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Ce script doit être exécuté avec sudo${NC}"
    exit 1
fi

# Configuration
SERVICE_NAME="log-analyzer"
USER_NAME="log_analyzer"
GROUP_NAME="log_analyzer"
INSTALL_DIR="/opt/log_analyzer"
LOG_DIR="/var/log/log_analyzer"
CONFIG_DIR="/etc/log_analyzer"

echo -e "\n${YELLOW}📋 Configuration :${NC}"
echo "   Utilisateur système : $USER_NAME"
echo "   Répertoire installation : $INSTALL_DIR"
echo "   Répertoire logs : $LOG_DIR"
echo "   Répertoire config : $CONFIG_DIR"

# 1. Créer l'utilisateur système
echo -e "\n${YELLOW}👤 Création de l'utilisateur système...${NC}"
if id "$USER_NAME" &>/dev/null; then
    echo -e "${GREEN}✓${NC} L'utilisateur $USER_NAME existe déjà"
else
    useradd -r -s /usr/sbin/nologin -d /nonexistent -c "Log Analyzer Service" "$USER_NAME"
    echo -e "${GREEN}✓${NC} Utilisateur $USER_NAME créé"
fi

# 2. Ajouter l'utilisateur au groupe adm pour lire les logs
echo -e "\n${YELLOW}🔐 Ajout au groupe adm...${NC}"
usermod -aG adm "$USER_NAME"
echo -e "${GREEN}✓${NC} $USER_NAME ajouté au groupe adm"

# 3. Créer les répertoires nécessaires
echo -e "\n${YELLOW}📁 Création des répertoires...${NC}"
mkdir -p "$INSTALL_DIR"
mkdir -p "$LOG_DIR"
mkdir -p "$CONFIG_DIR"
echo -e "${GREEN}✓${NC} Répertoires créés"

# 4. Définir les permissions
echo -e "\n${YELLOW}🔒 Configuration des permissions...${NC}"
chown -R "$USER_NAME:$GROUP_NAME" "$INSTALL_DIR"
chown -R "$USER_NAME:$GROUP_NAME" "$LOG_DIR"
chown -R "$USER_NAME:$GROUP_NAME" "$CONFIG_DIR"
chmod 750 "$INSTALL_DIR"
chmod 750 "$LOG_DIR"
chmod 750 "$CONFIG_DIR"
echo -e "${GREEN}✓${NC} Permissions configurées"

# 5. Créer le fichier de configuration
echo -e "\n${YELLOW}⚙️  Création de config.ini...${NC}"
cat > "$CONFIG_DIR/config.ini" << 'EOF'
[Settings]
# Fichiers de logs à surveiller
log_files = /var/log/apache2/error.log, /var/log/apache2/access.log, /var/log/auth.log

# Configuration email
email_sender = votre_email@gmail.com
email_receiver = destinataire@gmail.com

# Configuration SMTP
smtp_server = smtp.gmail.com
smtp_port = 587

# Intervalle de vérification (secondes)
log_check_interval = 300

# Paramètres IA
ai_temperature = 0.5
ai_max_tokens = 4096

# Fichier du rapport quotidien
daily_report_file = /var/log/log_analyzer/daily_report.txt
EOF

chown "$USER_NAME:$GROUP_NAME" "$CONFIG_DIR/config.ini"
chmod 640 "$CONFIG_DIR/config.ini"
echo -e "${GREEN}✓${NC} config.ini créé dans $CONFIG_DIR"

# 6. Créer le fichier .env template
echo -e "\n${YELLOW}🔑 Création du template .env...${NC}"
cat > "$CONFIG_DIR/.env.template" << 'EOF'
# Clé API Mistral AI
# Obtenez votre clé sur : https://console.mistral.ai/
AI_API_KEY=votre_clé_mistral_ici

# Mot de passe SMTP
# Pour Gmail : utilisez un mot de passe d'application
# https://myaccount.google.com/apppasswords
SMTP_PASSWORD=votre_mot_de_passe_email_ici
EOF

cat > "$CONFIG_DIR/.env" << 'EOF'
AI_API_KEY=
SMTP_PASSWORD=
EOF

chown "$USER_NAME:$GROUP_NAME" "$CONFIG_DIR/.env"
chown "$USER_NAME:$GROUP_NAME" "$CONFIG_DIR/.env.template"
chmod 400 "$CONFIG_DIR/.env"  # Lecture seule par le propriétaire
chmod 644 "$CONFIG_DIR/.env.template"
echo -e "${GREEN}✓${NC} Fichiers .env créés"
echo -e "${YELLOW}⚠️  IMPORTANT : Éditez $CONFIG_DIR/.env avec vos vraies clés !${NC}"

# 7. Créer le service systemd
echo -e "\n${YELLOW}🔧 Création du service systemd...${NC}"
cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=Log Analyzer with AI - Security Monitoring
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER_NAME
Group=$GROUP_NAME
WorkingDirectory=$INSTALL_DIR

# Charger les variables d'environnement
EnvironmentFile=$CONFIG_DIR/.env

# Exécuter le script Python depuis le dossier src
ExecStart=/usr/bin/python3 $INSTALL_DIR/src/log_monitor.py

# Redémarrage automatique en cas d'échec
Restart=always
RestartSec=10

# Logs
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

# Restrictions de sécurité supplémentaires
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$LOG_DIR
ReadOnlyPaths=/var/log

# Limites de ressources
LimitNOFILE=1024
CPUQuota=50%
MemoryMax=512M

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✓${NC} Service systemd créé"

# 8. Instructions finales
echo -e "\n${GREEN}✅ Installation terminée !${NC}"
echo -e "\n${YELLOW}📝 Prochaines étapes :${NC}"
echo ""
echo "1. Copiez vos fichiers Python dans $INSTALL_DIR :"
echo "   ${YELLOW}sudo cp log_monitor.py $INSTALL_DIR/${NC}"
echo "   ${YELLOW}sudo chown $USER_NAME:$GROUP_NAME $INSTALL_DIR/log_monitor.py${NC}"
echo ""
echo "2. Installez les dépendances Python :"
echo "   ${YELLOW}sudo pip3 install mistralai python-dotenv schedule${NC}"
echo ""
echo "3. Éditez la configuration :"
echo "   ${YELLOW}sudo nano $CONFIG_DIR/config.ini${NC}"
echo "   ${YELLOW}sudo nano $CONFIG_DIR/.env${NC}"
echo ""
echo "4. Rechargez systemd :"
echo "   ${YELLOW}sudo systemctl daemon-reload${NC}"
echo ""
echo "5. Activez et démarrez le service :"
echo "   ${YELLOW}sudo systemctl enable $SERVICE_NAME${NC}"
echo "   ${YELLOW}sudo systemctl start $SERVICE_NAME${NC}"
echo ""
echo "6. Vérifiez le statut :"
echo "   ${YELLOW}sudo systemctl status $SERVICE_NAME${NC}"
echo ""
echo "7. Consultez les logs :"
echo "   ${YELLOW}sudo journalctl -u $SERVICE_NAME -f${NC}"
echo ""
echo -e "${GREEN}🎉 Configuration avec utilisateur dédié terminée !${NC}"