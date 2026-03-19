#!/bin/bash

# --- 🛡️ 6372 HYBRID AI SENTINEL: Professional Startup v5 ---
# Author: myikgetzweb3

PROJ_DIR="/home/myikgetzweb3/6372-hybrid-ai-sentinel"
PID_FILE="$PROJ_DIR/sentinel.pid"
G_PID_FILE="$PROJ_DIR/guardian.pid"
LOG_FILE="$PROJ_DIR/activity.log"

echo -e "\033[96m🛡️  6372 Guardian: Booting system...\033[0m"

# 1. Clean shutdown
bash "$PROJ_DIR/stop.sh"
rm -f "$PID_FILE" "$G_PID_FILE"
sleep 2

# 2. Start Guardian
nohup bash -c "
echo \$\$ > '$G_PID_FILE'
export PYTHONPATH=\$PYTHONPATH:$PROJ_DIR/src
cd $PROJ_DIR
while true; do
    RUNNING=false
    if [ -f '$PID_FILE' ]; then
        MPID=\$(cat '$PID_FILE')
        if [ ! -z \"\$MPID\" ] && ps -p \$MPID > /dev/null; then
            RUNNING=true
        fi
    fi

    if [ \"\$RUNNING\" = false ]; then
        echo \"\$(date) [RECOVERY] Starting Sentinel...\" >> '$LOG_FILE'
        python3 src/main.py >> '$LOG_FILE' 2>&1 &
        NEW_PID=\$!
        echo \$NEW_PID > '$PID_FILE'
        sleep 2
    fi
    sleep 5
done
" > /dev/null 2>&1 &

echo -e "\033[92m✅ 6372 Supreme Protocol ACTIVE.\033[0m"
echo -e "💡 Dashboard: \033[96m6372-status\033[0m"
