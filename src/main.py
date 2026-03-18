import os
import sys
import time
import json
import threading
import signal

# --- DYNAMIC PATH SETUP ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

import utils
from core.database import SupremeDatabase
from core.market import MarketSentinel
from core.ai import IntelligenceSentinel

# --- DEVELOPER INFO ---
# Author: myikgetzweb3
# Project: 6372 HYBRID AI SENTINEL (Supreme Orchestrator)

BASE_DIR = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "6372.db")
CONFIG_PATH = os.path.join(BASE_DIR, "config", "settings.json")

class SentinelApp:
    def __init__(self):
        self.running = True
        self.db = SupremeDatabase(DB_PATH)
        self.config = self._load_config()
        self.intelligence = IntelligenceSentinel(self.db, self.config)
        self.market = MarketSentinel(self.db, self.config, ai_engine=self.intelligence)

    def _load_config(self):
        if not os.path.exists(CONFIG_PATH):
            return {"assets": {}, "sources": {"rss_feeds": [], "x_accounts": []}, "ai_prompts": {}}
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)

    def shutdown(self, signum, frame):
        utils.logger.info("Termination signal received. Shutting down engines...")
        self.running = False
        self.market.running = False
        self.intelligence.running = False
        sys.exit(0)

    def run(self):
        utils.clear_terminal()
        w = utils.get_terminal_width()
        THEME, BOLD, RESET, DIM = "\033[96m", "\033[1m", "\033[0m", "\033[2m"
        
        # 1. Header (Standardized)
        for line in utils.get_logo():
            print(utils.center_line(f"{THEME}{BOLD}{line}{RESET}", w))
        
        print(utils.center_line(f"{THEME}{BOLD}HYBRID AI SENTINEL v2.0{RESET}", w))
        print(utils.center_line(f"{DIM}{utils.get_brand_credit()}{RESET}", w) + "\n")
        
        if utils.is_monitor_running():
            print(utils.center_line(f"\033[91m⚠️  Sentinel is already active.\033[0m", w))
            return

        print(utils.center_line(f"{THEME}━━━━━━━━━━━━ SYSTEM INITIALIZING ━━━━━━━━━━━━{RESET}", w))
        utils.logger.info("Modular Surveillance Matrix Engaged.")
        
        # 2. Start Subsystems
        self.market.start()
        self.intelligence.start()
        
        print(utils.center_line(f"{BOLD}💡 NAVIGASI:{RESET} {THEME}6372-status{RESET} | {THEME}6372-config{RESET}", w))
        print(utils.center_line(f"{DIM}[Surveillance streams are active in background]{RESET}", w) + "\n")
        
        # 3. Log Scroll Region
        sys.stdout.write("\033[14;r\033[14;1H")
        sys.stdout.flush()
        
        while self.running:
            time.sleep(1)

if __name__ == "__main__":
    app = SentinelApp()
    signal.signal(signal.SIGINT, app.shutdown)
    signal.signal(signal.SIGTERM, app.shutdown)
    app.run()
