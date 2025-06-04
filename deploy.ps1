# lancé la commande : .\deploy.ps1
# Créer le dossier de déploiement
$deployFolder = "Deploy-files"
New-Item -ItemType Directory -Force -Path $deployFolder

# Créer la structure de dossiers
$folders = @("config", "core", "database", "features", "logs", "utils")
foreach ($folder in $folders) {
    New-Item -ItemType Directory -Force -Path "$deployFolder\$folder"
}

# Copier les fichiers principaux
Copy-Item "bot.py", ".env", "requirements.txt", "bot_conan.service", "discord.db" -Destination $deployFolder

# Copier les dossiers avec leur contenu
Copy-Item "config\*" -Destination "$deployFolder\config" -Recurse
Copy-Item "core\*" -Destination "$deployFolder\core" -Recurse
Copy-Item "commandes\*" -Destination "$deployFolder\commandes" -Recurse
Copy-Item "database\*" -Destination "$deployFolder\database" -Recurse
Copy-Item "features\*" -Destination "$deployFolder\features" -Recurse
Copy-Item "utils\*" -Destination "$deployFolder\utils" -Recurse

# Créer le dossier logs s'il n'existe pas
New-Item -ItemType Directory -Force -Path "$deployFolder\logs"

# Copier le fichier de log s'il existe
if (Test-Path "logs\bot.log") {
    Copy-Item "logs\bot.log" -Destination "$deployFolder\logs"
}

# Afficher les fichiers copiés
Write-Host "Déploiement terminé avec succès !"
Write-Host "Les fichiers et dossiers suivants ont été copiés :"
Write-Host "- bot.py"
Write-Host "- .env"
Write-Host "- requirements.txt"
Write-Host "- bot_conan.service"
Write-Host "- discord.db"
Write-Host "- Dossier config/"
Write-Host "- Dossier core/"
Write-Host "- Dossier database/"
Write-Host "- Dossier commandes/"
Write-Host "- Dossier features/"
Write-Host "- Dossier utils/"
Write-Host "- Dossier logs/"

# Pour copier sur le VPS, utilisez cette commande dans PowerShell :
Write-Host ""
Write-Host "Pour copier sur le VPS, utilisez cette commande :"
Write-Host "scp -r Deploy-files/* root@212.227.47.132:/root/bot/bot_conan/"
Write-Host ""
Write-Host "Après le transfert, n'oubliez pas de redémarrer le service avec :"
Write-Host "ssh root@212.227.47.132 'systemctl restart bot_conan'"