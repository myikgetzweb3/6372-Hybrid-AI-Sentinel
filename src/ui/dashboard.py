import os
import sys
import time
import json
import select
import shutil
import re
import warnings
from datetime import datetime

# Matikan peringatan agar TUI bersih
warnings.filterwarnings("ignore")

# Path Bootstrapping
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
sys.path.append(os.path.join(BASE_DIR, "src"))

import utils
from core.database import SupremeDatabase

# --- 🎨 THEME & STYLES ---
THEME, GREEN, YELLOW, RED, BOLD, RESET, DIM = "\033[96m", "\033[92m", "\033[93m", "\033[91m", "\033[1m", "\033[0m", "\033[2m"
START_TIME = datetime.now()

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
        tsize = shutil.get_terminal_size()
        w, h = tsize.columns, tsize.lines
        if h < 38:
            print(f"\n\n{RED}{BOLD}⚠️  TERMINAL TERLALU KECIL ({h} baris){RESET}"); time.sleep(2); break

        for line in utils.get_logo(): print(utils.center_line(f"{THEME}{BOLD}{line}{RESET}", w))
        print(utils.center_line(f"{THEME}{BOLD}📥 TACTICAL INTEL INBOX{RESET}", w))

        # Consistent Scope Header for Inbox
        border = "━" * min(w-4, 75)
        print(utils.center_line(f"{THEME}{border}{RESET}", w))
        uptime = datetime.now() - START_TIME
        sys.stdout.write(utils.center_line(f"{DIM}UPTIME: {str(uptime).split('.')[0]} | DATABASE: 📁 6372.db{RESET}", w) + "\n")
        print(utils.center_line(f"{THEME}{border}{RESET}", w) + "\n")

        archive = db.get_all_intel()

        if not archive: print("\n" * 2 + utils.center_line(f"{DIM}(Inbox Kosong){RESET}", w))
        else:
            header = f"{BOLD}{'ID':<4} | {'WAKTU':<8} | {'SUMBER':<10} | {'JUDUL BERITA'}{RESET}"
            print(utils.center_line(header, w))
            print(utils.center_line(f"{DIM}{'━' * 80}{RESET}", w))
            for r in archive[:15]: 
                title = r['title'].replace("\n", " ")
                line = f"{THEME}{r['id']: <4}{RESET} | {r['time_str']} | {YELLOW}{r['source']: <10}{RESET} | {title[:max(10, w-50)]}"
                print(utils.center_line(line, w + 10))
        
        print("\n" + utils.center_line(f"{THEME}{'━' * 75}{RESET}", w))
        print(utils.center_line(f"{BOLD}💡 AKSI:{RESET} [ID] Baca | q Kembali", w))
        sys.stdout.write(utils.center_line(f"{YELLOW}⌨️  PILIH : {RESET}", w-10))
        sys.stdout.flush()
        
        char = utils.get_key_universal()
        if not char: time.sleep(0.1); continue
        if char.lower() == 'q': break
        if char.isdigit():
            sys.stdout.write(char); sys.stdout.flush()
            remaining = sys.stdin.readline().strip()
            choice = char + remaining
            report = next((r for r in archive if str(r['id']) == choice), None)
            if report:
                utils.clear_terminal()
                print("\n" * 2)
                for line in utils.get_logo(): print(utils.center_line(f"{THEME}{BOLD}{line}{RESET}", w))
                print(utils.center_line(f"{THEME}{BOLD}📜 DETAIL INTELIJEN - ID #{choice}{RESET}", w))
                print(utils.center_line(f"{DIM}Sumber: {report['source']} | Waktu: {report['time_str']}{RESET}", w))
                print(utils.center_line(f"{THEME}{'━' * 75}{RESET}", w) + "\n")
                import textwrap
                wrapped = textwrap.wrap(report['message'], width=min(w-10, 85))
                for wl in wrapped: print(utils.center_line(wl, w))
                print("\n" + utils.center_line(f"{THEME}{'━' * 75}{RESET}", w))
                print(utils.center_line(f"{YELLOW}Tekan Enter untuk kembali...{RESET}", w))
                sys.stdin.readline()

def print_static_ui(w, config):
    utils.clear_terminal()
    for line in utils.get_logo(): print(utils.center_line(f"{THEME}{BOLD}{line}{RESET}", w))
    print(utils.center_line(f"{THEME}{BOLD}6372 HYBRID AI SENTINEL v2.0{RESET}", w))
    print(utils.center_line(f"{DIM}{utils.get_brand_credit()}{RESET}", w) + "\n")
    
    border = "━" * 85
    print(utils.center_line(f"{THEME}{border}{RESET}", w))
    print(utils.center_line(f"{THEME}━ SYSTEM SCOPE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}"[:len(border)], w))
    print("\n" * 2) 
    print(utils.center_line(f"{THEME}{border}{RESET}", w) + "\n")
    
    print(utils.center_line(f"{THEME}{BOLD}📈 MARKET RADAR (REAL-TIME STREAM){RESET}", w) + "\n")
    # Sub-header with hard-coded positioning
    header = f"  {'ASSET':<10} | {'PRICE':<18} | {'24H %':<10} | {'METADATA':<18} | {'TIER STATUS':<12} | {'TREND'}"
    print(utils.center_line(f"{BOLD}{header}{RESET}", w))
    print(utils.center_line(f"{DIM}{'─' * 85}{RESET}", w))
    print("\n" * 12) 
    
    print(utils.center_line(f"{THEME}{border}{RESET}", w))
    print(utils.center_line(f"{THEME}━ AI AGENT REGISTRY ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}"[:len(border)], w))
    print("\n" * 4) 
    print(utils.center_line(f"{THEME}{border}{RESET}", w))
    
    print(utils.center_line(f"{BOLD}{THEME}/config{RESET} | {BOLD}{THEME}/monitor{RESET} | {BOLD}{THEME}/intel{RESET} | {BOLD}{THEME}/restart{RESET} | {BOLD}{THEME}/exit{RESET}", w))
    print("\n")

def main_dashboard():
    db = SupremeDatabase(os.path.join(BASE_DIR, "data/6372.db"))
    cfg_path = os.path.join(BASE_DIR, "config/settings.json")
    config = json.load(open(cfg_path)) if os.path.exists(cfg_path) else {"assets": {}}
    
    last_w, last_h = 0, 0
    last_ref = 0
    cmd_buffer = ""
    
    while True:
        tsize = shutil.get_terminal_size()
        w, h = tsize.columns, tsize.lines
        if h < 38:
            utils.clear_terminal(); print(f"\n\n{RED}⚠️  TERMINAL TERLALU KECIL ({h}){RESET}"); time.sleep(2); last_w = 0; continue
        if w != last_w or h != last_h:
            print_static_ui(w, config); last_w, last_h = w, h; last_ref = 0

        now = time.time()
        if now - last_ref > 0.5:
            pid = utils.is_monitor_running()
            quota = db.get_quota()
            hbs = db.get_heartbeats()
            pnl_total = db.get_paper_trade_stats()
            
            # --- SCOPE ---
            sys.stdout.write("\033[13;1H\033[K")
            m_ok = f"{GREEN}⚡ ACTIVE{RESET}" if "MARKET" in hbs else f"{DIM}⚪ IDLE{RESET}"
            a_ok = f"{GREEN}✨ READY{RESET}" if "AI" in hbs else f"{DIM}⚪ IDLE{RESET}"
            time_now = datetime.now().strftime("%H:%M:%S")
            sys.stdout.write(utils.center_line(f"STATUS: {'🟢 AKTIF' if pid else '🔴 NONAKTIF'} | PID: {pid if pid else '---'} | 🕒 {time_now} | 📡 MARKET: {m_ok} | 🧠 AI: {a_ok}", w) + "\n")
            sys.stdout.write("\033[14;1H\033[K")
            uptime = datetime.now() - START_TIME
            uptime_str = str(uptime).split('.')[0] # Remove microseconds
            sys.stdout.write(utils.center_line(f"{DIM}UPTIME: {uptime_str} | DB: 📁 6372.db | LOGS: 📁 activity.log{RESET}", w) + "\n")
            
            # --- MARKET RADAR (ABSOLUTE POSITIONING) ---
            sys.stdout.write("\033[20;1H")
            assets = config.get("assets", {})
            start_x = max(0, (w - 85) // 2) # X coordinate for centering the 85-char block
            
            for i, (a, d) in enumerate(assets.items()):
                data = db.get_asset_state(a)
                row_theme = THEME if i % 2 == 0 else "\033[94m"
                history = db.get_asset_history(a, limit=10)
                spark = utils.generate_sparkline(history, width=10) if len(history) >= 2 else ".........."
                
                emoji = d.get('emoji','💰')
                price = f"$ {data.get('price', 0):,.8f}"
                c24 = data.get("change_24h", 0)
                c24_color = GREEN if c24 > 0 else (RED if c24 < 0 else DIM)
                
                meta = ""
                if data.get("onchain"):
                    oc = data["onchain"]
                    if "m5_activity" in oc:
                        m = oc["m5_activity"]; meta = f"🐳 B:{m.get('buys',0)}/S:{m.get('sells',0)}"
                    elif "gas_gwei" in oc: meta = f"⛽ {oc['gas_gwei']}g"
                
                st_val = data.get("tier")
                if st_val is None:
                    st_text = "STABIL"; st_color = DIM
                else:
                    st_text = f"{st_val:+.2f}%"
                    st_color = GREEN if st_val > 0 else (RED if st_val < 0 else YELLOW)
                
                # Logic Warna Sparkline (Sentiment Whale)
                spark_color = THEME
                if data.get("onchain"):
                    sent = data["onchain"].get("sentiment")
                    if sent == "whale_buy": spark_color = GREEN
                    elif sent == "whale_sell": spark_color = RED
                
                if len(history) < 2: spark_color = DIM

                # Trik Final: Paku posisi setiap kolom secara absolut
                # start_x adalah titik mulai emoji
                # start_x + 4  : Nama Aset
                # start_x + 48 : Metadata Area
                # start_x + 68 : Tier Status Area
                # start_x + 82 : Trend (Sparkline) Area
                
                line_prefix = f"\033[{20+i};{start_x}H\033[K{emoji}"
                line_name   = f"\033[{20+i};{start_x+4}H{row_theme}{BOLD}{a:<8}{RESET} | {BOLD}{price:<18}{RESET} | {c24_color}{c24:>+7.2f}%{RESET} |"
                line_meta   = f"\033[{20+i};{start_x+48}H{DIM}{meta:<18}{RESET} |"
                line_tier   = f"\033[{20+i};{start_x+68}H{st_color}[{st_text:^10}]{RESET} |"
                line_trend  = f"\033[{20+i};{start_x+82}H{spark_color}{spark}{RESET}"
                
                sys.stdout.write(line_prefix + line_name + line_meta + line_tier + line_trend + "\n")
            
            # --- AI REGISTRY ---
            sys.stdout.write("\033[35;1H\033[K")
            sys.stdout.write(utils.center_line(f"BRAINS: {GREEN}🌐 Gemini 3.1 Flash{RESET} | {YELLOW}🤖 Ollama TinyLlama{RESET}", w) + "\n")
            sys.stdout.write("\033[36;1H\033[K")
            sys.stdout.write(utils.center_line(f"QUOTA : {get_quota_bar(quota)}", w) + "\n")
            sys.stdout.write("\033[37;1H\033[K")
            pnl_color = YELLOW if round(pnl_total, 2) == 0 else (GREEN if pnl_total > 0 else RED)
            sys.stdout.write(utils.center_line(f"{BOLD}SIMULATED PnL: {pnl_color}{pnl_total:+.2f}%{RESET}", w) + "\n")
            sys.stdout.write("\033[38;1H\033[K")
            sources = config.get('sources', {})
            inflow = f"{DIM}📡 INFLOW: {len(sources.get('x_accounts',[]))} X | {len(sources.get('youtube',[]))} YT | {len(sources.get('rss_feeds',[]))} RSS{RESET}"
            sys.stdout.write(utils.center_line(inflow, w) + "\n")

            # --- COMMAND PROMPT ---
            sys.stdout.write("\033[41;1H\033[K" + f"   {BOLD}{THEME}❯{RESET} {BOLD}PERINTAH:{RESET} {cmd_buffer}")
            sys.stdout.flush()
            last_ref = now

        char = utils.get_key_universal()
        if char:
            if char in ["\r", "\n"]:
                cmd = cmd_buffer.strip().lower()
                cmd_buffer = ""
                if cmd in ["/q", "/exit"]: break
                if cmd in ["/i", "/intel"]: show_intel_inbox(db); print_static_ui(w, config); last_ref = 0
                if cmd in ["/c", "/config"]: os.system(f"python3 {os.path.join(BASE_DIR, 'src/ui/wizard.py')}"); print_static_ui(w, config); last_ref = 0
                if cmd in ["/r", "/restart"]: os.system(f"bash {os.path.join(BASE_DIR, 'stop.sh')} && bash {os.path.join(BASE_DIR, 'start.sh')}"); print_static_ui(w, config); last_ref = 0
            elif char in ["\x7f", "\x08"]: cmd_buffer = cmd_buffer[:-1]
            else: cmd_buffer += char
            sys.stdout.write("\033[41;1H\033[K" + f"   {BOLD}{THEME}❯{RESET} {BOLD}PERINTAH:{RESET} {cmd_buffer}"); sys.stdout.flush()
        time.sleep(0.02)

if __name__ == "__main__":
    fd = sys.stdin.fileno()
    old_settings = None
    if not utils.IS_WINDOWS:
        import tty, termios
        try:
            old_settings = termios.tcgetattr(fd); tty.setcbreak(fd)
        except: pass
    try:
        sys.stdout.write("\033[?25l"); main_dashboard()
    except KeyboardInterrupt: pass
    finally:
        if old_settings: termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        sys.stdout.write("\033[?25h"); utils.clear_terminal()
