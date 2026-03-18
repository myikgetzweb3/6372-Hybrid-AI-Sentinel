import os
import sys
import time
import json
import select
import shutil
import re
from datetime import datetime

# Path Bootstrapping (Universal)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
sys.path.append(os.path.join(BASE_DIR, "src"))

import utils
from core.database import SupremeDatabase

# --- 🎨 THEME & STYLES ---
THEME, GREEN, YELLOW, RED, BOLD, RESET, DIM = "\033[96m", "\033[92m", "\033[93m", "\033[91m", "\033[1m", "\033[0m", "\033[2m"

def get_quota_bar(count, limit=1500, width=30):
    rem = max(0, limit - count)
    perc = (rem / limit) * 100
    filled = int(width * rem // limit)
    bar = "█" * filled + "░" * (width - filled)
    c = GREEN if perc >= 50 else (YELLOW if perc >= 20 else RED)
    return f"{c}[{bar}] {rem}/{limit}{RESET}"

def show_intel_inbox(db):
    while True:
        utils.clear_terminal()
        w = utils.get_terminal_width()
        print("\n" * 2)
        print(utils.center_line(f"{THEME}{BOLD}📥 TACTICAL INTEL INBOX{RESET}", w))
        print(utils.center_line(f"{THEME}{'━' * 60}{RESET}", w))
        
        archive = db.get_all_intel()
        if not archive: 
            print("\n" * 2)
            print(utils.center_line(f"{DIM}(Inbox Kosong){RESET}", w))
        else:
            header = f"{BOLD}{'ID':<4} | {'WAKTU':<8} | {'SUMBER':<10} | {'JUDUL BERITA'}{RESET}"
            print(utils.center_line(header, w))
            print(utils.center_line(f"{DIM}{'━' * 70}{RESET}", w))
            for r in archive[:15]: 
                line = f"{THEME}{r['id']: <4}{RESET} | {r['time_str']} | {YELLOW}{r['source']: <10}{RESET} | {r['title'][:max(10, w-50)]}"
                print(utils.center_line(line, w + 10))
        
        print("\n" + utils.center_line(f"{THEME}{'━' * 60}{RESET}", w))
        print(utils.center_line(f"{BOLD}💡 AKSI:{RESET} [ID] Baca | q Kembali", w))
        sys.stdout.write(utils.center_line(f"{YELLOW}⌨️  PILIH : {RESET}", w-10))
        sys.stdout.flush()
        
        choice = sys.stdin.readline().strip().lower()
        if choice == 'q': break
        if choice.isdigit():
            report = next((r for r in archive if str(r['id']) == choice), None)
            if report:
                utils.clear_terminal()
                print("\n" * 3)
                print(utils.center_line(f"{THEME}{BOLD}📜 DETAIL INTELIJEN - ID #{choice}{RESET}", w))
                print(utils.center_line(f"{DIM}Sumber: {report['source']} | Waktu: {report['time_str']}{RESET}", w))
                print(utils.center_line(f"{THEME}{'━' * 60}{RESET}", w) + "\n")
                import textwrap
                wrapped = textwrap.wrap(report['message'], width=min(w-10, 80))
                for wl in wrapped: print(utils.center_line(wl, w))
                print("\n" + utils.center_line(f"{THEME}{'━' * 60}{RESET}", w))
                input(utils.center_line(f"{YELLOW}Tekan Enter untuk kembali...{RESET}", w))

def print_static_ui(w, config):
    utils.clear_terminal()
    # 1. Header Logo
    for line in utils.get_logo():
        print(utils.center_line(f"{THEME}{BOLD}{line}{RESET}", w))
    
    print(utils.center_line(f"{THEME}{BOLD}HYBRID AI SENTINEL v2.0{RESET}", w))
    print(utils.center_line(f"{DIM}{utils.get_brand_credit()}{RESET}", w) + "\n")
    
    # 2. Scope Static Box
    print(utils.center_line(f"{THEME}{'━' * 55}{RESET}", w))
    print(utils.center_line(f"{THEME}━ SCOPE ━{RESET}", w))
    print(utils.center_line(f"{THEME}{'━' * 55}{RESET}", w))
    print("\n") 
    
    # 3. Market Radar Static
    print(utils.center_line(f"{THEME}{BOLD}📈 MARKET RADAR (ACTIVE){RESET}", w) + "\n")
    print("\n" * 12)
    
    # 4. AI Registry Static
    print(utils.center_line(f"{THEME}━ AI AGENT REGISTRY ━{RESET}", w))
    print("\n" * 2)
    
    # 5. Inflow Static
    sources = config.get('sources', {})
    inflow_text = f"{THEME}📡 DATA INFLOW:{RESET} {DIM}{len(sources.get('x_accounts', []))} X | {len(sources.get('youtube', []))} YT | {len(sources.get('rss_feeds', []))} RSS{RESET}"
    print(utils.center_line(inflow_text, w))
    print("\n" + utils.center_line(f"{THEME}{DIM}{'━' * 60}{RESET}", w))
    print(utils.center_line(f"{BOLD}💡 [ /config | /monitor | /intel | /restart | /exit ]{RESET}", w))

def main_dashboard():
    db = SupremeDatabase(os.path.join(BASE_DIR, "data/6372.db"))
    cfg_path = os.path.join(BASE_DIR, "config/settings.json")
    
    if os.path.exists(cfg_path):
        with open(cfg_path, 'r') as f: config = json.load(f)
    else: config = {"assets": {}}
    
    last_w = utils.get_terminal_width()
    print_static_ui(last_w, config)
    
    last_ref = 0
    while True:
        w = utils.get_terminal_width()
        if w != last_w:
            print_static_ui(w, config)
            last_w = w
            last_ref = 0

        now = time.time()
        if now - last_ref > 5:
            pid = utils.is_monitor_running()
            quota = db.get_quota()
            
            # --- Update Scope (Line 12) ---
            sys.stdout.write("\033[12;1H\033[K")
            status_line = f"{THEME}[{RESET} SYSTEM {THEME}]{RESET} {'🟢 ' + utils.get_text('active') if pid else '🔴 ' + utils.get_text('inactive')} | PID: {pid if pid else '---'}"
            sys.stdout.write(utils.center_line(status_line, w) + "\n")
            
            # --- Update Market Radar (Lines 16+) ---
            sys.stdout.write("\033[16;1H")
            assets = config.get("assets", {})
            for a, d in assets.items():
                data = db.get_asset_state(a)
                
                # REFINED TABULAR LOGIC (Emoji-Aware)
                emoji = d.get('emoji', '💰').strip()
                # Use fixed-width fields without leading/trailing spaces for calculation
                f_name = f"{a:<10}"
                f_price = f": ${data.get('price', 0):,.8f}"
                f_price = f"{f_price:<22}"
                
                meta = ""
                if data.get("onchain"):
                    oc = data["onchain"]
                    if "unconfirmed" in oc: meta = f"| ⛓️ {oc['unconfirmed']}"
                    elif "m5_activity" in oc:
                        m = oc["m5_activity"]; meta = f"| 🐳 B:{m.get('buys',0)}/S:{m.get('sells',0)}"
                    elif "gas_gwei" in oc: meta = f"| ⛽ {oc['gas_gwei']}g"
                f_meta = f"{meta:<25}"
                
                st_val = data.get("tier")
                if st_val is None or isinstance(st_val, str): 
                    st_text = f"[ {utils.get_text('stable')} ]"; st_color = DIM
                else:
                    st_text = f"[ {st_val:+.2f}% ]"; st_color = RED if st_val < 0 else GREEN
                f_status = f">> {st_text:<14}"
                
                history = db.get_asset_history(a, limit=10)
                spark_raw = utils.generate_sparkline(history, width=10) if len(history) >= 2 else ".........."
                
                # Dynamic Coloring for BTC/MOODENG
                spark_color = THEME
                if a in ["BTC", "MOODENG"] and data.get("onchain") and "sentiment" in data["onchain"]:
                    sent = data["onchain"]["sentiment"]
                    if sent == "whale_buy": spark_color = GREEN
                    elif sent == "whale_sell": spark_color = RED
                
                f_spark = f"{spark_raw:>12}"
                
                # Final Assembly - Using explicit spacers to avoid emoji width issues
                # We use 2 spaces after emoji as a buffer
                styled_row = (
                    f"{emoji}  "
                    f"{THEME}{BOLD}{f_name}{RESET} "
                    f"{BOLD}{f_price}{RESET} "
                    f"{DIM}{f_meta}{RESET} "
                    f"{st_color}{f_status}{RESET} "
                    f"{spark_color if len(history) >= 2 else DIM}{f_spark}{RESET}"
                )
                
                # Calculate proper centering by ignoring the ANSI codes and treating emoji as width 2
                sys.stdout.write("\033[K" + utils.center_line(styled_row, w) + "\n") 
            
            # --- Update AI Quota (Line 31) ---
            sys.stdout.write("\033[31;1H\033[K")
            sys.stdout.write(utils.center_line(f"GEMINI : {get_quota_bar(quota, width=min(w-20, 30))}", w) + "\n")
            
            sys.stdout.write("\033[36;1H")
            sys.stdout.flush()
            last_ref = now

        if select.select([sys.stdin], [], [], 0.1)[0]:
            cmd = sys.stdin.readline().strip()
            if cmd:
                if cmd.lower() in ["/q", "/exit"]: break
                if cmd.lower() in ["/i", "/intel"]: show_intel_inbox(db); print_static_ui(w, config); last_ref = 0
                if cmd.lower() in ["/c", "/config"]: 
                    os.system(f"python3 {os.path.join(BASE_DIR, 'src/ui/wizard.py')}")
                    print_static_ui(w, config); last_ref = 0
                sys.stdout.write("\033[36;1H\033[K")
                sys.stdout.flush()

if __name__ == "__main__":
    try:
        sys.stdout.write("\033[?25l")
        main_dashboard()
    except KeyboardInterrupt: pass
    finally:
        sys.stdout.write("\033[?25h")
        utils.clear_terminal()
