# 🔧 Améliorations RCON - Reconnexion Automatique

## 🚨 Problème Résolu

**Avant** : Quand le serveur Conan Exiles se déconnectait 10 secondes, le bot perdait la connexion RCON et ne se reconnectait jamais automatiquement.

**Après** : Le bot gère automatiquement les déconnexions RCON et se reconnecte sans intervention manuelle !

## ✨ Améliorations Apportées

### 🔄 Reconnexion Automatique RCON
- **Détection automatique** des erreurs `Broken pipe`
- **Reconnexion immédiate** en cas de perte de connexion
- **Double tentative** pour chaque commande RCON
- **Logs détaillés** pour suivre les reconnexions

### 🛡️ Gestion d'Erreurs Robuste
- Le **PlayerTracker continue** même en cas d'erreur RCON
- **Pas de plantage** du bot entier
- **Messages informatifs** dans les logs
- **Préservation du dernier état** du canal

### 📊 Système de Surveillance Automatique
- **Script de monitoring** qui surveille les erreurs RCON
- **Redémarrage automatique** si trop d'erreurs (5 en 5 minutes)
- **Service systemd** pour surveillance continue
- **Logs de monitoring** dédiés

## 🚀 Déploiement

### 1. Préparer et Transférer
```powershell
# Sur votre PC
.\deploy.ps1
```

```bash
# Transférer vers le VPS
scp -r Deploy-files/* root@212.227.47.132:/root/bot/bot_conan/
```

### 2. Arrêter le Bot
```bash
systemctl stop bot_conan
```

### 3. Rendre le Script de Monitoring Exécutable
```bash
cd /root/bot/bot_conan
chmod +x monitor_bot.sh
```

### 4. Redémarrer le Bot
```bash
systemctl start bot_conan
```

### 5. (Optionnel) Installer la Surveillance Automatique
```bash
# Installer le service de surveillance
./monitor_bot.sh install

# Démarrer la surveillance
systemctl start bot_conan_monitor

# Vérifier que tout fonctionne
./monitor_bot.sh status
```

## 🔍 Nouvelles Fonctionnalités

### 📊 Commandes de Monitoring

```bash
# Voir le statut complet
./monitor_bot.sh status

# Voir les logs récents
./monitor_bot.sh logs

# Surveiller manuellement (pour tester)
./monitor_bot.sh monitor
```

### 🔧 Gestion du Service de Surveillance

```bash
# Démarrer la surveillance automatique
systemctl start bot_conan_monitor

# Arrêter la surveillance
systemctl stop bot_conan_monitor

# Voir les logs de surveillance
journalctl -u bot_conan_monitor -f

# Désinstaller la surveillance
./monitor_bot.sh uninstall
```

## 📈 Améliorations Techniques

### Avant (Problématique)
```
❌ Erreur RCON → Bot cassé → Redémarrage manuel requis
❌ Pas de reconnexion automatique
❌ PlayerTracker plante complètement
❌ Aucune surveillance automatique
```

### Après (Corrigé)
```
✅ Erreur RCON → Reconnexion automatique → Bot continue
✅ Double tentative pour chaque commande
✅ PlayerTracker robuste avec gestion d'erreurs
✅ Surveillance automatique avec redémarrage si nécessaire
```

## 🎯 Ce Qui Se Passe Maintenant

### En Cas de Déconnexion RCON
1. **Détection** de l'erreur `Broken pipe`
2. **Log d'avertissement** : "Connexion RCON temporairement perdue"
3. **Tentative de reconnexion** automatique
4. **Réessai de la commande** après reconnexion
5. **Continuation normale** du bot

### Logs Typiques (Normaux)
```
2025-06-27 07:15:32 - utils.rcon_client - WARNING - Connexion RCON perdue lors de l'exécution de 'GetPlayerList': [Errno 32] Broken pipe
2025-06-27 07:15:32 - utils.rcon_client - INFO - Tentative de reconnexion automatique...
2025-06-27 07:15:33 - utils.rcon_client - INFO - Connexion RCON réussie après 0 tentatives
2025-06-27 07:15:33 - features.player_tracker - DEBUG - Récupération réussie: 3 joueurs connectés
```

### Surveillance Automatique (Si Installée)
```
2025-06-27 07:20:15 - ✅ Service bot_conan fonctionne correctement (2 erreurs RCON récentes)
2025-06-27 07:21:15 - ✅ Service bot_conan fonctionne correctement (1 erreurs RCON récentes)
```

## ⚙️ Configuration de la Surveillance

### Paramètres Modifiables (dans monitor_bot.sh)
```bash
BROKEN_PIPE_THRESHOLD=5  # Nombre d'erreurs avant redémarrage
TIME_WINDOW=300          # Fenêtre de temps (5 minutes)
```

### Seuils Recommandés
- **Serveur stable** : `BROKEN_PIPE_THRESHOLD=10`
- **Serveur instable** : `BROKEN_PIPE_THRESHOLD=3`
- **Test/Debug** : `BROKEN_PIPE_THRESHOLD=2`

## 🆘 Dépannage

### Si le Bot Ne Se Reconnecte Pas
```bash
# Vérifier les logs détaillés
journalctl -u bot_conan -f | grep -i rcon

# Redémarrage manuel si nécessaire
systemctl restart bot_conan
```

### Si la Surveillance Ne Fonctionne Pas
```bash
# Vérifier le script
./monitor_bot.sh status

# Tester manuellement
./monitor_bot.sh monitor

# Réinstaller si nécessaire
./monitor_bot.sh uninstall
./monitor_bot.sh install
systemctl start bot_conan_monitor
```

## 🎉 Résultat Final

Votre bot est maintenant **ultra-robuste** ! 

- ✅ **Plus de plantages** à cause des déconnexions serveur
- ✅ **Reconnexion automatique** en cas de problème RCON
- ✅ **Surveillance continue** avec redémarrage préventif
- ✅ **Logs clairs** pour comprendre ce qui se passe
- ✅ **Fonctionnement autonome** 24h/24

**Fini les redémarrages manuels !** 🚀 