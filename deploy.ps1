# lancé la commande : .\deploy.ps1
# Créer le dossier de déploiement
$deployFolder = "Deploy-files"
New-Item -ItemType Directory -Force -Path $deployFolder

# Créer la structure de dossiers (ajout du dossier commandes)
$folders = @("config", "core", "commandes", "database", "features", "logs", "logs\archives", "utils")
foreach ($folder in $folders) {
    New-Item -ItemType Directory -Force -Path "$deployFolder\$folder"
}

# Copier les fichiers principaux
Copy-Item "bot.py", ".env", "requirements.txt", "bot_conan.service", "monitor_bot.sh" -Destination $deployFolder

# Copier les dossiers avec leur contenu
Copy-Item "config\*" -Destination "$deployFolder\config" -Recurse -Force
Copy-Item "core\*" -Destination "$deployFolder\core" -Recurse -Force
Copy-Item "commandes\*" -Destination "$deployFolder\commandes" -Recurse -Force
Copy-Item "database\*" -Destination "$deployFolder\database" -Recurse -Force
Copy-Item "features\*" -Destination "$deployFolder\features" -Recurse -Force
Copy-Item "utils\*" -Destination "$deployFolder\utils" -Recurse -Force

# Créer la structure de logs avec archives
New-Item -ItemType Directory -Force -Path "$deployFolder\logs"
New-Item -ItemType Directory -Force -Path "$deployFolder\logs\archives"

# Copier les fichiers de log existants (nouveau système)
if (Test-Path "logs\bot_activity.log") {
    Copy-Item "logs\bot_activity.log" -Destination "$deployFolder\logs" -Force
}

# Copier les archives de logs si elles existent
if (Test-Path "logs\archives\*") {
    Copy-Item "logs\archives\*" -Destination "$deployFolder\logs\archives" -Force
}

# Afficher les fichiers copiés
Write-Host "🚀 Déploiement terminé avec succès !"
Write-Host ""
Write-Host "📦 Les fichiers et dossiers suivants ont été copiés :"
Write-Host "- bot.py"
Write-Host "- .env"
Write-Host "- requirements.txt"
Write-Host "- bot_conan.service"
Write-Host "- monitor_bot.sh"
Write-Host "- Dossier config/ (avec nouveau système de logging)"
Write-Host "- Dossier core/"
Write-Host "- Dossier commandes/ (avec logs d achat)"
Write-Host "- Dossier database/"
Write-Host "- Dossier features/"
Write-Host "- Dossier utils/"
Write-Host "- Dossier logs/ (avec archives quotidiennes)"

Write-Host ""
Write-Host "📝 NOUVEAU SYSTÈME DE LOGGING :"
Write-Host "- Un seul fichier : logs/bot_activity.log"
Write-Host "- Contenu : Erreurs + commandes !buy uniquement"
Write-Host "- Archives : logs/archives/bot_activity_YYYY-MM-DD.log"
Write-Host "- Rotation : Quotidienne à minuit"
Write-Host "- Rétention : 30 jours"

# Pour copier sur le VPS, utilisez cette commande dans PowerShell :
Write-Host ""
Write-Host "🌐 Pour copier sur le VPS, utilisez cette commande :"
Write-Host "scp -r Deploy-files/* root@212.227.47.132:/root/bot/bot_conan/"
Write-Host ""
Write-Host "🔄 Après le transfert, redémarrez le service avec :"
Write-Host "ssh root@212.227.47.132"
Write-Host "systemctl restart bot_conan"
Write-Host ""
