#!/bin/bash

# Script de surveillance du bot Conan
# À placer dans /root/bot/bot_conan/ sur le VPS
# Usage: ./monitor_bot.sh

LOG_FILE="/var/log/bot_conan_monitor.log"
SERVICE_NAME="bot_conan"
BROKEN_PIPE_THRESHOLD=5  # Nombre d'erreurs Broken pipe avant redémarrage
TIME_WINDOW=300          # Fenêtre de temps en secondes (5 minutes)

# Fonction de logging
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Fonction pour compter les erreurs Broken pipe récentes
count_broken_pipe_errors() {
    local since_time=$(date -d "$TIME_WINDOW seconds ago" '+%Y-%m-%d %H:%M:%S')
    local error_count=$(journalctl -u "$SERVICE_NAME" --since "$since_time" | grep -c "Broken pipe\|Connexion RCON perdue" || echo "0")
    echo "$error_count"
}

# Fonction pour vérifier si le service est actif
is_service_running() {
    systemctl is-active --quiet "$SERVICE_NAME"
    return $?
}

# Fonction pour redémarrer le service
restart_service() {
    log_message "🔄 Redémarrage du service $SERVICE_NAME..."
    systemctl restart "$SERVICE_NAME"
    
    # Attendre 10 secondes et vérifier si le redémarrage a réussi
    sleep 10
    if is_service_running; then
        log_message "✅ Service $SERVICE_NAME redémarré avec succès"
        return 0
    else
        log_message "❌ Échec du redémarrage du service $SERVICE_NAME"
        return 1
    fi
}

# Fonction principale de surveillance
monitor_bot() {
    log_message "🚀 Démarrage de la surveillance du bot Conan"
    
    while true; do
        # Vérifier si le service est en cours d'exécution
        if ! is_service_running; then
            log_message "⚠️ Service $SERVICE_NAME arrêté, tentative de redémarrage..."
            restart_service
        else
            # Compter les erreurs Broken pipe récentes
            broken_pipe_count=$(count_broken_pipe_errors)
            
            if [ "$broken_pipe_count" -ge "$BROKEN_PIPE_THRESHOLD" ]; then
                log_message "🚨 Détection de $broken_pipe_count erreurs RCON dans les dernières $((TIME_WINDOW/60)) minutes"
                log_message "🔧 Seuil de $BROKEN_PIPE_THRESHOLD erreurs atteint, redémarrage préventif..."
                restart_service
                
                # Attendre plus longtemps après un redémarrage préventif
                log_message "⏳ Attente de 2 minutes avant la prochaine vérification..."
                sleep 120
            else
                log_message "✅ Service $SERVICE_NAME fonctionne correctement ($broken_pipe_count erreurs RCON récentes)"
            fi
        fi
        
        # Attendre 60 secondes avant la prochaine vérification
        sleep 60
    done
}

# Fonction pour installer le service de surveillance
install_monitor_service() {
    cat > /etc/systemd/system/bot_conan_monitor.service << EOF
[Unit]
Description=Bot Conan Monitor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/bot/bot_conan
ExecStart=/root/bot/bot_conan/monitor_bot.sh
Restart=always
RestartSec=30
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable bot_conan_monitor
    log_message "📦 Service de surveillance installé et activé"
}

# Fonction pour désinstaller le service de surveillance
uninstall_monitor_service() {
    systemctl stop bot_conan_monitor 2>/dev/null
    systemctl disable bot_conan_monitor 2>/dev/null
    rm -f /etc/systemd/system/bot_conan_monitor.service
    systemctl daemon-reload
    log_message "🗑️ Service de surveillance désinstallé"
}

# Gestion des arguments de ligne de commande
case "${1:-monitor}" in
    "monitor")
        monitor_bot
        ;;
    "install")
        install_monitor_service
        echo "✅ Service de surveillance installé. Démarrez-le avec: systemctl start bot_conan_monitor"
        ;;
    "uninstall")
        uninstall_monitor_service
        echo "✅ Service de surveillance désinstallé"
        ;;
    "status")
        echo "📊 Statut du bot:"
        systemctl status "$SERVICE_NAME" --no-pager -l
        echo ""
        echo "📊 Statut du monitoring:"
        systemctl status bot_conan_monitor --no-pager -l 2>/dev/null || echo "Service de monitoring non installé"
        echo ""
        echo "📈 Erreurs RCON récentes (dernières 5 minutes):"
        error_count=$(count_broken_pipe_errors)
        echo "Nombre d'erreurs: $error_count"
        ;;
    "logs")
        echo "📋 Logs du bot (dernières 50 lignes):"
        journalctl -u "$SERVICE_NAME" -n 50 --no-pager
        echo ""
        echo "📋 Logs du monitoring:"
        tail -20 "$LOG_FILE" 2>/dev/null || echo "Aucun log de monitoring trouvé"
        ;;
    *)
        echo "Usage: $0 {monitor|install|uninstall|status|logs}"
        echo ""
        echo "Commandes:"
        echo "  monitor    - Surveiller le bot en continu (défaut)"
        echo "  install    - Installer le service de surveillance automatique"
        echo "  uninstall  - Désinstaller le service de surveillance"
        echo "  status     - Afficher le statut du bot et du monitoring"
        echo "  logs       - Afficher les logs récents"
        exit 1
        ;;
esac 