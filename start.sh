#!/bin/bash

# --- 🛡️ 6372 HYBRID AI SENTINEL: Supreme Process Guardian ---
# Author: myikgetzweb3

PROJ_DIR="/home/myikgetzweb3/6372-hybrid-ai-sentinel"
LOG_FILE="$PROJ_DIR/activity.log"
MAIN_SCRIPT="$PROJ_DIR/src/main.py"

CYAN='\033[96m'
BOLD='\033[1m'
NC='\033[0m'
GREEN='\033[0;32m'

# Clear screen for fresh startup
clear
sleep 0.1

echo -e "${CYAN}${BOLD}🛡️  6372 Guardian: Mengaktifkan Protokol Penjagaan...${NC}"
echo -e "\033[2m      Developed by myikgetzweb3${NC}\n"

# 1. TOTAL CLEANUP: Matikan SEMUA monitor DAN guardian lama
echo -e "${DIM}Cleaning up old processes...${NC}"
pkill -f "$MAIN_SCRIPT" 2>/dev/null
pkill -f "while true; do.*$MAIN_SCRIPT" 2>/dev/null
sleep 2

# 2. Guardian Loop (Nohup Background with Robust Detection)
nohup bash -c "
while true; do 
    # Log Rotation (Max ~10MB)
    if [ -f \"$LOG_FILE\" ]; then
        FILESIZE=\$(stat -c%s \"$LOG_FILE\")
        if [ \$FILESIZE -ge 10485760 ]; then
            mv \"$LOG_FILE\" \"$LOG_FILE.old\"
            echo \"\$(date) [GUARDIAN] Log rotated.\" > \"$LOG_FILE\"
        fi
    fi

    # Pengecekan Presisi: Hanya cari proses PYTHON yang menjalankan script kita
    if ! pgrep -f \"python3 $MAIN_SCRIPT\" > /dev/null; then 
        echo \"\$(date) [GUARDIAN] Sentinel Down. Engaging Auto-Recovery...\" >> \"$LOG_FILE\"
        python3 \"$MAIN_SCRIPT\" >> \"$LOG_FILE\" 2>&1
    fi
    sleep 15
done
" > /dev/null 2>&1 &

echo -e "✅ ${GREEN}6372 Supreme Protocol ACTIVE.${NC}"
echo -e "${BOLD}💡 NAVIGASI:${NC} ${CYAN}6372-status${NC} | ${CYAN}6372-config${NC}"
