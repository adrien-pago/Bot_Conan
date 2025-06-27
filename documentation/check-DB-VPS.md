# 📊 Guide de Vérification de la Base de Données - VPS

Ce guide contient toutes les commandes utiles pour vérifier et explorer votre base de données `discord.db` sur le VPS.

## 🔌 Connexion au VPS

```bash
ssh root@212.227.47.132
cd /root/bot/bot_conan
```

## 📋 Commandes SQLite de Base

### **Ouvrir la base de données**
```bash
sqlite3 discord.db
```

### **Lister toutes les tables**
```sql
.tables
```

### **Voir la structure d'une table**
```sql
.schema items
.schema users
.schema classement
```

### **Sortir de SQLite**
```sql
.quit
```

## 🛒 Vérification de la Boutique

### **Compter les items par catégorie**
```bash
sqlite3 discord.db "SELECT category, COUNT(*) FROM items WHERE enabled = 1 GROUP BY category ORDER BY category;"
```

### **Voir tous les items disponibles**
```bash
sqlite3 discord.db "SELECT id_item_shop, name, price, category FROM items WHERE enabled = 1 ORDER BY category, name;"
```

### **Voir les items les plus chers**
```bash
sqlite3 discord.db "SELECT name, price, category FROM items WHERE enabled = 1 ORDER BY price DESC LIMIT 10;"
```

### **Vérifier un item spécifique**
```bash
sqlite3 discord.db "SELECT * FROM items WHERE name LIKE '%stellaire%';"
```

## 👥 Vérification des Utilisateurs

### **Compter les utilisateurs enregistrés**
```bash
sqlite3 discord.db "SELECT COUNT(*) FROM users;"
```

### **Voir les utilisateurs avec le plus de coins**
```bash
sqlite3 discord.db "SELECT player_name, wallet FROM users WHERE wallet > 0 ORDER BY wallet DESC LIMIT 10;"
```

### **Vérifier un utilisateur spécifique**
```bash
sqlite3 discord.db "SELECT * FROM users WHERE player_name = 'NomDuJoueur';"
```

### **Voir les derniers utilisateurs enregistrés**
```bash
sqlite3 discord.db "SELECT player_name, discord_id, steam_id FROM users ORDER BY rowid DESC LIMIT 5;"
```

## 🏆 Vérification du Classement

### **Top 10 des kills**
```bash
sqlite3 discord.db "SELECT original_name, kills FROM classement ORDER BY kills DESC LIMIT 10;"
```

### **Compter les joueurs avec des kills**
```bash
sqlite3 discord.db "SELECT COUNT(*) FROM classement WHERE kills > 0;"
```

### **Voir les stats d'un joueur**
```bash
sqlite3 discord.db "SELECT * FROM classement WHERE original_name LIKE '%NomDuJoueur%';"
```

## 💰 Historique des Transactions

### **Voir les derniers achats**
```bash
sqlite3 discord.db "SELECT player_name, item_id, count, price, timestamp FROM item_transactions ORDER BY timestamp DESC LIMIT 10;"
```

### **Compter les achats par statut**
```bash
sqlite3 discord.db "SELECT status, COUNT(*) FROM item_transactions GROUP BY status;"
```

## 🔧 Maintenance de la Base

### **Vérifier l'intégrité de la DB**
```bash
sqlite3 discord.db "PRAGMA integrity_check;"
```

### **Voir la taille des tables**
```bash
sqlite3 discord.db "SELECT name, COUNT(*) FROM sqlite_master WHERE type='table' GROUP BY name;"
```

### **Optimiser la base de données**
```bash
sqlite3 discord.db "VACUUM;"
```

## 📊 Statistiques Globales

### **Résumé complet de la boutique**
```bash
sqlite3 discord.db "
SELECT 
    'Total items' as stat, COUNT(*) as value FROM items WHERE enabled = 1
UNION ALL
SELECT 
    'Categories' as stat, COUNT(DISTINCT category) as value FROM items WHERE enabled = 1
UNION ALL
SELECT 
    'Prix moyen' as stat, ROUND(AVG(price), 2) as value FROM items WHERE enabled = 1;
"
```

### **Résumé des utilisateurs**
```bash
sqlite3 discord.db "
SELECT 
    'Utilisateurs total' as stat, COUNT(*) as value FROM users
UNION ALL
SELECT 
    'Avec wallet > 0' as stat, COUNT(*) as value FROM users WHERE wallet > 0
UNION ALL
SELECT 
    'Coins total' as stat, SUM(wallet) as value FROM users;
"
```

## 🚨 Commandes de Dépannage

### **Vérifier les doublons dans le classement**
```bash
sqlite3 discord.db "SELECT player_name, COUNT(*) FROM classement GROUP BY player_name HAVING COUNT(*) > 1;"
```

### **Voir les items sans catégorie**
```bash
sqlite3 discord.db "SELECT * FROM items WHERE category IS NULL OR category = '';"
```

### **Vérifier les prix aberrants**
```bash
sqlite3 discord.db "SELECT name, price FROM items WHERE price > 5000 OR price < 0;"
```

## 📁 Sauvegarde et Restauration

### **Créer une sauvegarde**
```bash
cp discord.db discord_backup_$(date +%Y%m%d_%H%M%S).db
```

### **Exporter en SQL**
```bash
sqlite3 discord.db .dump > discord_backup.sql
```

### **Restaurer depuis SQL**
```bash
sqlite3 discord_new.db < discord_backup.sql
```

## 📝 Format d'Affichage Amélioré

Pour un affichage plus lisible, vous pouvez utiliser ces options :

```bash
sqlite3 discord.db -header -column "SELECT * FROM items LIMIT 5;"
```

Ou dans SQLite :
```sql
.mode column
.headers on
.width 5 20 10 8 8 15
SELECT id_item_shop, name, price, count, category FROM items LIMIT 10;
```

## 🔍 Recherche Avancée

### **Rechercher dans tous les noms d'items**
```bash
sqlite3 discord.db "SELECT name, price, category FROM items WHERE name LIKE '%mot_recherche%';"
```

### **Items dans une gamme de prix**
```bash
sqlite3 discord.db "SELECT name, price FROM items WHERE price BETWEEN 100 AND 500 ORDER BY price;"
```

---

💡 **Astuce** : Pour exécuter plusieurs commandes rapidement, créez un script `.sql` et exécutez-le avec :
```bash
sqlite3 discord.db < mon_script.sql
```
