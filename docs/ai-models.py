# 🤖 Guide des modèles Mistral AI

## Modèles disponibles

Le Log Analyzer supporte tous les modèles Mistral AI. Voici un guide pour choisir le bon modèle.

## 📊 Comparaison des modèles

| Modèle | Performance | Coût | Vitesse | Recommandé pour |
|--------|-------------|------|---------|-----------------|
| **mistral-large-latest** | ⭐⭐⭐⭐⭐ | 💰💰💰 | 🐢🐢 | Production (meilleure qualité) |
| **mistral-medium-latest** | ⭐⭐⭐⭐ | 💰💰 | 🐢 | Production équilibrée |
| **mistral-small-latest** | ⭐⭐⭐ | 💰 | 🚀 | Tests, faible volume |
| **open-mixtral-8x22b** | ⭐⭐⭐⭐ | 💰💰 | 🐢 | Open source performant |
| **open-mixtral-8x7b** | ⭐⭐⭐ | 💰 | 🚀 | Open source économique |
| **open-mistral-7b** | ⭐⭐ | Gratuit | 🚀🚀 | Développement/tests |

## 🎯 Recommandations par cas d'usage

### Production - Haute qualité
```ini
ai_model = mistral-large-latest
ai_temperature = 0.5
ai_max_tokens = 4096
```
**Avantages :** Meilleure détection d'anomalies, analyses plus précises, recommandations détaillées  
**Inconvénients :** Coût élevé, plus lent

### Production - Équilibré (RECOMMANDÉ)
```ini
ai_model = mistral-medium-latest
ai_temperature = 0.5
ai_max_tokens = 4096
```
**Avantages :** Bon compromis qualité/coût, performances correctes  
**Inconvénients :** Légèrement moins précis que large

### Production - Économique
```ini
ai_model = mistral-small-latest
ai_temperature = 0.4
ai_max_tokens = 2048
```
**Avantages :** Économique, rapide  
**Inconvénients :** Moins de détails dans les analyses

### Développement/Tests
```ini
ai_model = open-mistral-7b
ai_temperature = 0.5
ai_max_tokens = 2048
```
**Avantages :** Gratuit, idéal pour tester  
**Inconvénients :** Qualité d'analyse réduite

## 💡 Conseils d'optimisation

### Réduire les coûts

1. **Utiliser un modèle plus petit pour les logs normaux**
   ```ini
   ai_model = mistral-small-latest
   ```

2. **Réduire le nombre de tokens**
   ```ini
   ai_max_tokens = 2048  # Au lieu de 4096
   ```

3. **Augmenter l'intervalle de vérification**
   ```ini
   log_check_interval = 600  # 10 minutes au lieu de 5
   ```

### Améliorer la qualité

1. **Utiliser le meilleur modèle**
   ```ini
   ai_model = mistral-large-latest
   ```

2. **Augmenter les tokens pour plus de détails**
   ```ini
   ai_max_tokens = 8192
   ```

3. **Ajuster la température**
   ```ini
   ai_temperature = 0.3  # Plus déterministe
   ```

### Optimiser la vitesse

1. **Modèle rapide**
   ```ini
   ai_model = open-mixtral-8x7b
   ```

2. **Tokens limités**
   ```ini
   ai_max_tokens = 2048
   ```

3. **Température basse**
   ```ini
   ai_temperature = 0.2
   ```

## 📈 Estimation des coûts

Basé sur les tarifs Mistral AI (peut varier) :

| Modèle | Prix / 1M tokens input | Prix / 1M tokens output |
|--------|------------------------|-------------------------|
| mistral-large-latest | $2.00 | $6.00 |
| mistral-medium-latest | $0.80 | $2.40 |
| mistral-small-latest | $0.20 | $0.60 |
| open-mixtral-8x22b | $0.80 | $2.40 |
| open-mixtral-8x7b | $0.20 | $0.60 |
| open-mistral-7b | $0.10 | $0.10 |

### Exemple de calcul

Pour un serveur avec 1000 lignes de logs par heure :
- Tokens input estimés : ~500 tokens/analyse
- Tokens output estimés : ~200 tokens/analyse
- Analyses par mois : ~720 (1 toutes les heures)

**Avec mistral-large-latest :**
- Input : (0.5k × 720) × $2.00 / 1000 = $0.72/mois
- Output : (0.2k × 720) × $6.00 / 1000 = $0.86/mois
- **Total : ~$1.58/mois**

**Avec mistral-small-latest :**
- Input : (0.5k × 720) × $0.20 / 1000 = $0.07/mois
- Output : (0.2k × 720) × $0.60 / 1000 = $0.09/mois
- **Total : ~$0.16/mois**

## 🔄 Changement de modèle

### Pendant le fonctionnement

1. Éditer la configuration :
   ```bash
   sudo nano /etc/log_analyzer/config.ini
   ```

2. Modifier le paramètre `ai_model`

3. Redémarrer le service :
   ```bash
   sudo systemctl restart log-analyzer
   ```

4. Vérifier que le nouveau modèle est utilisé :
   ```bash
   sudo journalctl -u log-analyzer -n 20
   ```

### A/B Testing de modèles

Pour comparer deux modèles, vous pouvez :

1. Créer deux configurations différentes
2. Analyser les mêmes logs avec les deux
3. Comparer la qualité des analyses

## ⚠️ Limitations par modèle

### open-mistral-7b
- Contexte limité (8k tokens max)
- Analyses moins détaillées
- Peut manquer des anomalies subtiles

### mistral-small-latest
- Bon pour les cas simples
- Moins adapté aux analyses complexes

### mistral-large-latest
- Plus coûteux
- Plus lent
- Nécessite plus de crédits API

## 📚 Ressources

- [Documentation Mistral AI](https://docs.mistral.ai/)
- [Tarification Mistral AI](https://mistral.ai/pricing/)
- [API Reference](https://docs.mistral.ai/api/)

## 🆘 Dépannage

### Erreur "Model not found"
Vérifiez que le nom du modèle est correct :
```bash
python3 -c "from config_loader import load_configuration, validate_configuration; config = load_configuration(); print(validate_configuration(config))"
```

### Performances lentes
Essayez un modèle plus rapide comme `mistral-small-latest` ou `open-mixtral-8x7b`.

### Coûts élevés
Réduisez `ai_max_tokens` ou utilisez un modèle moins cher.