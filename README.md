# 🏛️ Bot Conan Exiles Discord - Documentation Complète

Un bot Discord avancé et complet pour la gestion et la surveillance d'un serveur Conan Exiles. Ce bot offre une suite complète d'outils pour les administrateurs et les joueurs, incluant le suivi des activités, la gestion des items, un système de boutique, et bien plus encore.

## 🎯 **Fonctionnalités Principales**

### 🎮 **Gestion des Joueurs**
- **Suivi en temps réel** des joueurs connectés/déconnectés
- **Synchronisation automatique** des données joueurs avec la base de données du serveur
- **Mise à jour automatique** du nom du canal avec le nombre de joueurs connectés
- **Système d'informations** des joueurs via messages privés
- **Enregistrement et vérification** des comptes Discord/Conan Exiles

### 🏹 **Système de Combat et Classement**
- **Suivi des kills et morts** en temps réel
- **Classement des joueurs** par nombre de kills
- **Statistiques détaillées** des combats
- **Notifications automatiques** des événements PvP
- **Mise à jour automatique** du classement toutes les 5 secondes

### 🏗️ **Gestion des Constructions**
- **Limite de construction** configurable (défaut: 12,000 pièces)
- **Surveillance automatique** des constructions en cours
- **Notifications** quand les limites sont atteintes
- **Suivi des bâtiments** par joueur/clan
- **Rapports horaires** sur l'état des constructions

### 🛒 **Système de Boutique Avancé**
- **Boutique in-game** avec interface Discord élégante
- **Catégories d'items** : Armes, Outils, Ressources, Stockage, Pets, Potions
- **Système de coins** pour les achats
- **Gestion des inventaires** et starter packs
- **Interface stylée** avec embeds Discord colorés
- **Système de cooldown** pour éviter le spam
- **Vérification de présence** en ligne pour les achats

### 🗳️ **Système de Votes Automatique**
- **Votes pour serveur privé** ou public
- **Intégration avec les sites de classement** de serveurs
- **Notifications automatiques** des résultats de votes
- **Récompenses automatiques** (50 coins par vote)
- **Messages de confirmation** aux joueurs

### 🔧 **Administration RCON**
- **Commandes RCON** directement depuis Discord
- **Démarrage/arrêt** du serveur à distance
- **Gestion des joueurs** (kick, ban, etc.)
- **Exécution de commandes** personnalisées
- **Rate limiting** pour éviter le spam de commandes

### 📦 **Système de Starter Pack**
- **Pack de départ automatique** pour les nouveaux joueurs
- **Vérification de présence** en ligne
- **Items prédéfinis** : Piolet, Couteau, Hache, Coffre, Cheval, Selle, Potions
- **Système anti-abus** (une seule utilisation par joueur)

## 🚀 **Installation et Configuration**

### **Prérequis**
- **Python 3.10 ou 3.11** (⚠️ **Pas compatible avec Python 3.12** à cause de `python-valve`)
- **Serveur Conan Exiles** avec accès RCON et FTP
- **Bot Discord** avec les permissions appropriées
- **Base de données SQLite** (créée automatiquement)

### **1. Cloner le projet**
```bash
git clone https://github.com/votre-username/Bot_Conan.git
cd Bot_Conan
```

### **2. Installer les dépendances**
```bash
pip install -r requirements.txt
```

**Note importante** : Si vous utilisez Python 3.12, vous devrez downgrader vers Python 3.10 ou 3.11 car `python-valve` n'est pas encore compatible.

### **3. Configuration**
Créez un fichier `.env` à la racine du projet :

```env
# Discord Configuration
DISCORD_TOKEN=votre_token_discord_ici
RENAME_CHANNEL_ID=1375223092892401737
BUILD_CHANNEL_ID=1375234869071708260
KILLS_CHANNEL_ID=1375234869071708260
TOP_SERVER_CHANNEL_ID=1368550677030109225
SERVER_PRIVE_CHANNEL_ID=1369099859574915192
SHOP_CHANNEL_ID=1379725647579975730
COMMANDE_CHANNEL_ID=1375046216097988629

# Serveur de Jeu
GAME_SERVER_HOST=votre_ip_serveur
RCON_PORT=25575
RCON_PASSWORD=votre_mot_de_passe_rcon

# FTP Configuration
FTP_HOST=votre_ip_ftp
FTP_USER=votre_utilisateur_ftp
FTP_PASS=votre_mot_de_passe_ftp
FTP_DB_PATH=chemin/vers/game.db
FTP_LOG_PATH=Saved/Logs/ConanSandbox.log
```

### **4. Lancer le bot**
```bash
python bot.py
```

## 🐧 **Déploiement sur VPS Linux**

### **1. Préparation locale**
Utilisez le script PowerShell pour préparer les fichiers de déploiement :
```powershell
.\deploy.ps1
```

### **2. Transfert vers le VPS**
```bash
scp -r Deploy-files/* root@votre_ip:/root/bot/bot_conan/
```

### **3. Installation sur le VPS**
```bash
# Mise à jour du système
apt update && apt upgrade -y

# Installation de Python et pip
apt install -y python3 python3-pip

# Installation des dépendances
cd /root/bot/bot_conan
pip3 install -r requirements.txt

# Configuration du service systemd
cp bot_conan.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable bot_conan
systemctl start bot_conan
```

### **4. Gestion du service**
```bash
# Voir le statut
systemctl status bot_conan

# Redémarrer
systemctl restart bot_conan

# Arrêter
systemctl stop bot_conan

# Voir les logs en temps réel
journalctl -u bot_conan -f
```

## 🎯 **Commandes Discord**

### **Commandes Générales**
- `!info` - Affiche les informations du joueur (en MP uniquement)
- `!register` - Enregistre un nouveau joueur (en MP uniquement)
- `!solde` - Affiche le solde de coins du joueur (en MP uniquement)

### **Commandes de Boutique**
- `!shop` - Affiche la boutique avec tous les items disponibles (dans le canal de commandes)
- `!buy <id_item> [quantité]` - Achète un item de la boutique (en MP uniquement)

### **Commandes d'Administration**
- `!start` - Démarre le serveur Conan Exiles
- `!stop` - Arrête le serveur Conan Exiles
- `!rcon <commande>` - Exécute une commande RCON

### **Commandes de Statistiques**
- `!kills_status` - Affiche les statistiques de kills
- `!build` - Affiche les informations de construction

### **Commandes de Gestion**
- `!starterpack` - Gère les starter packs des joueurs (en MP uniquement)

## 🏗️ **Architecture Détaillée du Projet**

```
Bot_Conan/
├── 📁 bot.py                    # Point d'entrée principal
├── 📁 requirements.txt          # Dépendances Python
├── 📁 .env                      # Variables d'environnement
├── 📁 deploy.ps1                # Script de déploiement
├── 📁 bot_conan.service         # Service systemd
│
├── 📂 commandes/                # Commandes Discord (Cogs)
│   ├── build.py                 # Commandes de construction
│   ├── buy.py                   # Système d'achat (MP uniquement)
│   ├── info.py                  # Informations joueur (MP uniquement)
│   ├── kills_status.py          # Statistiques de combat
│   ├── rcon.py                  # Commandes RCON
│   ├── register.py              # Enregistrement joueurs (MP uniquement)
│   ├── shop.py                  # Boutique Discord (canal spécifique)
│   ├── solde.py                 # Gestion des coins (MP uniquement)
│   ├── start.py                 # Démarrage serveur
│   ├── starterpack.py           # Gestion starter packs (MP uniquement)
│   └── stop.py                  # Arrêt serveur
│
├── 📂 features/                 # Fonctionnalités principales
│   ├── build_limit.py           # Limitation constructions (rapports horaires)
│   ├── classement_player.py     # Système de classement (mise à jour 5s)
│   ├── item_manager.py          # Gestion des items (cooldown, vérifications)
│   ├── player_sync.py           # Synchronisation joueurs
│   ├── player_tracker.py        # Suivi des joueurs
│   └── vote_tracker.py          # Système de votes (vérification 10s)
│
├── 📂 database/                 # Gestion base de données
│   ├── init_database.py         # Initialisation BDD
│   ├── database_sync.py         # Synchronisation données
│   ├── database_classement.py   # Gestion classements
│   ├── database_build.py        # Gestion constructions
│   └── create_items_table.py    # Création tables items
│
├── 📂 utils/                    # Utilitaires
│   ├── rcon_client.py           # Client RCON (rate limiting)
│   ├── ftp_handler.py           # Gestionnaire FTP
│   └── helpers.py               # Fonctions utilitaires
│
├── 📂 config/                   # Configuration
│   ├── settings.py              # Paramètres généraux
│   └── logging_config.py        # Configuration logs
│
└── 📂 core/                     # Composants principaux
    ├── bot_core.py              # Classe principale du bot
    └── commands.py              # Gestion des commandes
```

## 🔧 **Configuration Avancée**

### **Variables d'Environnement Détaillées**

| Variable | Description | Valeur par défaut | Obligatoire |
|----------|-------------|-------------------|-------------|
| `DISCORD_TOKEN` | Token du bot Discord | - | ✅ **Requis** |
| `RENAME_CHANNEL_ID` | Canal de suivi des joueurs | `1375223092892401737` | ✅ |
| `BUILD_CHANNEL_ID` | Canal des constructions | `1375234869071708260` | ✅ |
| `KILLS_CHANNEL_ID` | Canal des kills | `1375234869071708260` | ✅ |
| `SHOP_CHANNEL_ID` | Canal de la boutique | `1379725647579975730` | ✅ |
| `COMMANDE_CHANNEL_ID` | Canal des commandes | `1375046216097988629` | ✅ |
| `GAME_SERVER_HOST` | IP du serveur de jeu | - | ✅ **Requis** |
| `RCON_PORT` | Port RCON | `25575` | ✅ |
| `RCON_PASSWORD` | Mot de passe RCON | - | ✅ **Requis** |
| `FTP_HOST` | Serveur FTP | - | ✅ **Requis** |
| `FTP_USER` | Utilisateur FTP | - | ✅ **Requis** |
| `FTP_PASS` | Mot de passe FTP | - | ✅ **Requis** |

### **Paramètres de Jeu**

- **Limite de construction** : 12,000 pièces par défaut
- **Joueurs maximum** : 40
- **Intervalles de mise à jour** :
  - Canal joueurs : 8 minutes (optimisé pour éviter le spam RCON)
  - Vérification constructions : 1 heure
  - Mise à jour kills : 5 secondes
  - Vérification votes : 10 secondes

### **Heures de Raid**
- **Jours** : Mercredi, Samedi et Dimanche (2, 5, 6)
- **Heures** : 19h00 - 22h00

## 📊 **Base de Données**

Le bot utilise **SQLite** pour stocker les données :

### **Tables Principales**
- `users` - Informations des utilisateurs Discord/Conan
- `items` - Catalogue de la boutique
- `item_transactions` - Historique des achats
- `kills` - Historique des kills
- `builds` - Données de construction
- `votes` - Système de votes

### **Synchronisation**
- **Automatique** avec la base de données du serveur Conan Exiles
- **Temps réel** pour les événements critiques
- **Sauvegarde** régulière des statistiques

## 🔍 **Fonctionnalités Automatiques**

### **Surveillance en Temps Réel**
- ✅ Connexions/déconnexions des joueurs (8 min)
- ✅ Nouveaux kills et morts (5 sec)
- ✅ Constructions terminées (1 heure)
- ✅ Dépassement des limites de construction
- ✅ Votes sur les sites de classement (10 sec)

### **Notifications Discord**
- 🔔 Événements PvP importants
- 🔔 Alertes de construction
- 🔔 Changements de statut du serveur
- 🔔 Résultats de votes
- 🔔 Confirmation d'achats

### **Maintenance Automatique**
- 🔄 Nettoyage des anciens logs
- 🔄 Optimisation de la base de données
- 🔄 Mise à jour des statistiques
- 🔄 Synchronisation des données

## 🛡️ **Sécurité et Anti-Abus**

### **Rate Limiting**
- **RCON** : 2 secondes minimum entre les commandes
- **Discord** : Gestion automatique des rate limits
- **Cooldown** : 60 secondes après les constructions

### **Vérifications**
- **Présence en ligne** pour les achats et starter packs
- **Enregistrement obligatoire** pour les commandes sensibles
- **Vérification des permissions** par canal
- **Système de verrous** pour éviter les conflits

### **Logging**
- **Logs détaillés** de toutes les actions
- **Traçabilité** des transactions
- **Gestion d'erreurs** robuste

## ⚠️ **Problèmes Connus et Solutions**

### **Problème de Compatibilité Python 3.12**
**Erreur** : `ModuleNotFoundError: No module named 'valve.rcon'`

**Solution** : Le package `python-valve` n'est pas compatible avec Python 3.12. Utilisez Python 3.10 ou 3.11.

```bash
# Vérifier votre version de Python
python --version

# Si vous avez Python 3.12, installez Python 3.10 ou 3.11
# Puis créez un environnement virtuel avec la bonne version
```

### **Problèmes de Connexion RCON**
- Vérifiez que le port RCON est ouvert sur votre serveur
- Confirmez que le mot de passe RCON est correct
- Assurez-vous que le serveur Conan Exiles est démarré

### **Problèmes FTP**
- Vérifiez les permissions d'accès aux fichiers
- Confirmez que le chemin vers la base de données est correct
- Testez la connexion FTP manuellement

### **Problèmes "Too many commands"**
**Résolu** : Le bot inclut maintenant un système de rate limiting pour éviter ce problème.

## 🔄 **Mises à Jour Récentes**

### **v2.1 - Optimisation RCON**
- ✅ **Rate limiting** : 2 secondes minimum entre les commandes RCON
- ✅ **Fréquence réduite** : Mise à jour des joueurs toutes les 8 minutes
- ✅ **Gestion d'erreur** : Détection et gestion de "Too many commands"
- ✅ **Parsing corrigé** : Plus d'interprétation de "many" comme nom de joueur
- ✅ **Mise à jour conditionnelle** : Le salon ne se met à jour que si le nombre de joueurs change

### **v2.0 - Système de Boutique**
- ✅ **Interface élégante** avec embeds Discord colorés
- ✅ **Catégories d'items** avec icônes et couleurs
- ✅ **Système de coins** intégré
- ✅ **Vérification de présence** en ligne
- ✅ **Historique des transactions**

## 🤝 **Contribution**

Les contributions sont les bienvenues ! N'hésitez pas à :

1. 🍴 **Fork** le projet
2. 🌟 **Créer** une branche pour votre fonctionnalité
3. 📝 **Commiter** vos changements
4. 🚀 **Push** vers la branche
5. 🔄 **Ouvrir** une Pull Request

## 📜 **Licence**

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🆘 **Support**

Pour obtenir de l'aide :
- 📧 Ouvrez une **issue** sur GitHub
- 💬 Rejoignez notre **serveur Discord**
- 📖 Consultez la **documentation** complète

---

**Développé avec ❤️ pour la communauté Conan Exiles**

*Dernière mise à jour : Décembre 2024*
