import logging
import sqlite3
import threading
import time
import tempfile
import os
from config.logging_config import setup_logging

logger = setup_logging()

# Verrou global pour éviter les appels multiples
_global_lock = threading.Lock()

class ItemManager:
    def __init__(self, bot, ftp_handler):
        """Initialise le gestionnaire d'items"""
        self.bot = bot
        self.ftp = ftp_handler
        self.game_db_path = 'ConanSandbox/Saved/game.db'
        self.last_build_time = 0
        self.build_cooldown = 60  # 60 secondes de cooldown après un build

    def can_modify_database(self):
        """Vérifie si on peut modifier la base de données"""
        current_time = time.time()
        if current_time - self.last_build_time < self.build_cooldown:
            remaining = int(self.build_cooldown - (current_time - self.last_build_time))
            logger.warning(f"Base de données verrouillée, attendez {remaining} secondes")
            return False
        return True

    def set_last_build_time(self):
        """Met à jour le timestamp du dernier build"""
        self.last_build_time = time.time()

    async def give_starter_pack(self, player_id):
        """Donne le pack de départ à un joueur"""
        # Vérifier si on peut modifier la base de données
        if not self.can_modify_database():
            return False

        # Utiliser le verrou global pour éviter les appels multiples
        if not _global_lock.acquire(blocking=False):
            logger.warning(f"Une autre opération est en cours pour le joueur {player_id}")
            return False

        try:
            logger.info(f"Début de l'ajout du pack de départ pour le joueur {player_id}")
            
            # Liste des template_id pour le starter pack
            starter_items = [
                51020, 51312, 53002, 52001, 52002, 52003, 52004, 52005, 80852, 92226, 2708
            ]

            # Lire la base de données du jeu
            logger.info("Lecture de la base de données du jeu...")
            game_db = self.ftp.read_database(self.game_db_path)
            if not game_db:
                logger.error("Impossible de lire la base de données du jeu")
                return False

            # Créer un fichier temporaire pour la base de données
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_path = temp_file.name
                temp_file.write(game_db)

            try:
                # Se connecter à la base de données
                conn = sqlite3.connect(temp_path)
                cursor = conn.cursor()

                # Récupérer le dernier item_id utilisé
                logger.info("Récupération du dernier item_id...")
                cursor.execute('SELECT MAX(item_id) FROM item_inventory WHERE owner_id = ? AND inv_type = 0', (player_id,))
                last_item_id = cursor.fetchone()[0] or 0
                logger.info(f"Dernier item_id trouvé: {last_item_id}")

                # Ajouter chaque item dans l'inventaire
                logger.info("Ajout des items dans l'inventaire...")
                for template_id in starter_items:
                    last_item_id += 1
                    logger.info(f"Ajout de l'item {template_id} avec item_id {last_item_id}")

                    # Trouver un item existant du même type pour copier ses données
                    cursor.execute('''
                        SELECT data 
                        FROM item_inventory 
                        WHERE template_id = ? 
                        AND data IS NOT NULL 
                        LIMIT 1
                    ''', (template_id,))
                    result = cursor.fetchone()

                    if result and result[0]:
                        # Utiliser les données de l'item existant
                        item_data = result[0]
                        logger.info(f"Données trouvées pour l'item {template_id}")
                    else:
                        # Si aucun item du même type n'est trouvé, utiliser un BLOB vide
                        item_data = b'\x00' * 32
                        logger.warning(f"Aucune donnée trouvée pour l'item {template_id}, utilisation d'un BLOB vide")

                    cursor.execute('''
                        INSERT INTO item_inventory (item_id, owner_id, inv_type, template_id, data)
                        VALUES (?, ?, 0, ?, ?)
                    ''', (last_item_id, player_id, template_id, item_data))

                # Sauvegarder les modifications
                logger.info("Sauvegarde des modifications...")
                conn.commit()
                conn.close()

                # Lire le fichier modifié
                with open(temp_path, 'rb') as f:
                    modified_db = f.read()

                # Écrire les modifications dans la base de données
                logger.info("Écriture des modifications dans la base de données...")
                if self.ftp.write_database(self.game_db_path, modified_db):
                    logger.info(f"Pack de départ ajouté avec succès pour le joueur {player_id}")
                    return True
                else:
                    logger.error("Échec de l'écriture dans la base de données du jeu")
                    return False

            finally:
                # Nettoyer le fichier temporaire
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    logger.error(f"Erreur lors de la suppression du fichier temporaire: {e}")

        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du pack de départ: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        finally:
            # Libérer le verrou global
            _global_lock.release() 