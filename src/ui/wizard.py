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

def print_header(title):
    utils.clear_terminal()
    w = utils.get_terminal_width()
    for line in utils.get_logo(): print(utils.center_line(f"{THEME}{BOLD}{line}{RESET}", w))
    print(utils.center_line(f"{THEME}{BOLD}6372 SENTINEL - CONFIGURATION WIZARD{RESET}", w))
    print(utils.center_line(f"{DIM}{utils.get_brand_credit()}{RESET}", w) + "\n")
    
    border = "━" * 60
    print(utils.center_line(f"{THEME}{border}{RESET}", w))
    print(utils.center_line(f"{THEME}{BOLD}📡 {title} 📡{RESET}", w))
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
        print_header("MANAJEMEN ASET")
        assets = config.get("assets", {})
        
        print(f"   {BOLD}Daftar Aset Aktif:{RESET}")
        for a in assets:
            print(f"   • {THEME}{a:<8}{RESET} ({assets[a].get('symbol')})")
        
        print(f"\n   {THEME}[1]{RESET} Tambah Aset Baru")
        print(f"   {THEME}[2]{RESET} Hapus Aset")
        print(f"   {THEME}[3]{RESET} Kembali")
        
        c = input(f"\n   {THEME}PILIH OPSI : {RESET}")
        if c == "1":
            name = input(f"   Nama Aset (misal: BTC): ").upper()
            if not name: continue
            
            print(f"   {YELLOW}🔍 Sentinel AI sedang menganalisis aset '{name}'...{RESET}")
            info = utils.discovery_ai_asset_info(name)
            network = info.get("network", "unknown")
            handle = info.get("handle", "")
            
            print(f"   {GREEN}✔ Analisis Selesai:{RESET} Jaringan: {network.upper()} | X: @{handle if handle else 'N/A'}")
            
            sym = input(f"   Symbol Binance (Kosongkan jika hanya koin DEX): ").upper()
            addr = ""
            if not sym or network != "bitcoin":
                addr = input(f"   Alamat Kontrak (Address): ")

            # Build Smart Config
            asset_cfg = {
                "symbol": sym if sym else name,
                "emoji": "💰",
                "priority": False,
                "keywords": [name.lower(), network.lower()],
                "onchain": {"network": network},
                "thresholds": {"hourly": 1.0, "dips": [], "spikes": []}
            }
            if addr:
                asset_cfg["dex"] = {"network": network, "address": addr}
                asset_cfg["onchain"]["address"] = addr
            
            config["assets"][name] = asset_cfg
            
            # Smart Auto-Source: Add Twitter if found
            if handle:
                exists = any(x.get("handle") == handle for x in config["sources"]["x_accounts"])
                if not exists:
                    config["sources"]["x_accounts"].append({"name": f"{name} Official", "handle": handle, "priority": True})
                    print(f"   {GREEN}✔ Akun X @{handle} otomatis ditambahkan ke pemantauan.{RESET}")

            save_config(config)
            print(f"{GREEN}   ✔ Aset '{name}' berhasil dikonfigurasi secara cerdas.{RESET}")
        elif c == "2":
            name = input("   Nama Aset yang akan dihapus: ").upper()
            if name in config["assets"]:
                # 1. Identifikasi handle X koin ini (jika ada)
                asset_handle = ""
                # Kami mencari handle yang namanya mirip 'Koin Official'
                for x in config["sources"]["x_accounts"]:
                    if x.get("name") == f"{name} Official":
                        asset_handle = x.get("handle")
                        break
                
                # 2. Hapus Aset
                del config["assets"][name]
                
                # 3. Smart Cleanup: Hapus X handle jika tidak digunakan koin lain
                if asset_handle:
                    # Cek koin lain yang mungkin menggunakan handle yang sama (jarang tapi mungkin)
                    still_needed = any(asset_handle in str(cfg) for a, cfg in config["assets"].items())
                    if not still_needed:
                        config["sources"]["x_accounts"] = [x for x in config["sources"]["x_accounts"] if x.get("handle") != asset_handle]
                        print(f"   {YELLOW}✔ Sumber data X @{asset_handle} juga dibersihkan.{RESET}")

                save_config(config)
                print(f"{GREEN}   ✔ Berhasil dihapus.{RESET}")
        elif c == "3": break
        time.sleep(1)

def manage_sources():
    while True:
        config = load_config()
        print_header("SUMBER DATA INTEL")
        sources = config.get("sources", {})
        print(f"   {BOLD}Status Pipa Data:{RESET}")
        print(f"   • Saluran X  : {THEME}{len(sources.get('x_accounts', []))}{RESET}")
        print(f"   • YouTube    : {THEME}{len(sources.get('youtube', []))}{RESET}")
        print(f"   • RSS Global : {THEME}{len(sources.get('rss_feeds', []))}{RESET}")
        
        print(f"\n   {THEME}[1]{RESET} Tambah Target X (Twitter)")
        print(f"   {THEME}[2]{RESET} Tambah Channel YouTube")
        print(f"   {THEME}[3]{RESET} Reset Semua Sumber")
        print(f"   {THEME}[4]{RESET} Kembali")
        
        c = input(f"\n   {THEME}PILIH OPSI : {RESET}")
        if c == "1":
            handle = input("   Handle X (tanpa @): ")
            if handle:
                config.setdefault("sources", {}).setdefault("x_accounts", []).append({"name": handle, "handle": handle, "priority": True})
                save_config(config); print(f"{GREEN}   ✔ Sumber X terdaftar.{RESET}")
        elif c == "2":
            cid = input("   Channel ID YouTube: ")
            if cid:
                config.setdefault("sources", {}).setdefault("youtube", []).append({"name": "New Channel", "channel_id": cid, "priority": True})
                save_config(config); print(f"{GREEN}   ✔ YouTube terdaftar.{RESET}")
        elif c == "3":
            config["sources"] = {"x_accounts": [], "youtube": [], "rss_feeds": [], "nitter_instances": ["https://nitter.net"]}
            save_config(config); print(f"{YELLOW}   ✔ Seluruh sumber dibersihkan.{RESET}")
        elif c == "4": break
        time.sleep(1)

def manage_language():
    while True:
        config = load_config()
        print_header("PENGATURAN BAHASA")
        curr = config.get('app_language', 'id').upper()
        print(f"   Bahasa Aktif: {YELLOW}{BOLD}{curr}{RESET}")
        print(f"\n   {THEME}[1]{RESET} Bahasa Indonesia (ID)")
        print(f"   {THEME}[2]{RESET} English (EN)")
        print(f"   {THEME}[3]{RESET} Kembali")
        
        c = input(f"\n   {THEME}PILIH : {RESET}")
        if c == "1":
            config["app_language"] = "id"
            save_config(config)
            print(f"{GREEN}   ✔ Bahasa berhasil diubah ke Indonesia.{RESET}")
            time.sleep(1)
        elif c == "2":
            config["app_language"] = "en"
            save_config(config)
            print(f"{GREEN}   ✔ Language successfully changed to English.{RESET}")
            time.sleep(1)
        elif c == "3": break

def manage_ai_test():
    print_header("UJI KONEKTIVITAS AI")
    print(f"   📡 {BOLD}Ollama (Local)...{RESET}", end=" ", flush=True)
    res_o = utils.call_ollama("Say OK")
    print(f"{GREEN}ONLINE{RESET}" if "AI" not in res_o else f"{RED}OFFLINE{RESET}")
    
    print(f"   🌍 {BOLD}Gemini Pro (Online)...{RESET}", end=" ", flush=True)
    res_g = utils.call_gemini("Say OK")
    print(f"{GREEN}ONLINE{RESET}" if "Error" not in res_g else f"{RED}OFFLINE{RESET}")
    input(f"\n   {DIM}Tekan Enter untuk kembali...{RESET}")

def manage_advanced():
    print_header("PENGATURAN LANJUT")
    env_path = os.path.join(BASE_DIR, ".env")
    current_quota = utils.get_env("GEMINI_QUOTA_LIMIT", "1500")
    current_log = utils.get_env("LOG_BACKUP_COUNT", "3")
    
    print(f"   {THEME}[1]{RESET} Batas Kuota Gemini ({current_quota}/hari)")
    print(f"   {THEME}[2]{RESET} Jumlah Cadangan Log ({current_log} file)")
    print(f"   {THEME}[3]{RESET} Kembali")
    
    c = input(f"\n   {THEME}PILIH : {RESET}")
    if c == "1":
        val = input("   Batas Baru (Angka): ")
        if val.isdigit():
            os.system(f"sed -i '/GEMINI_QUOTA_LIMIT=/d' {env_path} && echo 'GEMINI_QUOTA_LIMIT={val}' >> {env_path}")
            print(f"{GREEN}   ✔ Kuota diperbarui.{RESET}")
    elif c == "2":
        val = input("   Jumlah Cadangan: ")
        if val.isdigit():
            os.system(f"sed -i '/LOG_BACKUP_COUNT=/d' {env_path} && echo 'LOG_BACKUP_COUNT={val}' >> {env_path}")
            print(f"{GREEN}   ✔ Konfigurasi log disimpan.{RESET}")
    time.sleep(1)

def main_menu():
    while True:
        print_header("PUSAT KENDALI SENTINEL")
        print(f"   {THEME}[1]{RESET} {BOLD}Manajemen Aset & Radar{RESET}")
        print(f"   {THEME}[2]{RESET} {BOLD}Strategi & Gaya Investasi{RESET}")
        print(f"   {THEME}[3]{RESET} {BOLD}Manajemen Sumber Data Intel{RESET}")
        print(f"   {THEME}[4]{RESET} {BOLD}Bahasa Antarmuka (ID/EN){RESET}")
        print(f"   {THEME}[5]{RESET} {BOLD}Uji & Diagnosa AI Agents{RESET}")
        print(f"   {THEME}[6]{RESET} {BOLD}Pengaturan Lanjut (Quota/Log){RESET}")
        print(f"   {THEME}[7]{RESET} {BOLD}Keluar{RESET}")
        
        choice = input(f"\n   {THEME}PILIH OPSI : {RESET}")
        if choice == "1": manage_assets()
        elif choice == "2":
            config = load_config()
            print_header("STRATEGI INVESTASI")
            print(f"   Tipe Saat Ini: {YELLOW}{config.get('user_strategy', {}).get('type', 'DCA')}{RESET}")
            new_type = input("   Ubah Tipe (DCA/Scalp/Hold): ").upper()
            if new_type: config.setdefault("user_strategy", {})["type"] = new_type; save_config(config)
            print(f"{GREEN}   ✔ Strategi diperbarui.{RESET}"); time.sleep(1)
        elif choice == "3": manage_sources()
        elif choice == "4": manage_language()
        elif choice == "5": manage_ai_test()
        elif choice == "6": manage_advanced()
        elif choice == "7": break

if __name__ == "__main__":
    try: main_menu()
    except KeyboardInterrupt: print(f"\n{DIM}Menutup Konfigurasi...{RESET}"); sys.exit(0)
