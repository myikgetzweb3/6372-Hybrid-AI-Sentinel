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

def show_log_monitor():
    """Halaman Monitor Log Real-time Tanpa Kedip & Hemat RAM"""
    log_path = os.path.join(BASE_DIR, "activity.log")
    utils.clear_terminal() 
    while True:
        w = utils.get_terminal_width()
        sys.stdout.write("\033[H")
        
        buffer = ""
        for line in utils.get_logo(): buffer += utils.center_line(f"{THEME}{BOLD}{line}{RESET}", w) + "\n"
        buffer += utils.center_line(f"{THEME}{BOLD}🖥️  {utils.get_text('market_radar')}{RESET}", w) + "\n"
        border = "━" * min(w-4, 85)
        buffer += utils.center_line(f"{THEME}{border}{RESET}", w) + "\n"
        
        if os.path.exists(log_path):
            try:
                with open(log_path, 'rb') as f:
                    f.seek(0, os.SEEK_END)
                    f_size = f.tell()
                    offset = min(f_size, 4096)
                    f.seek(f_size - offset)
                    chunk = f.read().decode('utf-8', errors='ignore')
                    lines = chunk.splitlines()[-25:]
                    if not lines:
                        buffer += "\n" * 5 + utils.center_line(f"{DIM}Waiting for engine...{RESET}", w) + "\n"
                    else:
                        for l in lines: buffer += "\033[K" + utils.center_line(f"{DIM}{l.strip()}{RESET}", w + 20) + "\n"
            except: pass
        
        buffer += "\n" + utils.center_line(f"{THEME}{border}{RESET}", w) + "\n"
        buffer += utils.center_line(f"{BOLD}💡 [q] Back{RESET}", w) + "\n"
        sys.stdout.write(buffer); sys.stdout.flush()
        char = utils.get_key_universal()
        if char and char.lower() == 'q': break
        time.sleep(2)

def show_intel_inbox(db):
    import textwrap
    needs_redraw = True
    while True:
        if needs_redraw:
            utils.clear_terminal()
            tsize = shutil.get_terminal_size()
            w, h = tsize.columns, tsize.lines
            if h < 38: break
            
            for line in utils.get_logo(): print(utils.center_line(f"{THEME}{BOLD}{line}{RESET}", w))
            print(utils.center_line(f"{THEME}{BOLD}📥 TACTICAL INTEL INBOX{RESET}", w))
            
            border = "━" * min(w-4, 75)
            print(utils.center_line(f"{THEME}{border}{RESET}", w))
            uptime_str = str(datetime.now() - START_TIME).split('.')[0]
            sys.stdout.write(utils.center_line(f"{DIM}{utils.get_text('uptime')}: {uptime_str} | {utils.get_text('database')}: 📁 6372.db{RESET}", w) + "\n")
            print(utils.center_line(f"{THEME}{border}{RESET}", w) + "\n")
            
            archive = db.get_all_intel()
            if not archive: print("\n" * 2 + utils.center_line(f"{DIM}(Inbox Empty){RESET}", w))
            else:
                for r in archive[:10]:
                    time_tag = f"{DIM}[{r['time_str']}]{RESET}"
                    source_tag = f"{YELLOW}{BOLD}{r['source']:<10}{RESET}"
                    print(utils.center_line(f"{time_tag} {source_tag} ID: {r['id']}", w))
                    
                    title_wrapped = textwrap.wrap(f"{BOLD}NEWS:{RESET} {r['title']}", width=min(w-10, 85))
                    for tw in title_wrapped: print(utils.center_line(tw, w))
                    
                    msg_body = r['message'].replace("VERIFIKASI INTEL:", f"{GREEN}{BOLD}{utils.get_text('online_ai')}:{RESET}")
                    msg_wrapped = textwrap.wrap(f"{BOLD}AI ANALYSIS:{RESET} {msg_body}", width=min(w-10, 85))
                    for mw in msg_wrapped: print(utils.center_line(mw, w))
                    print(utils.center_line(f"{DIM}{'─' * 60}{RESET}", w) + "\n")
            
            print(utils.center_line(f"{THEME}{border}{RESET}", w))
            print(utils.center_line(f"{BOLD}💡 [ID] Detail | q Back | r Refresh{RESET}", w))
            sys.stdout.write(utils.center_line(f"{YELLOW}⌨️  {utils.get_text('command_label')} : {RESET}", w-10))
            sys.stdout.flush()
            needs_redraw = False
        
        char = utils.get_key_universal()
        if not char: time.sleep(0.1); continue
        if char.lower() == 'q': break
        if char.lower() == 'r': needs_redraw = True; continue
        if char.isdigit():
            sys.stdout.write(char); sys.stdout.flush()
            choice = char + sys.stdin.readline().strip()
            report = next((r for r in archive if str(r['id']) == choice), None)
            if report:
                utils.clear_terminal()
                print("\n" * 2)
                for line in utils.get_logo(): print(utils.center_line(f"{THEME}{BOLD}{line}{RESET}", w))
                print(utils.center_line(f"{THEME}{BOLD}📜 {utils.get_text('online_ai')} DOCUMENT - #{choice}{RESET}", w))
                print(utils.center_line(f"{THEME}{border}{RESET}", w) + "\n")
                full_content = f"ORIGINAL NEWS:\n{report['title']}\n\nSTRATEGIC ANALYSIS:\n{report['message']}"
                wrapped = textwrap.wrap(full_content, width=min(w-10, 85), replace_whitespace=False)
                for wl in wrapped: print(utils.center_line(wl, w))
                print("\n" + utils.center_line(f"{THEME}{border}{RESET}", w))
                print(utils.center_line(f"{YELLOW}Press Enter to go back...{RESET}", w))
                sys.stdin.readline(); needs_redraw = True

def print_static_ui(w, config):
    utils.clear_terminal()
    for line in utils.get_logo(): print(utils.center_line(f"{THEME}{BOLD}{line}{RESET}", w))
    print(utils.center_line(f"{THEME}{BOLD}6372 HYBRID AI SENTINEL v2.3{RESET}", w))
    print(utils.center_line(f"{DIM}{utils.get_brand_credit()}{RESET}", w) + "\n")
    
    border = "━" * min(w-4, 85)
    print(utils.center_line(f"{THEME}{border}{RESET}", w))
    scope_title = f" {utils.get_text('system_status').upper()} SCOPE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print(utils.center_line(f"{THEME}━{scope_title[:len(border)-2]}━{RESET}", w))
    print("\n" * 2) 
    print(utils.center_line(f"{THEME}{border}{RESET}", w) + "\n")
    
    print(utils.center_line(f"{THEME}{BOLD}{utils.get_text('market_radar')}{RESET}", w) + "\n")
    header = f"  {'ASSET':<12} | {'PRICE':<18} | {'24H %':<14} | {'METADATA':<18} | {'TIER STATUS'}"
    print(utils.center_line(f"{BOLD}{header}{RESET}", w))
    print(utils.center_line(f"{DIM}{'─' * 85}{RESET}", w))
    print("\n" * 12) 
    
    print(utils.center_line(f"{THEME}{border}{RESET}", w))
    print(utils.center_line(f"{THEME}━ {utils.get_text('ai_registry')} ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}"[:len(border)], w))
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
            utils.clear_terminal(); print(f"\n\n{RED}⚠️  TERMINAL TOO SMALL ({h}){RESET}"); time.sleep(2); last_w = 0; continue
        if w != last_w or h != last_h:
            print_static_ui(w, config); last_w, last_h = w, h; last_ref = 0

        now = time.time()
        if now - last_ref > 0.5:
            # Re-load config dynamic for language
            if os.path.exists(cfg_path):
                try:
                    with open(cfg_path, 'r') as f: config = json.load(f)
                except: pass

            pid = utils.is_monitor_running()
            quota = db.get_quota()
            hbs = db.get_heartbeats()
            pnl_total = db.get_paper_trade_stats()
            
            buffer = ""
            m_ok = f"{GREEN}⚡ {utils.get_text('active')}{RESET}" if "MARKET" in hbs else f"{DIM}⚪ {utils.get_text('idle')}{RESET}"
            a_ok = f"{GREEN}✨ {utils.get_text('ready')}{RESET}" if "AI" in hbs else f"{DIM}⚪ {utils.get_text('idle')}{RESET}"
            time_now = datetime.now().strftime("%H:%M:%S")
            
            # --- Update Scope ---
            st_line = f"{utils.get_text('status_label')}: {'🟢 ' + utils.get_text('active') if pid else '🔴 ' + utils.get_text('inactive')} | PID: {pid if pid else '---'} | 🕒 {time_now} | 📡 MARKET: {m_ok} | 🧠 AI: {a_ok}"
            buffer += f"\033[13;1H\033[K" + utils.center_line(st_line, w) + "\n"
            
            uptime_str = str(datetime.now() - START_TIME).split('.')[0]
            up_line = f"{DIM}{utils.get_text('uptime')}: {uptime_str} | {utils.get_text('database')}: 📁 6372.db | {utils.get_text('logs')}: 📁 activity.log{RESET}"
            buffer += f"\033[14;1H\033[K" + utils.center_line(up_line, w) + "\n"
            
            # --- Update Market ---
            assets = config.get("assets", {})
            start_x = max(0, (w - 85) // 2)
            for i, (a, d) in enumerate(assets.items()):
                data = db.get_asset_state(a)
                row_theme = THEME if i % 2 == 0 else "\033[94m"
                history = db.get_asset_history(a, limit=10)
                spark = utils.generate_sparkline(history, width=10) if len(history) >= 2 else ".........."
                
                f_name = f"{a:<8}"
                price_str = f"$ {data.get('price', 0):,.8f}"
                c24 = data.get("change_24h", 0)
                c24_color = GREEN if c24 > 0 else (RED if c24 < 0 else DIM)
                
                meta = ""
                if data.get("onchain"):
                    oc = data["onchain"]
                    if "m5_activity" in oc:
                        m = oc["m5_activity"]; meta = f"🐳 B:{m.get('buys',0)}/S:{m.get('sells',0)}"
                    elif "gas_gwei" in oc: meta = f"⛽ {oc['gas_gwei']}g"
                
                st_val = data.get("tier")
                if st_val is None: st_text = utils.get_text('stable'); st_color = DIM
                else:
                    st_text = f"{st_val:+.2f}%"; st_color = GREEN if st_val > 0 else (RED if st_val < 0 else YELLOW)
                
                spark_color = THEME
                if data.get("onchain") and "sentiment" in data["onchain"]:
                    sent = data["onchain"]["sentiment"]
                    if sent == "whale_buy": spark_color = GREEN
                    elif sent == "whale_sell": spark_color = RED
                if len(history) < 2: spark_color = DIM

                row_y = 20 + i
                buffer += f"\033[{row_y};{start_x}H\033[K{d.get('emoji','💰')}"
                buffer += f"\033[{row_y};{start_x+4}H{row_theme}{BOLD}{f_name}{RESET} | {BOLD}{price_str:<18}{RESET} | {c24_color}{c24:>+7.2f}%{RESET} |"
                buffer += f"\033[{row_y};{start_x+48}H{DIM}{meta:<18}{RESET} |"
                buffer += f"\033[{row_y};{start_x+68}H{st_color}[{st_text:^10}]{RESET} |"
                buffer += f"\033[{row_y};{start_x+82}H{spark_color}{spark}{RESET}\n"

            # --- Update AI ---
            buffer += f"\033[35;1H\033[K" + utils.center_line(f"{utils.get_text('brains')}: {GREEN}🌐 Gemini 3.1 Flash{RESET} | {YELLOW}🤖 Ollama TinyLlama{RESET}", w) + "\n"
            buffer += f"\033[36;1H\033[K" + utils.center_line(f"{utils.get_text('quota')} : {get_quota_bar(quota)}", w) + "\n"
            pnl_color = YELLOW if round(pnl_total, 2) == 0 else (GREEN if pnl_total > 0 else RED)
            buffer += f"\033[37;1H\033[K" + utils.center_line(f"{BOLD}{utils.get_text('pnl_summary')}: {pnl_color}{pnl_total:+.2f}%{RESET}", w) + "\n"
            sources = config.get('sources', {})
            inflow = f"{DIM}📡 {utils.get_text('data_inflow')}: {len(sources.get('x_accounts',[]))} X | {len(sources.get('youtube',[]))} YT | {len(sources.get('rss_feeds',[]))} RSS{RESET}"
            buffer += f"\033[38;1H\033[K" + utils.center_line(inflow, w) + "\n"
            buffer += f"\033[41;1H\033[K" + f"   {BOLD}{THEME}❯{RESET} {BOLD}{utils.get_text('command_label')}:{RESET} {cmd_buffer}"
            
            sys.stdout.write(buffer); sys.stdout.flush()
            last_ref = now

        char = utils.get_key_universal()
        if char:
            if char in ["\r", "\n"]:
                cmd = cmd_buffer.strip().lower()
                cmd_buffer = ""
                if cmd in ["/q", "/exit"]: break
                if cmd in ["/i", "/intel"]: show_intel_inbox(db); print_static_ui(w, config); last_ref = 0
                if cmd in ["/m", "/monitor"]: show_log_monitor(); print_static_ui(w, config); last_ref = 0
                if cmd in ["/c", "/config"]: os.system(f"python3 {os.path.join(BASE_DIR, 'src/ui/wizard.py')}"); print_static_ui(w, config); last_ref = 0
                if cmd in ["/r", "/restart"]: os.system(f"bash {os.path.join(BASE_DIR, 'stop.sh')} && bash {os.path.join(BASE_DIR, 'start.sh')}"); print_static_ui(w, config); last_ref = 0
            elif char in ["\x7f", "\x08"]: cmd_buffer = cmd_buffer[:-1]
            else: cmd_buffer += char
            sys.stdout.write(f"\033[41;1H\033[K   {BOLD}{THEME}❯{RESET} {BOLD}{utils.get_text('command_label')}:{RESET} {cmd_buffer}"); sys.stdout.flush()
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
