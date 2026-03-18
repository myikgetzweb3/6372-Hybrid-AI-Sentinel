#!/bin/bash

# --- 🛡️ 6372 HYBRID AI SENTINEL: Universal Setup Wizard ---
# Author: myikgetzweb3

CYAN='\033[96m'
BOLD='\033[1m'
NC='\033[0m'
GREEN='\033[0;32m'

PROJ_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$PROJ_DIR"

clear
echo -e "${CYAN}${BOLD}🛡️ 6372 PROTOCOL INITIALIZING...${NC}"

# Python Path Setup
export PYTHONPATH=$PYTHONPATH:$PROJ_DIR/src

# Shell Aliases update (REBRANDING to 6372)
for RC in "$HOME/.bashrc" "$HOME/.zshrc"; do
    if [ -f "$RC" ]; then
        # Clean old aliases
        sed -i '/crypto-/d' "$RC"
        sed -i '/6372-/d' "$RC"
        # Add NEW supreme aliases
        echo "alias 6372-status='python3 $PROJ_DIR/src/ui/dashboard.py'" >> "$RC"
        echo "alias 6372-monitor='python3 $PROJ_DIR/src/main.py'" >> "$RC"
        echo "alias 6372-config='python3 $PROJ_DIR/src/ui/wizard.py'" >> "$RC"
        echo -e "${GREEN}✅ 6372 Aliases integrated into $RC${NC}"
    fi
done

mkdir -p data 2>/dev/null

echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "🚀 ${BOLD}6372 HYBRID AI SENTINEL READY!${NC}"
echo -e "Commands: ${CYAN}6372-status${NC}, ${CYAN}6372-config${NC}, ${CYAN}6372-monitor${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "Silakan jalankan: ${BOLD}source ~/.bashrc${NC} atau restart terminal."
