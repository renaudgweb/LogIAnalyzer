#!/bin/bash
# Script de test de la configuration Log Analyzer

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🧪 TEST DE CONFIGURATION - LOG ANALYZER${NC}"
echo "=========================================="
echo ""

# Compteurs
TESTS_PASSED=0
TESTS_FAILED=0

# Fonction de test
test_item() {
    local test_name="$1"
    local test_command="$2"
    
    echo -n "  Testing $test_name... "
    
    if eval "$test_command" &>/dev/null; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

# 1. Tests de Python et dépendances
echo -e "${YELLOW}📦 Vérification de Python et des dépendances...${NC}"
test_item "Python 3" "command -v python3"
test_item "pip3" "command -v pip3"
test_item "Module mistralai" "python3 -c 'import mistralai'"
test_item "Module python-dotenv" "python3 -c 'import dotenv'"
test_item "Module schedule" "python3 -c 'import schedule'"
echo ""

# 2. Tests des fichiers de configuration
echo -e "${YELLOW}📄 Vérification des fichiers de configuration...${NC}"
test_item "config.ini exists" "[ -f /etc/log_analyzer/config.ini ] || [ -f ./config/config.ini ]"
test_item ".env exists" "[ -f /etc/log_analyzer/.env ] || [ -f ./config/.env ]"
echo ""

# 3. Tests des répertoires
echo -e "${YELLOW}📁 Vérification des répertoires...${NC}"
if [ -d "/opt/log_analyzer" ]; then
    test_item "/opt/log_analyzer" "[ -d /opt/log_analyzer ]"
    test_item "src/ directory" "[ -d /opt/log_analyzer/src ]"
    test_item "log_monitor.py" "[ -f /opt/log_analyzer/src/log_monitor.py ]"
else
    echo -e "  ${YELLOW}ℹ️  Installation en mode développement (répertoires production non trouvés)${NC}"
fi
echo ""

# 4. Tests de l'utilisateur système
echo -e "${YELLOW}👤 Vérification de l'utilisateur système...${NC}"
if id "log_analyzer" &>/dev/null; then
    test_item "Utilisateur log_analyzer" "id log_analyzer"
    test_item "Groupe adm" "id -nG log_analyzer | grep -q adm"
else
    echo -e "  ${YELLOW}ℹ️  Utilisateur log_analyzer non créé (mode développement)${NC}"
fi
echo ""

# 5. Tests du service systemd
echo -e "${YELLOW}⚙️  Vérification du service systemd...${NC}"
if [ -f "/etc/systemd/system/log-analyzer.service" ]; then
    test_item "Service installé" "[ -f /etc/systemd/system/log-analyzer.service ]"
    
    if systemctl is-active --quiet log-analyzer 2>/dev/null; then
        echo -e "  ${GREEN}✓ Service actif${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "  ${YELLOW}⚠ Service inactif${NC}"
    fi
    
    if systemctl is-enabled --quiet log-analyzer 2>/dev/null; then
        echo -e "  ${GREEN}✓ Service activé au démarrage${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "  ${YELLOW}⚠ Service non activé au démarrage${NC}"
    fi
else
    echo -e "  ${YELLOW}ℹ️  Service systemd non installé (mode développement)${NC}"
fi
echo ""

# 6. Tests des permissions
echo -e "${YELLOW}🔒 Vérification des permissions...${NC}"
if [ -f "/etc/log_analyzer/.env" ]; then
    ENV_PERMS=$(stat -c "%a" /etc/log_analyzer/.env 2>/dev/null || echo "unknown")
    if [ "$ENV_PERMS" = "400" ] || [ "$ENV_PERMS" = "600" ]; then
        echo -e "  ${GREEN}✓ Permissions .env correctes ($ENV_PERMS)${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "  ${RED}✗ Permissions .env incorrectes ($ENV_PERMS, devrait être 400 ou 600)${NC}"
        ((TESTS_FAILED++))
    fi
fi

# Test d'accès aux logs
for log_file in /var/log/auth.log /var/log/syslog; do
    if [ -f "$log_file" ]; then
        if [ -r "$log_file" ]; then
            echo -e "  ${GREEN}✓ Accès en lecture à $log_file${NC}"
            ((TESTS_PASSED++))
        else
            echo -e "  ${RED}✗ Pas d'accès en lecture à $log_file${NC}"
            ((TESTS_FAILED++))
        fi
    fi
done
echo ""

# 7. Test de configuration Python
echo -e "${YELLOW}🐍 Test de chargement de la configuration Python...${NC}"
if [ -f "./src/config_loader.py" ]; then
    if python3 src/config_loader.py 2>&1 | grep -q "Configuration valide"; then
        echo -e "  ${GREEN}✓ Configuration Python valide${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "  ${RED}✗ Erreur dans la configuration Python${NC}"
        echo -e "  ${YELLOW}Détails :${NC}"
        python3 src/config_loader.py 2>&1 | head -n 10
        ((TESTS_FAILED++))
    fi
else
    echo -e "  ${YELLOW}ℹ️  Fichier config_loader.py non trouvé${NC}"
fi
echo ""

# 8. Test d'envoi d'email (optionnel)
echo -e "${YELLOW}📧 Test d'envoi d'email...${NC}"
read -p "Voulez-vous tester l'envoi d'email ? (o/N) : " -n 1 -r
echo
if [[ $REPLY =~ ^[Oo]$ ]]; then
    if [ -f "./src/email_sender.py" ]; then
        echo -e "  ${BLUE}Envoi d'un email de test...${NC}"
        if python3 src/email_sender.py 2>&1 | grep -q "Test réussi"; then
            echo -e "  ${GREEN}✓ Email envoyé avec succès${NC}"
            ((TESTS_PASSED++))
        else
            echo -e "  ${RED}✗ Échec de l'envoi d'email${NC}"
            ((TESTS_FAILED++))
        fi
    fi
else
    echo -e "  ${YELLOW}⊘ Test d'email ignoré${NC}"
fi
echo ""

# Résumé
echo "=========================================="
echo -e "${BLUE}📊 RÉSUMÉ DES TESTS${NC}"
echo "=========================================="
TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
echo -e "Total de tests : ${BLUE}$TOTAL_TESTS${NC}"
echo -e "Tests réussis : ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests échoués : ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ Tous les tests sont passés !${NC}"
    echo -e "${GREEN}Le système est prêt à être utilisé.${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Certains tests ont échoué.${NC}"
    echo -e "${YELLOW}Vérifiez la configuration avant de démarrer le service.${NC}"
    exit 1
fi