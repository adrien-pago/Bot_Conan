# 🔧 Fix du Problème "Too many commands" RCON

## 📋 **Problème Identifié**

Votre bot Discord rencontrait des erreurs répétées dans les logs :
```
Too many commands, try again later.
```

### **Causes du Problème :**

1. **Fréquence trop élevée** : Le `PlayerTracker` faisait une mise à jour **toutes les 60 secondes**
2. **Commandes multiples** : À chaque mise à jour, le client RCON essayait **2 commandes** (`GetPlayerList` + `ListPlayers`)
3. **Pas de rate limiting** : Aucune limitation sur la fréquence des commandes RCON
4. **Parsing incorrect** : Le bot interprétait "many" comme un nom de joueur au lieu d'une erreur

## ✅ **Solutions Implémentées**

### **1. Rate Limiting RCON (`utils/rcon_client.py`)**

```python
# Ajout d'un système de rate limiting
self.last_command_time = 0  # Timestamp de la dernière commande
self.min_command_interval = 2.0  # Intervalle minimum entre les commandes (en secondes)

def _rate_limit_check(self):
    """Vérifie et respecte le rate limiting des commandes RCON"""
    current_time = time.time()
    time_since_last = current_time - self.last_command_time
    
    if time_since_last < self.min_command_interval:
        sleep_time = self.min_command_interval - time_since_last
        logger.debug(f"Rate limiting: attente de {sleep_time:.2f} secondes")
        time.sleep(sleep_time)
    
    self.last_command_time = time.time()
```

### **2. Gestion des Erreurs "Too many commands"**

```python
def execute(self, command: str) -> str:
    """Exécute une commande RCON avec gestion du rate limiting"""
    self._rate_limit_check()
    self._ensure_connection()
    
    # Utiliser un autre ID (2) pour l'exécution de commande (type=2)
    self._send_packet(2, 2, command)
    _, _, payload = self._recv_packet()
    
    # Vérifier si la réponse indique "Too many commands"
    if "Too many commands" in payload:
        logger.warning(f"Rate limit RCON atteint pour la commande '{command}'. Attente de 5 secondes...")
        time.sleep(5)  # Attendre 5 secondes avant de réessayer
        raise RuntimeError("Too many commands, try again later")
    
    return payload
```

### **3. Optimisation du PlayerTracker (`features/player_tracker.py`)**

```python
# Augmentation de l'intervalle de mise à jour
await asyncio.sleep(480)  # 8 minutes au lieu de 60 secondes

# Mise à jour conditionnelle
if count != self.last_player_count:
    self.last_player_count = count
    # ... mise à jour du salon
else:
    logger.debug(f"Nombre de joueurs inchangé ({count}), pas de mise à jour du salon")
```

### **4. Amélioration du Parsing**

```python
# Filtrage de "many" comme nom de joueur
if char_name and char_name != "Steam" and not char_name.isdigit() and char_name != "many":
    players.append(char_name)
```

## 🚀 **Améliorations Apportées**

### **Performance :**
- ✅ **Réduction de 87.5%** des commandes RCON (de 60s à 480s)
- ✅ **Rate limiting** : 2 secondes minimum entre les commandes
- ✅ **Mise à jour conditionnelle** : seulement si le nombre de joueurs change

### **Robustesse :**
- ✅ **Gestion d'erreur** pour "Too many commands"
- ✅ **Reconnexion automatique** en cas de déconnexion
- ✅ **Logging amélioré** avec niveaux appropriés

### **Logging :**
- ✅ **Logs DEBUG** pour les détails techniques
- ✅ **Logs WARNING** pour les erreurs de rate limiting
- ✅ **Logs INFO** pour les événements importants

## 📊 **Comparaison Avant/Après**

| Aspect | Avant | Après |
|--------|-------|-------|
| **Fréquence de mise à jour** | 60 secondes | 480 secondes (8 minutes) |
| **Commandes RCON/min** | 2 | 0.25 |
| **Rate limiting** | ❌ Aucun | ✅ 2 secondes minimum |
| **Gestion d'erreur** | ❌ Basique | ✅ Complète |
| **Parsing "many"** | ❌ Erroné | ✅ Corrigé |

## 🧪 **Test des Modifications**

Un script de test a été créé : `test_rcon_fix.py`

```bash
python test_rcon_fix.py
```

Ce script teste :
- ✅ Le rate limiting entre les commandes
- ✅ La récupération des joueurs connectés
- ✅ La gestion des erreurs "Too many commands"
- ✅ La robustesse générale du client RCON

## 🔄 **Déploiement**

### **1. Redémarrage du Bot**
```bash
# Arrêter le service
systemctl stop bot_conan

# Redémarrer le service
systemctl start bot_conan

# Vérifier le statut
systemctl status bot_conan
```

### **2. Vérification des Logs**
```bash
# Suivre les logs en temps réel
journalctl -u bot_conan -f

# Vérifier qu'il n'y a plus d'erreurs "Too many commands"
journalctl -u bot_conan | grep "Too many commands"
```

## 📈 **Résultats Attendus**

Après ces modifications, vous devriez voir :

### **Dans les Logs :**
```
✅ PlayerTracker démarré
✅ Nom du salon mis à jour: X joueurs connectés
✅ Joueurs connectés via GetPlayerList: ['Joueur1', 'Joueur2']
```

### **Plus d'Erreurs :**
- ❌ `Too many commands, try again later.`
- ❌ `Joueur trouvé (format alternatif): many`
- ❌ Spam de commandes RCON

### **Performance :**
- 📉 **Réduction drastique** des commandes RCON
- 📈 **Stabilité améliorée** du bot
- 📊 **Logs plus propres** et informatifs

## 🛠️ **Configuration Avancée**

Si vous souhaitez ajuster les paramètres :

### **Intervalle de mise à jour (PlayerTracker)**
```python
# Dans features/player_tracker.py, ligne 47
await asyncio.sleep(480)  # 8 minutes
```

### **Rate limiting RCON**
```python
# Dans utils/rcon_client.py, ligne 30
self.min_command_interval = 2.0  # 2 secondes
```

### **Timeout de reconnexion**
```python
# Dans utils/rcon_client.py, ligne 25
DEFAULT_TIMEOUT = 10.0  # 10 secondes
```

## 🆘 **En Cas de Problème**

Si vous rencontrez encore des erreurs :

1. **Vérifiez la connectivité RCON** :
   ```bash
   telnet votre_ip_serveur 25575
   ```

2. **Testez le client RCON** :
   ```bash
   python test_rcon_fix.py
   ```

3. **Vérifiez les logs** :
   ```bash
   journalctl -u bot_conan --since "1 hour ago"
   ```

4. **Redémarrez le service** :
   ```bash
   systemctl restart bot_conan
   ```

---

**Ces modifications devraient résoudre complètement le problème "Too many commands" et améliorer significativement la stabilité de votre bot Discord ! 🎉** 