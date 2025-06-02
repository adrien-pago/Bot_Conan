import logging
import sqlite3
import tempfile
import os
from config.logging_config import setup_logging

logger = setup_logging()

class ItemManager:
    def __init__(self, bot, ftp_handler):
        """Initialise le gestionnaire d'items"""
        self.bot = bot
        self.ftp = ftp_handler
        self.game_db_path = 'ConanSandbox/Saved/game.db'

    async def give_starter_pack(self, player_id):
        """Donne le pack de départ à un joueur"""
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
            logger.info(f"Base de données lue, taille: {len(game_db)} octets")

            # Créer un fichier temporaire
            logger.info("Création du fichier temporaire...")
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_path = temp_file.name
                temp_file.write(game_db)
            logger.info(f"Fichier temporaire créé: {temp_path}")

            try:
                # Se connecter à la base de données temporaire
                logger.info("Connexion à la base de données temporaire...")
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
                    # Créer un BLOB vide de 32 octets
                    empty_blob = b'\x00' * 32
                    cursor.execute('''
                        INSERT INTO item_inventory (item_id, owner_id, inv_type, template_id, data)
                        VALUES (?, ?, 0, ?, ?)
                    ''', (last_item_id, player_id, template_id, empty_blob))

                # Sauvegarder les modifications
                logger.info("Sauvegarde des modifications...")
                conn.commit()
                conn.close()
                logger.info("Modifications sauvegardées")

                # Lire le fichier modifié
                logger.info("Lecture du fichier modifié...")
                with open(temp_path, 'rb') as f:
                    modified_db = f.read()
                logger.info(f"Fichier modifié lu, taille: {len(modified_db)} octets")

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
                logger.info("Nettoyage du fichier temporaire...")
                try:
                    os.unlink(temp_path)
                    logger.info("Fichier temporaire supprimé")
                except Exception as e:
                    logger.error(f"Erreur lors de la suppression du fichier temporaire: {e}")

        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du pack de départ: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False 