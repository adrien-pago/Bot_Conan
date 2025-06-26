#!/usr/bin/env python3
"""
Script de migration pour mettre à jour la structure de la table classement
À exécuter sur le VPS après avoir déployé les nouvelles modifications
"""

import sqlite3
import os
from datetime import datetime

def migrate_classement_table():
    """Migre la table classement vers la nouvelle structure"""
    db_path = 'discord.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Base de données {db_path} non trouvée")
        return False
    
    # Créer une sauvegarde
    backup_path = f'discord.db.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"✅ Sauvegarde créée: {backup_path}")
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    try:
        # Vérifier la structure actuelle
        c.execute("PRAGMA table_info(classement)")
        columns = [row[1] for row in c.fetchall()]
        print(f"📋 Colonnes actuelles: {columns}")
        
        # Vérifier si la migration est nécessaire
        if 'original_name' in columns and 'id' in columns:
            print("✅ La table est déjà à jour, aucune migration nécessaire")
            return True
        
        print("🔄 Migration de la table classement...")
        
        # Créer la nouvelle table
        c.execute('''
            CREATE TABLE IF NOT EXISTS classement_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL,
                original_name TEXT NOT NULL,
                kills INTEGER DEFAULT 0,
                last_kill TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(player_name)
            )
        ''')
        
        # Migrer les données existantes
        if 'player_name' in columns:
            # Ancienne structure avec player_name
            c.execute('''
                INSERT INTO classement_new (player_name, original_name, kills, last_kill)
                SELECT 
                    lower(trim(player_name)) as player_name,
                    player_name as original_name,
                    kills,
                    last_kill
                FROM classement
                WHERE player_name IS NOT NULL AND player_name != ''
            ''')
        else:
            print("⚠️ Structure de table non reconnue, création d'une table vide")
        
        # Supprimer l'ancienne table et renommer la nouvelle
        c.execute('DROP TABLE IF EXISTS classement')
        c.execute('ALTER TABLE classement_new RENAME TO classement')
        
        conn.commit()
        
        # Vérifier le résultat
        c.execute("SELECT COUNT(*) FROM classement")
        count = c.fetchone()[0]
        print(f"✅ Migration terminée avec succès! {count} joueurs migrés")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Démarrage de la migration de la table classement...")
    success = migrate_classement_table()
    if success:
        print("🎉 Migration terminée avec succès!")
        print("📝 Vous pouvez maintenant redémarrer le bot: systemctl restart bot_conan")
    else:
        print("💥 Migration échouée, vérifiez les logs") 