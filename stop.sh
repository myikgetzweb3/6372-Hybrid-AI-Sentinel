#!/bin/bash

# --- 🛡️ 6372 HYBRID AI SENTINEL: THE NUCLEAR STOP ---
# Author: myikgetzweb3

PROJ_DIR="/home/myikgetzweb3/6372-hybrid-ai-sentinel"
PID_FILE="$PROJ_DIR/sentinel.pid"
G_PID_FILE="$PROJ_DIR/guardian.pid"

echo -e "\033[91m🛡️  6372 Sentinel: PERINGATAN! Menghentikan SEMUA sistem secara paksa...\033[0m"

# 1. Matikan Guardian (apapun caranya)
if [ -f "$G_PID_FILE" ]; then
    GPID=$(cat "$G_PID_FILE")
    kill -9 $GPID 2>/dev/null
    rm -f "$G_PID_FILE"
fi
pkill -9 -f "while true; do.*main.py" 2>/dev/null

# 2. Matikan Mesin Utama (apapun caranya)
if [ -f "$PID_FILE" ]; then
    MPID=$(cat "$PID_FILE")
    kill -9 $MPID 2>/dev/null
    rm -f "$PID_FILE"
fi
pkill -9 -f "python3.*/6372-hybrid-ai-sentinel/src/main.py" 2>/dev/null
pkill -9 -f "python3 src/main.py" 2>/dev/null

# 3. Jeda Krusial (Menunggu OS membersihkan tabel proses)
sleep 2

echo -e "\033[92m✅ 6372 System TOTALLY STOPPED. Memory cleared.\033[0m"
