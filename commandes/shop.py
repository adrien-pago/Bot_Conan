import os
import discord
from discord.ext import commands
import sqlite3

SHOP_CHANNEL_ID = int(os.getenv('SHOP_CHANNEL_ID', 1379725647579975730))
COMMANDE_CHANNEL_ID = int(os.getenv('COMMANDE_CHANNEL_ID', 1375046216097988629))
DB_PATH = 'discord.db'

CATEGORY_STYLES = {
    "Outils":     {"color": 0x3498DB, "icon": "https://cdn-icons-png.flaticon.com/128/7213/7213807.png"},  # Bleu
    "Ressources": {"color": 0x27AE60, "icon": "https://cdn-icons-png.flaticon.com/128/17257/17257592.png"}, # Vert
    "Pets":       {"color": 0x8E44AD, "icon": "https://cdn-icons-png.flaticon.com/128/5511/5511666.png"},   # Violet
    "Alchimie":   {"color": 0x16A085, "icon": "https://cdn-icons-png.flaticon.com/128/3828/3828771.png"},   # Turquoise
    "Recipe":     {"color": 0xF39C12, "icon": "https://cdn-icons-png.flaticon.com/128/1041/1041373.png"},   # Orange
    "Thrall":     {"color": 0xC0392B, "icon": "https://cdn-icons-png.flaticon.com/128/3805/3805896.png"},   # Rouge
    "Atelier":    {"color": 0x95A5A6, "icon": "https://cdn-icons-png.flaticon.com/128/1504/1504085.png"},   # Gris
    "Sorcellery": {"color": 0x9B59B6, "icon": "https://cdn-icons-png.flaticon.com/128/2106/2106218.png"},   # Violet foncé
    
}

# Ordre d'affichage des catégories
CATEGORY_ORDER = [
    "Outils",
    "Ressources", 
    "Pets",
    "Alchimie",
    "Recipe",
    "Thrall",
    "Atelier",
    "Sorcellery",
]

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.shop_channel_id = SHOP_CHANNEL_ID
        self.command_channel_id = COMMANDE_CHANNEL_ID
        print(f"✅ Cog Shop initialisé avec les IDs: Shop={self.shop_channel_id}, Commande={self.command_channel_id}")

    @commands.command()
    async def shop(self, ctx):
        """
        Affiche le shop dans le channel shop, groupé par catégorie, avec des embeds Discord stylés.
        Avant d'afficher, supprime les anciens messages du bot dans le channel shop.
        """
        print(f"Commande shop appelée dans le channel {ctx.channel.id}")
        print(f"Channel attendu: {self.command_channel_id}")
        
        # Vérifier que la commande est utilisée dans le bon channel
        if ctx.channel.id != self.command_channel_id:
            print(f"❌ Mauvais channel. Channel actuel: {ctx.channel.id}, Channel attendu: {self.command_channel_id}")
            await ctx.send("❌ Cette commande ne peut être utilisée que dans le channel de commandes.")
            return

        shop_channel = self.bot.get_channel(self.shop_channel_id)
        if shop_channel is None:
            print(f"❌ Channel shop non trouvé (ID: {self.shop_channel_id})")
            await ctx.send("❌ Le channel de shop n'a pas été trouvé (vérifiez SHOP_CHANNEL_ID).")
            return

        # Supprimer les anciens messages du bot dans le channel shop (limite 50 derniers)
        try:
            def is_bot_message(m):
                return m.author == self.bot.user
            deleted = await shop_channel.purge(limit=50, check=is_bot_message)
            print(f"🗑️ {len(deleted)} anciens messages supprimés dans le shop.")
        except Exception as e:
            print(f"Erreur lors de la suppression des anciens messages : {e}")

        # Lire les items depuis la base de données
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name, id_item_shop, count, price, category FROM items WHERE enabled = 1 ORDER BY category, name")
            items = cursor.fetchall()
            conn.close()
        except Exception as e:
            await ctx.send(f"❌ Erreur lors de la lecture de la base de données: {e}")
            return

        # Organiser les items par catégorie
        shop_dict = {}
        for name, id_item_shop, count, price, category in items:
            if category not in shop_dict:
                shop_dict[category] = []
            shop_dict[category].append({
                'name': name,
                'id_item_shop': id_item_shop,
                'count': count,
                'price': price
            })

        # Envoyer un embed par catégorie dans l'ordre défini
        for category in CATEGORY_ORDER:
            if category in shop_dict:  # Vérifier que la catégorie existe
                items = shop_dict[category]
                style = CATEGORY_STYLES.get(category, {"color": 0x95A5A6, "icon": None})
                
                embed = discord.Embed(
                    title=f"__**{category.upper()}**__",
                    description=f"*{len(items)} item(s) disponible(s)*",
                    color=style["color"]
                )
                if style["icon"]:
                    embed.set_thumbnail(url=style["icon"])
                    
                for item in items:
                    embed.add_field(
                        name=f"🔹 {item['name']} (ID: {item['id_item_shop']})",
                        value=f"📦 Quantité: `{item['count']}`\n💰 Prix: `{item['price']} coins`",
                        inline=False
                    )
                    
                embed.set_footer(text=f"Utilisez !buy <ID> pour acheter un item")
                await shop_channel.send(embed=embed)
        
        # Afficher les catégories non définies dans CATEGORY_ORDER (au cas où)
        for category, items in shop_dict.items():
            if category not in CATEGORY_ORDER:
                style = CATEGORY_STYLES.get(category, {"color": 0x95A5A6, "icon": None})
                embed = discord.Embed(
                    title=f"__**{category.upper()}**__ ⚠️",
                    description=f"*{len(items)} item(s) - Catégorie non classée*",
                    color=style["color"]
                )
                for item in items:
                    embed.add_field(
                        name=f"🔹 {item['name']} (ID: {item['id_item_shop']})",
                        value=f"📦 Quantité: `{item['count']}`\n💰 Prix: `{item['price']} coins`",
                        inline=False
                    )
                await shop_channel.send(embed=embed)
        await ctx.send("✅ Shop affiché dans le channel shop avec des embeds stylés !")

async def setup(bot):
    print("Chargement du Cog Shop...")
    await bot.add_cog(Shop(bot))
    print("✅ Cog Shop chargé avec succès")