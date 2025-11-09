#!/bin/bash
# Script de désinstallation du Log Analyzer
# À exécuter avec sudo

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Vérifier si exécuté en tant que root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Ce script doit être exécuté avec sudo${NC}"
    exit 1
fi

echo -e "${RED}🗑️  DÉSINSTALLATION DU LOG ANALYZER${NC}"
echo "========================================"
echo ""
echo -e "${YELLOW}⚠️  ATTENTION : Cette action va :${NC}"
echo "   - Arrêter et désactiver le service"
echo "   - Supprimer l'utilisateur système log_analyzer"
echo "   - Supprimer tous les fichiers d'installation"
echo "   - Supprimer les fichiers de configuration"
echo -e "${YELLOW}   - Supprimer les logs et rapports${NC}"
echo ""

read -p "Êtes-vous sûr de vouloir continuer ? (oui/non) : " -r
echo
if [[ ! $REPLY =~ ^[Oo]ui$ ]]; then
    echo "Désinstallation annulée."
    exit 0
fi

SERVICE_NAME="log-analyzer"
USER_NAME="log_analyzer"
INSTALL_DIR="/opt/log_analyzer"
LOG_DIR="/var/log/log_analyzer"
CONFIG_DIR="/etc/log_analyzer"

# 1. Arrêter et désactiver le service
echo -e "\n${YELLOW}🛑 Arrêt du service...${NC}"
if systemctl is-active --quiet "$SERVICE_NAME"; then
    systemctl stop "$SERVICE_NAME"
    echo -e "${GREEN}✓${NC} Service arrêté"
else
    echo -e "${GREEN}✓${NC} Service déjà arrêté"
fi

if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
    systemctl disable "$SERVICE_NAME"
    echo -e "${GREEN}✓${NC} Service désactivé"
fi

# 2. Supprimer le fichier service systemd
echo -e "\n${YELLOW}🗑️  Suppression du service systemd...${NC}"
if [ -f "/etc/systemd/system/$SERVICE_NAME.service" ]; then
    rm "/etc/systemd/system/$SERVICE_NAME.service"
    systemctl daemon-reload
    echo -e "${GREEN}✓${NC} Fichier service supprimé"
fi

# 3. Sauvegarder les configurations et logs (optionnel)
echo -e "\n${YELLOW}💾 Sauvegarde des données...${NC}"
BACKUP_DIR="/tmp/log_analyzer_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

if [ -d "$CONFIG_DIR" ]; then
    cp -r "$CONFIG_DIR" "$BACKUP_DIR/" 2>/dev/null || true
fi

if [ -d "$LOG_DIR" ]; then
    cp -r "$LOG_DIR" "$BACKUP_DIR/" 2>/dev/null || true
fi

if [ "$(ls -A $BACKUP_DIR 2>/dev/null)" ]; then
    echo -e "${GREEN}✓${NC} Sauvegarde créée dans : $BACKUP_DIR"
else
    rm -rf "$BACKUP_DIR"
    echo -e "${GREEN}✓${NC} Aucune donnée à sauvegarder"
fi

# 4. Supprimer les répertoires
echo -e "\n${YELLOW}🗑️  Suppression des répertoires...${NC}"
for dir in "$INSTALL_DIR" "$LOG_DIR" "$CONFIG_DIR"; do
    if [ -d "$dir" ]; then
        rm -rf "$dir"
        echo -e "${GREEN}✓${NC} Supprimé : $dir"
    fi
done

# 5. Supprimer l'utilisateur système
echo -e "\n${YELLOW}👤 Suppression de l'utilisateur système...${NC}"
if id "$USER_NAME" &>/dev/null; then
    userdel "$USER_NAME" 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Utilisateur $USER_NAME supprimé"
else
    echo -e "${GREEN}✓${NC} Utilisateur déjà supprimé"
fi

# Supprimer le groupe s'il existe encore
if getent group "$USER_NAME" &>/dev/null; then
    groupdel "$USER_NAME" 2>/dev/null || true
fi

echo -e "\n${GREEN}✅ Désinstallation terminée !${NC}"

if [ -d "$BACKUP_DIR" ]; then
    echo -e "\n${YELLOW}💾 Une sauvegarde a été créée :${NC}"
    echo "   $BACKUP_DIR"
    echo -e "\n${YELLOW}Pour restaurer vos données plus tard :${NC}"
    echo "   sudo cp -r $BACKUP_DIR/log_analyzer /etc/"
    echo "   sudo cp -r $BACKUP_DIR/log_analyzer /var/log/"
fi

echo ""