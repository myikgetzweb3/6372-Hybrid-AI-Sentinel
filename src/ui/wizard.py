import json
import os
import sys
import time
import shutil

# Path Bootstrapping
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
sys.path.append(os.path.join(BASE_DIR, "src"))

import utils

# --- 🎨 THEME & STYLES ---
THEME, GREEN, YELLOW, RED, BOLD, RESET, DIM = "\033[96m", "\033[92m", "\033[93m", "\033[91m", "\033[1m", "\033[0m", "\033[2m"

def print_header(title_key):
    utils.clear_terminal()
    w = utils.get_terminal_width()
    for line in utils.get_logo(): print(utils.center_line(f"{THEME}{BOLD}{line}{RESET}", w))
    print(utils.center_line(f"{THEME}{BOLD}{utils.get_text('wiz_title')}{RESET}", w))
    print(utils.center_line(f"{DIM}{utils.get_brand_credit()}{RESET}", w) + "\n")
    
    border = "━" * 60
    print(utils.center_line(f"{THEME}{border}{RESET}", w))
    print(utils.center_line(f"{THEME}{BOLD}📡 {utils.get_text(title_key)} 📡{RESET}", w))
    print(utils.center_line(f"{THEME}{border}{RESET}", w) + "\n")

def load_config():
    cfg_path = os.path.join(BASE_DIR, "config/settings.json")
    with open(cfg_path, 'r') as f: return json.load(f)

def save_config(config):
    cfg_path = os.path.join(BASE_DIR, "config/settings.json")
    with open(cfg_path, 'w') as f: json.dump(config, f, indent=2)

def manage_assets():
    while True:
        config = load_config()
        print_header("wiz_asset_mgmt")
        assets = config.get("assets", {})
        
        print(f"   {BOLD}{utils.get_text('market_radar')}:{RESET}")
        for a in assets:
            print(f"   • {THEME}{a:<8}{RESET} ({assets[a].get('symbol')})")
        
        print(f"\n   {THEME}[1]{RESET} {utils.get_text('wiz_add_asset')}")
        print(f"   {THEME}[2]{RESET} {utils.get_text('wiz_del_asset')}")
        print(f"   {THEME}[3]{RESET} {utils.get_text('wiz_back')}")
        
        c = input(f"\n   {THEME}{utils.get_text('wiz_select')} : {RESET}")
        if c == "1":
            name = input(f"   {utils.get_text('status_label')} (BTC/SOL): ").upper()
            if not name: continue
            print(f"   {YELLOW}🔍 {utils.get_text('wiz_analyzing')} '{name}'...{RESET}")
            info = utils.discovery_ai_asset_info(name)
            network, handle = info.get("network", "unknown"), info.get("handle", "")
            print(f"   {GREEN}✔ OK:{RESET} Net: {network.upper()} | X: @{handle}")
            
            sym = input(f"   Symbol (Binance): ").upper()
            addr = input(f"   Address (DEX): ") if not sym or network != "bitcoin" else ""

            asset_cfg = {
                "symbol": sym if sym else name, "emoji": "💰", "priority": False,
                "keywords": [name.lower(), network.lower()], "onchain": {"network": network},
                "thresholds": {"hourly": 1.0, "dips": [], "spikes": []}
            }
            if addr:
                asset_cfg["dex"] = {"network": network, "address": addr}
                asset_cfg["onchain"]["address"] = addr
            
            config["assets"][name] = asset_cfg
            if handle:
                if not any(x.get("handle") == handle for x in config["sources"]["x_accounts"]):
                    config["sources"]["x_accounts"].append({"name": f"{name} Official", "handle": handle, "priority": True})
            save_config(config); print(f"{GREEN}   ✔ {utils.get_text('wiz_done')}.{RESET}"); time.sleep(1)
        elif c == "2":
            name = input(f"   {utils.get_text('wiz_del_asset')}: ").upper()
            if name in config["assets"]:
                del config["assets"][name]; save_config(config); print(f"{GREEN}   ✔ OK.{RESET}"); time.sleep(1)
        elif c == "3": break

def manage_sources():
    while True:
        config = load_config()
        print_header("wiz_sources")
        sources = config.get("sources", {})
        print(f"   {BOLD}{utils.get_text('data_inflow')}:{RESET}")
        print(f"   • X Accounts : {THEME}{len(sources.get('x_accounts', []))}{RESET}")
        print(f"   • YouTube    : {THEME}{len(sources.get('youtube', []))}{RESET}")
        
        print(f"\n   {THEME}[1]{RESET} Add X (Twitter)")
        print(f"   {THEME}[2]{RESET} Add YouTube")
        print(f"   {THEME}[3]{RESET} Reset All")
        print(f"   {THEME}[4]{RESET} {utils.get_text('wiz_back')}")
        
        c = input(f"\n   {THEME}{utils.get_text('wiz_select')} : {RESET}")
        if c == "1":
            handle = input("   Handle X: ")
            if handle:
                config.setdefault("sources", {}).setdefault("x_accounts", []).append({"name": handle, "handle": handle, "priority": True})
                save_config(config); print(f"{GREEN}   ✔ OK.{RESET}"); time.sleep(1)
        elif c == "2":
            cid = input("   YouTube CID: ")
            if cid:
                config.setdefault("sources", {}).setdefault("youtube", []).append({"name": "New", "channel_id": cid, "priority": True})
                save_config(config); print(f"{GREEN}   ✔ OK.{RESET}"); time.sleep(1)
        elif c == "3":
            config["sources"] = {"x_accounts": [], "youtube": [], "rss_feeds": [], "nitter_instances": ["https://nitter.net"]}
            save_config(config); print(f"{YELLOW}   ✔ OK.{RESET}"); time.sleep(1)
        elif c == "4": break

def manage_language():
    while True:
        config = load_config()
        print_header("wiz_lang")
        curr = config.get('app_language', 'id').upper()
        print(f"   {utils.get_text('status_label')}: {YELLOW}{BOLD}{curr}{RESET}")
        print(f"\n   {THEME}[1]{RESET} Bahasa Indonesia (ID)")
        print(f"   {THEME}[2]{RESET} English (EN)")
        print(f"   {THEME}[3]{RESET} {utils.get_text('wiz_back')}")
        c = input(f"\n   {THEME}{utils.get_text('wiz_select')} : {RESET}")
        if c == "1": config["app_language"] = "id"; save_config(config); time.sleep(0.5)
        elif c == "2": config["app_language"] = "en"; save_config(config); time.sleep(0.5)
        elif c == "3": break

def manage_ai_test():
    print_header("wiz_ai_test")
    print(f"   📡 {BOLD}Ollama (Local)...{RESET}", end=" ", flush=True)
    res_o = utils.call_ollama("Say OK")
    print(f"{GREEN}ONLINE{RESET}" if "AI" not in res_o else f"{RED}OFFLINE{RESET}")
    print(f"   🌍 {BOLD}Gemini Pro (Online)...{RESET}", end=" ", flush=True)
    res_g = utils.call_gemini("Say OK")
    print(f"{GREEN}ONLINE{RESET}" if "Error" not in res_g else f"{RED}OFFLINE{RESET}")
    input(f"\n   {DIM}{utils.get_text('wiz_back')} (Enter)...{RESET}")

def manage_advanced():
    print_header("wiz_advanced")
    env_path = os.path.join(BASE_DIR, ".env")
    current_quota = utils.get_env("GEMINI_QUOTA_LIMIT", "1500")
    print(f"   {THEME}[1]{RESET} {utils.get_text('gemini_limit')} ({current_quota}/day)")
    print(f"   {THEME}[2]{RESET} {utils.get_text('wiz_back')}")
    c = input(f"\n   {THEME}{utils.get_text('wiz_select')} : {RESET}")
    if c == "1":
        val = input("   Limit: ")
        if val.isdigit():
            os.system(f"sed -i '/GEMINI_QUOTA_LIMIT=/d' {env_path} && echo 'GEMINI_QUOTA_LIMIT={val}' >> {env_path}")
            print(f"{GREEN}   ✔ OK.{RESET}"); time.sleep(1)
    elif c == "2": return

def main_menu():
    while True:
        config = load_config()
        print_header("wiz_main_menu")
        print(f"   {THEME}[1]{RESET} {BOLD}{utils.get_text('wiz_asset_mgmt')}{RESET}")
        print(f"   {THEME}[2]{RESET} {BOLD}{utils.get_text('wiz_strategy')}{RESET}")
        print(f"   {THEME}[3]{RESET} {BOLD}{utils.get_text('wiz_sources')}{RESET}")
        print(f"   {THEME}[4]{RESET} {BOLD}{utils.get_text('wiz_lang')}{RESET}")
        print(f"   {THEME}[5]{RESET} {BOLD}{utils.get_text('wiz_ai_test')}{RESET}")
        print(f"   {THEME}[6]{RESET} {BOLD}{utils.get_text('wiz_advanced')}{RESET}")
        print(f"   {THEME}[7]{RESET} {BOLD}{utils.get_text('wiz_exit')}{RESET}")
        
        choice = input(f"\n   {THEME}{utils.get_text('wiz_select')} : {RESET}")
        if choice == "1": manage_assets()
        elif choice == "2":
            print_header("wiz_strategy")
            print(f"   Type: {YELLOW}{config.get('user_strategy', {}).get('type', 'DCA')}{RESET}")
            new_type = input("   New Type (DCA/Scalp/Hold): ").upper()
            if new_type: config.setdefault("user_strategy", {})["type"] = new_type; save_config(config)
            print(f"{GREEN}   ✔ OK.{RESET}"); time.sleep(1)
        elif choice == "3": manage_sources()
        elif choice == "4": manage_language()
        elif choice == "5": manage_ai_test()
        elif choice == "6": manage_advanced()
        elif choice == "7": break

if __name__ == "__main__":
    try: main_menu()
    except KeyboardInterrupt: sys.exit(0)
