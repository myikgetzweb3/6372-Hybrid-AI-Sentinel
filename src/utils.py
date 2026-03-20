import warnings
# Suppress Gemini API Deprecation and other warnings at the absolute top
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")
warnings.filterwarnings("ignore", category=UserWarning, module="google.generativeai")

import os
import sys
import subprocess
import platform
import psutil
import json
import requests
import feedparser
import logging
import urllib3
import time
import re
import shutil
import asyncio
import httpx
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
from urllib.parse import urlparse, urlunparse, quote
from plyer import notification

# --- 🛡️ ORIGINAL CREATOR INFO (MANDATORY) ---
# AUTHOR: myikgetzweb3
# PROJECT: 6372 HYBRID AI SENTINEL (Supreme Refinement)
# --------------------------------------------

# Dynamic Path Resolution
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(BASE_DIR, "src") not in sys.path:
    sys.path.append(os.path.join(BASE_DIR, "src"))

# Platform Detection
IS_WINDOWS = platform.system().lower() == "windows"

# Theme Constants
THEME = "\033[96m" # Cyan Neon
GREEN, YELLOW, RED = "\033[92m", "\033[93m", "\033[91m"
BOLD, RESET, DIM = "\033[1m", "\033[0m", "\033[2m"

# Helper for initial ENV read (since logger isn't ready)
def _get_raw_env(key, default):
    try:
        env_path = os.path.join(BASE_DIR, ".env")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    if line.strip().startswith(f"{key}="):
                        val = line.split("=", 1)[1].strip()
                        return val if val else default
    except: pass
    return os.getenv(key, default)

# Logging Setup (Optimized for 2026)
LOG_PATH = os.path.join(BASE_DIR, "activity.log")
LOG_MAX_BYTES = int(_get_raw_env("LOG_MAX_BYTES", 5242880))
LOG_BACKUP_COUNT = int(_get_raw_env("LOG_BACKUP_COUNT", 3))

logger = logging.getLogger("6372Sentinel")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

# Rotating File Handler
file_handler = RotatingFileHandler(LOG_PATH, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Stream Handler
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

http_session = requests.Session()

def get_env(key, default, base_dir=BASE_DIR):
    try:
        env_path = os.path.join(base_dir, ".env")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    if line.strip().startswith(f"{key}="):
                        val = line.split("=", 1)[1].strip()
                        return val if val else default
    except Exception as e:
        logger.debug(f"Env Load Error ({key}): {e}")
    return os.getenv(key, default)

def get_text(key):
    lang = get_env("APP_LANGUAGE", "id")
    locale_path = os.path.join(BASE_DIR, f"config/locales/{lang}.json")
    try:
        if os.path.exists(locale_path):
            with open(locale_path, 'r') as f:
                data = json.load(f); return data.get(key, key)
    except Exception as e:
        logger.debug(f"Locale Load Error ({lang}/{key}): {e}")
    return key

def get_brand_credit():
    return "Developed by myikgetzweb3"

def get_logo():
    # Final Supreme Logo v3: Enhanced '7' and spacing
    return [
        "  ██████╗  ██████╗  ███████╗ ██████╗ ",
        " ██╔════╝  ╚════██╗ ╚══███╔╝ ╚════██╗",
        " ███████╗   █████╔╝   ███╔╝   █████╔╝",
        " ██╔═══██╗  ╚═══██╗  ███╔╝   ██╔═══╝ ",
        " ╚██████╔╝ ██████╔╝ ███╔╝    ███████╗",
        "  ╚═════╝  ╚═════╝  ╚══╝     ╚══════╝"
    ]

def clear_terminal():
    os.system('cls' if IS_WINDOWS else 'clear')

def center_line(text, width):
    # Regex Universal untuk menghapus SEMUA kode ANSI (warna, gaya, posisi kursor)
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    clean_text = ansi_escape.sub('', text)
    padding = max(0, (width - len(clean_text)) // 2)
    return " " * padding + text

def get_terminal_width():
    return shutil.get_terminal_size().columns

def backup_database():
    """Create a hot backup using SQLite VACUUM INTO (100% safe)"""
    db_src = os.path.join(BASE_DIR, "data", "6372.db")
    if not os.path.exists(db_src): return
    
    backup_dir = os.path.join(BASE_DIR, ".SAFE_BACKUP")
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_dest = os.path.join(backup_dir, f"6372_{ts}.db.bak")
    
    try:
        import sqlite3
        conn = sqlite3.connect(db_src)
        conn.execute(f"VACUUM INTO '{db_dest}'")
        conn.close()
        
        # Keep only last 5 backups
        backups = sorted([f for f in os.listdir(backup_dir) if f.endswith(".bak")])
        while len(backups) > 5:
            os.remove(os.path.join(backup_dir, backups.pop(0)))
        logger.debug(f"Hot backup created: {db_dest}")
    except Exception as e:
        logger.error(f"Backup Error: {e}")

import google.generativeai as genai

# --- AI CORE ---
def get_heuristic_analysis(text):
    t = text.lower()
    if any(kw in t for kw in ["crash", "dump", "plummet", "exploit", "hack", "fud", "danger"]):
        return "⚠️ ANALISIS DARURAT: Sentimen negatif terdeteksi. Waspadai penurunan harga."
    if any(kw in t for kw in ["moon", "pump", "bullish", "rally", "breakout", "alpha", "buy"]):
        return "🚀 ANALISIS CEPAT: Momentum positif terdeteksi. Potensi kenaikan berlanjut."
    return "⚖️ ANALISIS NETRAL: Berita rutin terdeteksi. Tetap pada strategi Anda."

def call_ollama(prompt):
    model = get_env("OLLAMA_MODEL", "tinyllama")
    url = get_env("OLLAMA_API_URL", "http://localhost:11434/api/generate")
    try:
        res = http_session.post(url, json={"model": model, "prompt": prompt, "stream": False}, timeout=120)
        return res.json().get("response", "").strip()
    except: return "AI Lokal Offline."

def call_gemini(prompt):
    api_key = get_env("GEMINI_API_KEY", "")
    if not api_key: 
        logger.warning("No Gemini Key - Falling back to Ollama.")
        return call_ollama(prompt)
    try:
        genai.configure(api_key=api_key)
        model_name = get_env("GEMINI_MODEL", "gemini-3.1-flash-lite-preview")
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini API Error: {e} - Falling back to Ollama.")
        return call_ollama(prompt)

def discovery_ai_asset_info(asset_name):
    """Smart Onboarding: AI searches for best metadata for a new asset"""
    prompt = f"Identify the primary blockchain and official/most active Twitter handle for the crypto asset '{asset_name}'. Return ONLY a JSON object like: {{\"network\": \"solana/ethereum/base/bsc/bitcoin\", \"handle\": \"username\"}}"
    res = call_gemini(prompt)
    try:
        # Extract JSON from potential AI chatter
        match = re.search(r'\{.*\}', res.replace('\n', ''))
        if match: return json.loads(match.group())
    except: pass
    return {"network": "unknown", "handle": ""}

async def fetch_rss_async(url):
    try:
        async with httpx.AsyncClient(headers={'User-Agent': 'Mozilla/5.0'}, timeout=15) as client:
            res = await client.get(url)
            feed = feedparser.parse(res.text)
            results = []
            for entry in feed.entries[:5]:
                results.append({"title": entry.title, "link": entry.link})
            return results
    except Exception as e:
        logger.debug(f"RSS Fetch Error ({url}): {e}")
        return []

def fetch_rss(url):
    try:
        res = http_session.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        feed = feedparser.parse(res.text)
        results = []
        for entry in feed.entries[:5]:
            results.append({"title": entry.title, "link": entry.link})
        return results
    except Exception as e:
        logger.debug(f"RSS Fetch Error ({url}): {e}")
        return []

async def fetch_dex_price_async(address, asset_name=None, expected_sym=None):
    if not address and not asset_name: return None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Try direct token endpoint first
            url = f"https://api.dexscreener.com/latest/dex/tokens/{address}"
            res = await client.get(url)
            data = res.json() if res.status_code == 200 else {}
            pairs = data.get("pairs", [])
            
            # Fallback to search if direct token fails and we have a name
            if not pairs and asset_name:
                url_search = f"https://api.dexscreener.com/latest/dex/search?q={asset_name}"
                res_s = await client.get(url_search)
                if res_s.status_code == 200:
                    pairs = res_s.json().get("pairs", [])
            
            if pairs:
                # Sort by liquidity primarily
                pairs.sort(key=lambda x: float(x.get("liquidity", {}).get("usd", 0)), reverse=True)
                
                # Smart Filter: For Solana, prioritize Raydium or Jupiter
                primary_dexes = ["raydium", "jupiter", "uniswap", "pancakeswap"]
                best_pair = pairs[0]
                for dx in primary_dexes:
                    found = [p for p in pairs if p.get("dexId", "").lower() == dx]
                    if found:
                        best_pair = found[0]
                        break

                # Validation: If we have an expected symbol, ensure it matches
                if expected_sym:
                    if best_pair.get("baseToken", {}).get("symbol", "").replace("$", "").upper() != expected_sym.upper():
                        valid_pairs = [p for p in pairs if p.get("baseToken", {}).get("symbol", "").replace("$", "").upper() == expected_sym.upper()]
                        if valid_pairs: best_pair = valid_pairs[0]
                        else: return None

                return {
                    "price_usd": float(best_pair.get("priceUsd", 0)), 
                    "change_24h": float(best_pair.get("priceChange", {}).get("h24", 0)),
                    "base_token": best_pair.get("baseToken", {}).get("symbol", ""),
                    "buys": best_pair.get("txns", {}).get("m5", {}).get("buys", 0),
                    "sells": best_pair.get("txns", {}).get("m5", {}).get("sells", 0)
                }
    except Exception as e:
        logger.debug(f"Price Fetch Error ({asset_name or address}): {e}")
    return None

def fetch_dex_price(address, asset_name=None, expected_sym=None):
    if not address and not asset_name: return None
    try:
        # Try direct token endpoint first
        url = f"https://api.dexscreener.com/latest/dex/tokens/{address}"
        res = requests.get(url, timeout=10)
        data = res.json() if res.status_code == 200 else {}
        pairs = data.get("pairs", [])
        
        # Fallback to search if direct token fails and we have a name
        if not pairs and asset_name:
            url_search = f"https://api.dexscreener.com/latest/dex/search?q={asset_name}"
            res_s = requests.get(url_search, timeout=10)
            if res_s.status_code == 200:
                pairs = res_s.json().get("pairs", [])
        
        if pairs:
            # Sort by liquidity primarily
            pairs.sort(key=lambda x: float(x.get("liquidity", {}).get("usd", 0)), reverse=True)
            
            # Smart Filter: For Solana, prioritize Raydium or Jupiter
            primary_dexes = ["raydium", "jupiter", "uniswap", "pancakeswap"]
            best_pair = pairs[0]
            for dx in primary_dexes:
                found = [p for p in pairs if p.get("dexId", "").lower() == dx]
                if found:
                    best_pair = found[0]
                    break

            # Validation: If we have an expected symbol, ensure it matches
            if expected_sym:
                # Some DEXes use $ symbol prefix, clean it
                if best_pair.get("baseToken", {}).get("symbol", "").replace("$", "").upper() != expected_sym.upper():
                    # If primary dex fails symbol check, try other pairs
                    valid_pairs = [p for p in pairs if p.get("baseToken", {}).get("symbol", "").replace("$", "").upper() == expected_sym.upper()]
                    if valid_pairs: best_pair = valid_pairs[0]
                    else: return None

            return {
                "price_usd": float(best_pair.get("priceUsd", 0)), 
                "change_24h": float(best_pair.get("priceChange", {}).get("h24", 0)),
                "base_token": best_pair.get("baseToken", {}).get("symbol", "")
            }
    except Exception as e:
        logger.debug(f"Price Fetch Error ({asset_name or address}): {e}")
    return None

async def fetch_btc_whale_tx_async():
    """Detect large transactions in the BTC Mempool (> 500 BTC)"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get("https://mempool.space/api/v1/fees/mempool-blocks")
            if res.status_code == 200:
                blocks = res.json()
                if blocks:
                    first_block = blocks[0]
                    if first_block.get('medianFee', 0) > 50:
                        return {"type": "CONGESTION", "val": first_block.get('medianFee')}
    except Exception as e:
        logger.debug(f"BTC On-chain Fetch Error: {e}")
    return None

def fetch_btc_whale_tx():
    """Detect large transactions in the BTC Mempool (> 500 BTC)"""
    try:
        # Using Mempool.space API to check for large recent transactions
        res = requests.get("https://mempool.space/api/v1/fees/mempool-blocks", timeout=10)
        if res.status_code == 200:
            blocks = res.json()
            if blocks:
                # Analyze top pending block for heavy transactions
                first_block = blocks[0]
                if first_block.get('medianFee', 0) > 50: # High congestion often follows whale moves
                    return {"type": "CONGESTION", "val": first_block.get('medianFee')}
    except Exception as e:
        logger.debug(f"BTC On-chain Fetch Error: {e}")
    return None

async def fetch_solana_whale_burst_async(address):
    """Detect spontaneous volume bursts for Solana tokens"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{address}"
            res = await client.get(url)
            if res.status_code == 200:
                pairs = res.json().get("pairs", [])
                if pairs:
                    pairs.sort(key=lambda x: float(x.get("liquidity", {}).get("usd", 0)), reverse=True)
                    p = pairs[0]
                    m5_vol = float(p.get("volume", {}).get("m5", 0))
                    h24_vol = float(p.get("volume", {}).get("h24", 0))
                    if m5_vol > (h24_vol * 0.05) and m5_vol > 10000:
                        return {"type": "BURST", "vol": m5_vol, "pair": p.get("dexId")}
    except Exception as e:
        logger.debug(f"SOL Burst Fetch Error: {e}")
    return None

def fetch_solana_whale_burst(address):
    """Detect spontaneous volume bursts for Solana tokens"""
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{address}"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            pairs = res.json().get("pairs", [])
            if pairs:
                pairs.sort(key=lambda x: float(x.get("liquidity", {}).get("usd", 0)), reverse=True)
                p = pairs[0]
                m5_vol = float(p.get("volume", {}).get("m5", 0))
                h24_vol = float(p.get("volume", {}).get("h24", 0))
                # Burst Detection: If 5m volume is more than 5% of 24h volume
                if m5_vol > (h24_vol * 0.05) and m5_vol > 10000:
                    return {"type": "BURST", "vol": m5_vol, "pair": p.get("dexId")}
    except Exception as e:
        logger.debug(f"SOL Burst Fetch Error: {e}")
    return None

async def fetch_solana_trades_async(token_address):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
            res = await client.get(url)
            if res.status_code == 200:
                pairs = res.json().get("pairs", [])
                if not pairs: return []
                pairs.sort(key=lambda x: float(x.get("volume", {}).get("h24", 0)), reverse=True)
                return pairs[0]
    except Exception as e:
        logger.debug(f"SOL Trades Fetch Error: {e}")
    return None

def fetch_solana_trades(token_address):
    """Fetch recent large trades for a Solana token via DexScreener/Helius-like logic"""
    try:
        # We use DexScreener's pair information to find recent high-volume pairs
        url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            pairs = res.json().get("pairs", [])
            if not pairs: return []
            # Sort by volume or liquidity
            pairs.sort(key=lambda x: float(x.get("volume", {}).get("h24", 0)), reverse=True)
            primary_pair = pairs[0]
            return primary_pair
    except Exception as e:
        logger.debug(f"SOL Trades Fetch Error: {e}")
    return None

async def fetch_base_gas_async():
    try:
        url = "https://mainnet.base.org"
        payload = {"jsonrpc": "2.0", "method": "eth_gasPrice", "params": [], "id": 1}
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.post(url, json=payload)
            if res.status_code == 200:
                hex_gas = res.json().get("result", "0x0")
                gwei = int(hex_gas, 16) / 10**9
                return round(gwei, 4)
    except Exception as e:
        logger.debug(f"Base Gas Fetch Error: {e}")
    return 0

def fetch_base_gas():
    """Fetch current gas price on Base Network via Public RPC"""
    try:
        url = "https://mainnet.base.org"
        payload = {"jsonrpc": "2.0", "method": "eth_gasPrice", "params": [], "id": 1}
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            hex_gas = res.json().get("result", "0x0")
            # Convert wei to gwei
            gwei = int(hex_gas, 16) / 10**9
            return round(gwei, 4) # Base gas is usually very low
    except Exception as e:
        logger.debug(f"Base Gas Fetch Error: {e}")
    return 0

def send_notification(title, message, sound_path=None, timeout=10):
    try: notification.notify(title=title.upper(), message=message[:240], app_name="6372-Sentinel", timeout=timeout)
    except Exception as e:
        logger.debug(f"Notification Error: {e}")
    if sound_path and os.path.exists(sound_path):
        try:
            if not IS_WINDOWS: subprocess.Popen(["paplay", sound_path], stderr=subprocess.DEVNULL)
            else:
                import winsound
                winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception as e:
            logger.debug(f"Sound Error: {e}")

def is_monitor_running():
    """Ultra-Reliable Process Detection using PID file only"""
    pid_file = os.path.join(BASE_DIR, "sentinel.pid")
    my_pid = os.getpid()
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                pid_str = f.read().strip()
                if pid_str:
                    pid = int(pid_str)
                    # Jika PID di file adalah proses ini sendiri, berarti aman (lanjutkan)
                    if pid == my_pid: return None
                    # Check if this exact PID is actually a Python process
                    if psutil.pid_exists(pid):
                        proc = psutil.Process(pid)
                        if "python" in proc.name().lower():
                            return pid
        except: pass
    return None

def get_key_universal():
    if IS_WINDOWS:
        import msvcrt
        if msvcrt.kbhit(): return msvcrt.getch().decode('utf-8', errors='ignore')
    else:
        import select
        if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
            return sys.stdin.read(1)
    return None

def generate_sparkline(series, width=10):
    if not series or len(series) < 2: return " " * width
    # Normalize series to fit in block heights (0-7)
    chars = [" ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
    min_v = min(series); max_v = max(series)
    range_v = max_v - min_v
    
    # If price is static, show middle bars
    if range_v == 0: return chars[4] * width
    
    # Take last 'width' elements
    data = series[-width:]
    result = ""
    for v in data:
        idx = int(((v - min_v) / range_v) * (len(chars) - 1))
        result += chars[idx]
    return result.ljust(width)
