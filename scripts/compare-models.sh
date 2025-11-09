#!/bin/bash
# Script de comparaison des modèles Mistral AI
# Permet de tester différents modèles sur les mêmes logs

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🤖 COMPARATEUR DE MODÈLES MISTRAL AI${NC}"
echo "========================================"
echo ""

# Configuration
CONFIG_FILE="/etc/log_analyzer/config.ini"
TEST_LOG_FILE="/tmp/test_logs.txt"

# Vérifier si le fichier de config existe
if [ ! -f "$CONFIG_FILE" ]; then
    CONFIG_FILE="./config/config.ini"
fi

if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}❌ Fichier de configuration non trouvé${NC}"
    exit 1
fi

# Modèles à tester
MODELS=(
    "mistral-large-latest"
    "mistral-medium-latest"
    "mistral-small-latest"
    "open-mixtral-8x22b"
    "open-mixtral-8x7b"
    "open-mistral-7b"
)

# Créer un fichier de logs de test
echo -e "${YELLOW}📝 Création des logs de test...${NC}"
cat > "$TEST_LOG_FILE" << 'EOF'
Nov 09 10:15:32 server sshd[12345]: Failed password for invalid user admin from 192.168.1.100 port 52342 ssh2
Nov 09 10:15:33 server sshd[12345]: Failed password for invalid user admin from 192.168.1.100 port 52342 ssh2
Nov 09 10:15:34 server sshd[12345]: Failed password for invalid user admin from 192.168.1.100 port 52342 ssh2
Nov 09 10:15:35 server kernel: [12345.678901] Out of memory: Kill process 1234 (apache2) score 912 or sacrifice child
Nov 09 10:16:00 server apache2[5678]: [error] [client 192.168.1.200] File does not exist: /var/www/html/wp-admin
Nov 09 10:16:01 server apache2[5678]: [error] [client 192.168.1.200] File does not exist: /var/www/html/.env
Nov 09 10:17:00 server systemd[1]: nginx.service: Main process exited, code=exited, status=1/FAILURE
EOF

echo -e "${GREEN}✓${NC} Logs de test créés : $TEST_LOG_FILE"
echo ""

# Sauvegarder le modèle actuel
ORIGINAL_MODEL=$(grep "^ai_model" "$CONFIG_FILE" | cut -d'=' -f2 | xargs)
echo -e "${YELLOW}📌 Modèle actuel : $ORIGINAL_MODEL${NC}"
echo ""

# Demander confirmation
read -p "Voulez-vous tester tous les modèles ? (o/N) : " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Oo]$ ]]; then
    echo "Test annulé."
    exit 0
fi

echo ""
echo -e "${BLUE}🧪 DÉBUT DES TESTS${NC}"
echo "========================================"

# Créer un fichier de résultats
RESULTS_FILE="/tmp/model_comparison_$(date +%Y%m%d_%H%M%S).txt"
echo "Comparaison des modèles Mistral AI - $(date)" > "$RESULTS_FILE"
echo "======================================" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"

# Fonction pour tester un modèle
test_model() {
    local model=$1
    echo -e "\n${YELLOW}🔍 Test du modèle : $model${NC}"
    echo "----------------------------------------"
    
    # Modifier le config.ini temporairement
    sudo sed -i.bak "s/^ai_model.*/ai_model = $model/" "$CONFIG_FILE"
    
    # Créer un script Python temporaire pour tester
    cat > /tmp/test_ai_model.py << PYEOF
import sys
sys.path.insert(0, './src')
sys.path.insert(0, '/opt/log_analyzer/src')

from config_loader import load_configuration
from log_monitor import analyze_logs_with_ai
import time

try:
    config = load_configuration()
    
    with open('$TEST_LOG_FILE', 'r') as f:
        logs = f.readlines()
    
    start_time = time.time()
    analysis = analyze_logs_with_ai(logs, config)
    end_time = time.time()
    
    print(f"Modèle: $model")
    print(f"Temps: {end_time - start_time:.2f}s")
    print(f"Analyse:")
    print(analysis)
    print("\n" + "="*60 + "\n")
    
except Exception as e:
    print(f"ERREUR: {e}")
    sys.exit(1)
PYEOF
    
    # Exécuter le test
    if python3 /tmp/test_ai_model.py 2>&1 | tee -a "$RESULTS_FILE"; then
        echo -e "${GREEN}✓ Test réussi${NC}"
    else
        echo -e "${RED}✗ Test échoué${NC}"
    fi
    
    echo "----------------------------------------"
    sleep 2
}

# Tester chaque modèle
for model in "${MODELS[@]}"; do
    test_model "$model"
done

# Restaurer le modèle original
echo -e "\n${YELLOW}🔄 Restauration du modèle original...${NC}"
sudo sed -i "s/^ai_model.*/ai_model = $ORIGINAL_MODEL/" "$CONFIG_FILE"
echo -e "${GREEN}✓${NC} Modèle restauré : $ORIGINAL_MODEL"

# Nettoyer
rm -f /tmp/test_ai_model.py
rm -f "$CONFIG_FILE.bak"

echo ""
echo -e "${GREEN}✅ TESTS TERMINÉS${NC}"
echo "========================================"
echo -e "${BLUE}📊 Résultats sauvegardés dans : $RESULTS_FILE${NC}"
echo ""
echo -e "${YELLOW}📝 Pour voir les résultats :${NC}"
echo "   cat $RESULTS_FILE"
echo ""
echo -e "${YELLOW}💡 Recommandations :${NC}"
echo "   - Comparez les temps de réponse"
echo "   - Vérifiez la qualité des analyses"
echo "   - Évaluez le rapport qualité/prix"
echo ""