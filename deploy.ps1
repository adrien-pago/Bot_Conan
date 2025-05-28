# lancé la commande : .\deploy.ps1
# Créer le dossier Deploy-files
New-Item -ItemType Directory -Force -Path "Deploy-files"

# Copier les fichiers nécessaires
Copy-Item "bot.py","classement.py", ".env", "database.py", "rcon.py", "ftp_handler.py", "requirements.txt", "bot_conan.service", "discord.db" -Destination "Deploy-files"

# Copier le fichier de log s'il existe
if (Test-Path "bot.log") {
    Copy-Item "bot.log" -Destination "Deploy-files"
}

# Afficher les fichiers copiés
Write-Host "Déploiement terminé avec succès !"
Write-Host "Les fichiers suivants ont été copiés :"
Write-Host "- bot.py"
Write-Host "- database.py"
Write-Host "- rcon.py"
Write-Host "- ftp_handler.py"
Write-Host "- requirements.txt"
Write-Host "- bot_conan.service"
Write-Host "- discord.db"
Write-Host "- classement.py"
if (Test-Path "bot.log") {
    Write-Host "- bot.log"
}

# Pour copier sur le VPS, utilisez cette commande dans PowerShell :
Write-Host "Pour copier sur le VPS, utilisez cette commande :"
Write-Host "scp -r C:\Users\adrie\Documents\GitHub\Bot_Conan\Deploy-files\* root@212.227.47.132:/root/bot/bot_conan/"