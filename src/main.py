import os
import sys
import time
import json
import threading
import asyncio
import signal
import stat
import utils
from core.database import SupremeDatabase
from core.market import MarketSentinel
from core.ai import IntelligenceSentinel

# --- DEVELOPER INFO ---
# Author: myikgetzweb3
# Project: 6372 HYBRID AI SENTINEL (Supreme Orchestrator)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
        default_cfg = {
            "assets": {"BTC": {"symbol": "BTCUSDT", "emoji": "₿ ", "thresholds": {"hourly": 1.0, "dips": [], "spikes": []}}},
            "sources": {"rss_feeds": [], "x_accounts": [], "youtube": [], "nitter_instances": ["https://nitter.net"]},
            "ai_prompts": {"local": "Trader mode: {text}", "online": "Analyst mode: {text}"},
            "user_strategy": {"type": "DCA"}
        }
        if not os.path.exists(CONFIG_PATH):
            return default_cfg
        try:
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        except: return default_cfg

    def _check_security(self):
        env_path = os.path.join(BASE_DIR, ".env")
        if os.path.exists(env_path) and not utils.IS_WINDOWS:
            mode = os.stat(env_path).st_mode
            if mode & stat.S_IROTH:
                utils.logger.warning("SECURITY: .env is world-readable! chmod 600 .env recommended.")

    async def _backup_loop(self):
        while self.running:
            await asyncio.sleep(3600)
            utils.backup_database()

    def shutdown(self, signum, frame):
        utils.logger.info("Shutting down Sentinel...")
        self.running = False
        self.market.running = False
        # Remove PID file on clean exit
        pid_file = os.path.join(BASE_DIR, "sentinel.pid")
        if os.path.exists(pid_file): os.remove(pid_file)
        sys.exit(0)

    async def run(self):
        utils.clear_terminal()
        w = utils.get_terminal_width()
        THEME, BOLD, RESET = "\033[96m", "\033[1m", "\033[0m"
        
        for line in utils.get_logo(): print(utils.center_line(f"{THEME}{BOLD}{line}{RESET}", w))
        print(utils.center_line(f"{THEME}{BOLD}HYBRID AI SENTINEL v2.0{RESET}", w))
        print(utils.center_line(f"\033[2m{utils.get_brand_credit()}{RESET}", w) + "\n")
        
        if utils.is_monitor_running():
            print(utils.center_line(f"\033[91m⚠️  Sentinel is already active.\033[0m", w))
            return

        # 0. Register PID for Dashboard Synchronization
        with open(os.path.join(BASE_DIR, "sentinel.pid"), "w") as f:
            f.write(str(os.getpid()))

        self._check_security()
        
        # 1. Start WebSockets (Threaded - Non-blocking for Async Loop)
        self.market.start() 
        
        # 2. Set scroll region for logs (Only if interactive TTY)
        if sys.stdout.isatty():
            sys.stdout.write("\033[14;r\033[14;1H")
            sys.stdout.flush()
        
        # 3. Run Polling Loops (Async)
        await asyncio.gather(
            self.market.start_async(),
            self.intelligence.start_async(),
            self._backup_loop()
        )

if __name__ == "__main__":
    app = SentinelApp()
    signal.signal(signal.SIGINT, app.shutdown)
    signal.signal(signal.SIGTERM, app.shutdown)
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt: pass
