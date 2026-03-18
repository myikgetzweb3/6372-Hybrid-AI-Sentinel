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

# THEME CONSTANTS
THEME, GREEN, YELLOW, RED, BOLD, RESET, DIM = "\033[96m", "\033[92m", "\033[93m", "\033[91m", "\033[1m", "\033[0m", "\033[2m"

def load_config():
    path = os.path.join(BASE_DIR, "config/settings.json")
    if os.path.exists(path):
        with open(path, "r") as f: return json.load(f)
    return {"assets": {}, "sources": {}, "ai_prompts": {}, "user_strategy": {}}

def save_config(config):
    path = os.path.join(BASE_DIR, "config/settings.json")
    with open(path, "w") as f: json.dump(config, f, indent=2)

def print_header(title="KONFIGURASI"):
    utils.clear_terminal()
    term_w = utils.get_terminal_width()
    # Header Logo (Standardized)
    for line in utils.get_logo():
        print(utils.center_line(f"{THEME}{BOLD}{line}{RESET}", term_w))
    
    print(utils.center_line(f"{THEME}{BOLD}HYBRID AI SENTINEL v2.0{RESET}", term_w))
    print(utils.center_line(f"{DIM}Developed by myikgetzweb3{RESET}", term_w) + "\n")
    
    box_w = 55
    sep = f"{THEME}{'━' * ((box_w - (len(title)+2)) // 2)} {BOLD}{title}{RESET}{THEME} {'━' * ((box_w - (len(title)+2)) // 2)}{RESET}"
    print(utils.center_line(sep, term_w) + "\n")

def manage_language():
    print_header("PENGATURAN BAHASA")
    print(f"   {THEME}[1]{RESET} Bahasa Indonesia (id)")
    print(f"   {THEME}[2]{RESET} English (en)")
    print(f"   {THEME}[3]{RESET} Kembali")
    c = input(f"\n   {THEME}PILIH : {RESET}")
    env_path = os.path.join(BASE_DIR, ".env")
    if c == "1":
        os.system(f"sed -i '/APP_LANGUAGE=/d' {env_path} && echo 'APP_LANGUAGE=id' >> {env_path}")
        print(f"{GREEN}   ✔ Bahasa disetel ke Indonesia.{RESET}")
    elif c == "2":
        os.system(f"sed -i '/APP_LANGUAGE=/d' {env_path} && echo 'APP_LANGUAGE=en' >> {env_path}")
        print(f"{GREEN}   ✔ Language set to English.{RESET}")
    time.sleep(1)

def manage_ai_test():
    print_header("UJI KONEKSI AI")
    print(f"🤖 {BOLD}Ollama Tiny (Lokal)...{RESET}", end=" ", flush=True)
    res_o = utils.call_ollama("Test.")
    print(f"{GREEN}SIAGA{RESET}" if "Offline" not in res_o else f"{RED}OFFLINE{RESET}")
    
    print(f"🌍 {BOLD}Gemini CLI (Online)...{RESET}", end=" ", flush=True)
    res_g = utils.call_gemini("Test.")
    print(f"{GREEN}SIAGA{RESET}" if "Error" not in res_g else f"{RED}OFFLINE{RESET}")
    input(f"\n{DIM}Tekan Enter untuk kembali...{RESET}")

def main_menu():
    while True:
        config = load_config()
        print_header("PUSAT KENDALI PENGGUNA")
        print(f"   {THEME}[1]{RESET} Koin & Harga (% Perubahan)")
        print(f"   {THEME}[2]{RESET} Gaya Investasi & Strategi")
        print(f"   {THEME}[3]{RESET} Sumber Data (X/YT/RSS)")
        print(f"   {THEME}[4]{RESET} Bahasa Antarmuka (ID/EN)")
        print(f"   {THEME}[5]{RESET} Uji & Prioritas AI Agents")
        print(f"   {THEME}[6]{RESET} Keluar")
        
        # Footer Quick Nav
        term_w = utils.get_terminal_width()
        print(f"\n{THEME}{DIM}{'━' * term_w}{RESET}")
        print(f"{BOLD}💡 NAVIGASI:{RESET} {THEME}crypto-status{RESET} | {THEME}crypto-config{RESET} | {THEME}crypto-monitor{RESET}")
        
        choice = input(f"\n   {THEME}PILIH OPSI : {RESET}")
        
        if choice == "1":
            asset = input(f"\n   Simbol Aset (misal: BTC): ").upper()
            if asset in config["assets"]:
                print(f"   {GREEN}✔ Aset ditemukan. Mengalihkan ke menu detail...{RESET}"); time.sleep(1)
            else:
                print(f"   {RED}✘ Aset belum terdaftar.{RESET}"); time.sleep(1)
        elif choice == "2":
            print_header("STRATEGI INVESTASI")
            print(f"   Tipe Saat Ini: {YELLOW}{config.get('user_strategy', {}).get('type', 'DCA')}{RESET}")
            new_type = input("   Ubah Tipe (DCA/Scalp/Hold): ").upper()
            if new_type: config.setdefault("user_strategy", {})["type"] = new_type; save_config(config)
            print(f"{GREEN}   ✔ Strategi diperbarui.{RESET}"); time.sleep(1)
        elif choice == "3":
            print_header("SUMBER DATA MASUK")
            print(f"   Jumlah RSS: {len(config.get('sources', {}).get('rss_feeds', []))}")
            print(f"   Jumlah X  : {len(config.get('sources', {}).get('x_accounts', []))}")
            input(f"\n   {DIM}Gunakan editor untuk menambah sumber (Fitur segera hadir). Enter...{RESET}")
        elif choice == "4":
            manage_language()
        elif choice == "5":
            manage_ai_test()
        elif choice == "6":
            break

if __name__ == "__main__":
    try: main_menu()
    except KeyboardInterrupt: print(f"\n{DIM}Keluar...{RESET}"); sys.exit(0)
