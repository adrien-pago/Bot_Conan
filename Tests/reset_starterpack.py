import sqlite3
import sys

# Fonction pour réinitialiser le starterpack d'un utilisateur
def reset_starterpack(discord_id=None):
    try:
        # Connexion à la base de données
        conn = sqlite3.connect('discord.db')
        cursor = conn.cursor()
        
        if discord_id:
            # Réinitialiser pour un utilisateur spécifique
            cursor.execute("UPDATE users SET has_received_starterpack = 0 WHERE discord_id = ?", (discord_id,))
            print(f"Starterpack réinitialisé pour l'utilisateur avec Discord ID: {discord_id}")
        else:
            # Réinitialiser pour tous les utilisateurs
            cursor.execute("UPDATE users SET has_received_starterpack = 0")
            print("Starterpack réinitialisé pour tous les utilisateurs")
        
        # Afficher les utilisateurs concernés
        if discord_id:
            cursor.execute("SELECT discord_id, player_name, has_received_starterpack FROM users WHERE discord_id = ?", (discord_id,))
        else:
            cursor.execute("SELECT discord_id, player_name, has_received_starterpack FROM users")
        
        users = cursor.fetchall()
        print("\nListe des utilisateurs après réinitialisation:")
        print("Discord ID | Nom du joueur | Starterpack reçu")
        print("-" * 50)
        for user in users:
            print(f"{user[0]} | {user[1]} | {user[2]}")
        
        # Sauvegarder les changements
        conn.commit()
        
    except Exception as e:
        print(f"Erreur: {e}")
    finally:
        # Fermer la connexion
        if conn:
            conn.close()

if __name__ == "__main__":
    # Vérifier si un ID Discord a été passé en argument
    if len(sys.argv) > 1:
        discord_id = sys.argv[1]
        reset_starterpack(discord_id)
    else:
        # Demander confirmation avant de réinitialiser tous les utilisateurs
        confirm = input("Voulez-vous réinitialiser le starterpack pour TOUS les utilisateurs? (o/n): ")
        if confirm.lower() == 'o':
            reset_starterpack()
        else:
            print("Opération annulée.") 