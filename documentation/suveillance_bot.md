# 🔧 Surveillance Automatique du Bot Conan

## 🎯 Objectif

Activer une surveillance automatique qui redémarre le bot en cas de problèmes RCON persistants (erreurs "Broken pipe").

## 📋 Prérequis

- Bot déployé sur le VPS avec le fichier `monitor_bot.sh`
- Accès SSH au VPS
- Permissions root

## 🚀 Procédure d'Activation

### 1. Connexion au VPS
```bash
ssh root@212.227.47.132
cd /root/bot/bot_conan
```

### 2. Rendre le Script Exécutable
```bash
chmod +x monitor_bot.sh
```

### 3. Installer le Service de Surveillance
```bash
./monitor_bot.sh install
```

**Sortie attendue :**
```
✅ Service de surveillance installé. Démarrez-le avec: systemctl start bot_conan_monitor
```

### 4. Démarrer la Surveillance
```bash
systemctl start bot_conan_monitor
```

### 5. Activer le Démarrage Automatique
```bash
systemctl enable bot_conan_monitor
```

### 6. Vérifier l'Installation
```bash
./monitor_bot.sh status
```

**Sortie attendue :**
```
📊 Statut du bot:
● bot_conan.service - Bot Conan Discord
   Active: active (running)

📊 Statut du monitoring:
● bot_conan_monitor.service - Bot Conan Monitor
   Active: active (running)

📈 Erreurs RCON récentes (dernières 5 minutes):
Nombre d'erreurs: 0
```

## 🔍 Commandes de Gestion

### Surveillance des Logs
```bash
# Logs de surveillance en temps réel
journalctl -u bot_conan_monitor -f

# Logs du bot principal
journalctl -u bot_conan -f

# Logs de surveillance dans le fichier dédié
tail -f /var/log/bot_conan_monitor.log
```

### Gestion du Service
```bash
# Voir le statut complet
./monitor_bot.sh status

# Voir les logs récents
./monitor_bot.sh logs

# Arrêter la surveillance
systemctl stop bot_conan_monitor

# Redémarrer la surveillance
systemctl restart bot_conan_monitor

# Désactiver le démarrage automatique
systemctl disable bot_conan_monitor
```

### Désinstallation (si nécessaire)
```bash
./monitor_bot.sh uninstall
```

## ⚙️ Configuration

### Paramètres par Défaut
- **Seuil d'erreurs** : 5 erreurs "Broken pipe" en 5 minutes
- **Fréquence de vérification** : Toutes les minutes
- **Log file** : `/var/log/bot_conan_monitor.log`

### Modifier les Seuils (optionnel)
```bash
nano monitor_bot.sh
```

Modifier ces lignes :
```bash
BROKEN_PIPE_THRESHOLD=5  # Nombre d'erreurs avant redémarrage
TIME_WINDOW=300          # Fenêtre de temps en secondes (5 minutes)
```

## 📊 Fonctionnement

### Ce que fait la surveillance :
1. **Vérifie toutes les minutes** si le service `bot_conan` est actif
2. **Compte les erreurs RCON** dans les 5 dernières minutes
3. **Redémarre automatiquement** si plus de 5 erreurs "Broken pipe"
4. **Log tout** dans `/var/log/bot_conan_monitor.log`

### Logs Typiques
```
2025-06-27 08:30:15 - 🚀 Démarrage de la surveillance du bot Conan
2025-06-27 08:31:15 - ✅ Service bot_conan fonctionne correctement (0 erreurs RCON récentes)
2025-06-27 08:32:15 - ✅ Service bot_conan fonctionne correctement (0 erreurs RCON récentes)
```

### En Cas de Problème
```
2025-06-27 08:45:15 - 🚨 Détection de 6 erreurs RCON dans les dernières 5 minutes
2025-06-27 08:45:15 - 🔧 Seuil de 5 erreurs atteint, redémarrage préventif...
2025-06-27 08:45:15 - 🔄 Redémarrage du service bot_conan...
2025-06-27 08:45:25 - ✅ Service bot_conan redémarré avec succès
```

## 🎯 Services Actifs

Après installation, vous aurez **deux services** qui tournent :

1. **`bot_conan`** - Le bot Discord principal
2. **`bot_conan_monitor`** - La surveillance automatique

### Vérification Rapide
```bash
# Voir les deux services d'un coup
systemctl status bot_conan bot_conan_monitor
```

## 🆘 Dépannage

### Si la surveillance ne démarre pas
```bash
# Vérifier les permissions
ls -la monitor_bot.sh

# Réinstaller si nécessaire
./monitor_bot.sh uninstall
./monitor_bot.sh install
systemctl start bot_conan_monitor
```

### Si le bot ne redémarre pas automatiquement
```bash
# Vérifier les logs de surveillance
journalctl -u bot_conan_monitor -n 50

# Tester manuellement
./monitor_bot.sh monitor
```

### Logs détaillés
```bash
# Logs du bot avec filtrage RCON
journalctl -u bot_conan -f | grep -i "rcon\|broken"

# Tous les logs de surveillance
cat /var/log/bot_conan_monitor.log
```

## ✅ Validation

Pour confirmer que tout fonctionne :

1. **Les deux services sont actifs** : `systemctl status bot_conan bot_conan_monitor`
2. **Logs de surveillance réguliers** : `tail -f /var/log/bot_conan_monitor.log`
3. **Pas d'erreurs dans les logs** : `journalctl -u bot_conan_monitor -n 10`

## 🎉 Résultat

**Avant** : Erreur RCON → Bot cassé → Redémarrage manuel requis

**Après** : Erreur RCON → Surveillance détecte → Redémarrage automatique → Bot fonctionne

**Plus jamais de `systemctl restart bot_conan` manuel !** 🚀

---

**Date de création** : 27 juin 2025  
**Dernière mise à jour** : 27 juin 2025
