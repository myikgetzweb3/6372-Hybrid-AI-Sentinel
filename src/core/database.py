import sqlite3
import threading
import os
import json
from datetime import datetime, timedelta

# --- 🛡️ ORIGINAL CREATOR INFO (MANDATORY) ---
# AUTHOR: myikgetzweb3
# PROJECT: 6372 HYBRID AI SENTINEL (Supreme Database)
# --------------------------------------------

class SupremeDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._initialize_db()

    def _get_connection(self):
        """Standard optimized connection factory"""
        return sqlite3.connect(self.db_path, check_same_thread=False, timeout=30)

    def _initialize_db(self):
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                # HIGH PERFORMANCE PRAGMAS
                cursor.execute('PRAGMA journal_mode=WAL')
                cursor.execute('PRAGMA synchronous=NORMAL')
                
                # TABLE: ASSETS (Enhanced with metadata)
                cursor.execute('''CREATE TABLE IF NOT EXISTS assets_state (
                    asset TEXT PRIMARY KEY, last_price REAL, last_tier REAL, 
                    onchain_data TEXT, last_update TIMESTAMP)''')
                
                # TABLE: SEEN_ITEMS (Persistent de-duplication)
                cursor.execute('''CREATE TABLE IF NOT EXISTS seen_items (
                    identifier TEXT PRIMARY KEY, first_seen TIMESTAMP)''')
                
                # TABLE: PRICE_HISTORY (New for real sparklines)
                cursor.execute('''CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, asset TEXT, 
                    price REAL, timestamp TIMESTAMP)''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_history_asset ON price_history(asset, timestamp)')
                
                # TABLE: INTELLIGENCE
                cursor.execute('''CREATE TABLE IF NOT EXISTS intel_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TIMESTAMP, 
                    source TEXT, title TEXT, message TEXT)''')
                
                # TABLE: SYSTEM
                cursor.execute('''CREATE TABLE IF NOT EXISTS system_state (
                    key TEXT PRIMARY KEY, value TEXT, updated_at TIMESTAMP)''')
                
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Database Initialization Error: {e}")

    # --- ATOMIC ASSET UPDATES ---
    def update_asset(self, asset, price=None, tier=None, onchain_data=None):
        with self.lock:
            conn = None
            try:
                conn = self._get_connection(); cursor = conn.cursor()
                now = datetime.now().isoformat()
                
                # Check if asset exists
                cursor.execute('SELECT last_price FROM assets_state WHERE asset = ?', (asset,))
                row = cursor.fetchone()
                
                if not row:
                    # New asset entry: Ensure price is never None on insert
                    p_val = price if price is not None else 0
                    cursor.execute('''INSERT INTO assets_state (asset, last_price, last_tier, onchain_data, last_update)
                        VALUES (?, ?, ?, ?, ?)''', (asset, p_val, None, json.dumps(onchain_data) if onchain_data else None, now))
                else:
                    # Dynamic update: Always update price if provided, else keep old
                    # BUT: if old price was 0, keep tier as None to avoid % artifacts
                    old_p = row[0]
                    fields = []; params = []
                    if price is not None: 
                        fields.append("last_price = ?"); params.append(price)
                        if old_p <= 0: # First real price after 0
                            fields.append("last_tier = ?"); params.append(None)
                    
                    if tier is not None and old_p > 0: 
                        fields.append("last_tier = ?"); params.append(tier)
                    
                    if onchain_data is not None: 
                        fields.append("onchain_data = ?"); params.append(json.dumps(onchain_data))
                    
                    fields.append("last_update = ?"); params.append(now)
                    params.append(asset)
                    
                    sql = f"UPDATE assets_state SET {', '.join(fields)} WHERE asset = ?"
                    cursor.execute(sql, tuple(params))
                
                conn.commit()
            except Exception as e:
                if conn: conn.rollback()
                print(f"DB Update Error ({asset}): {e}")
            finally:
                if conn: conn.close()

    # --- PERSISTENT SEEN ITEMS (News/Signals) ---
    def is_already_seen(self, identifier):
        with self.lock:
            try:
                conn = self._get_connection(); cursor = conn.cursor()
                cursor.execute('SELECT 1 FROM seen_items WHERE identifier = ?', (identifier,))
                res = cursor.fetchone(); conn.close()
                return res is not None
            except: return False

    def mark_as_seen(self, identifier):
        with self.lock:
            try:
                conn = self._get_connection(); cursor = conn.cursor()
                cursor.execute('INSERT OR IGNORE INTO seen_items (identifier, first_seen) VALUES (?, ?)', 
                               (identifier, datetime.now().isoformat()))
                # Cleanup: keep only last 1000 items
                cursor.execute('DELETE FROM seen_items WHERE identifier NOT IN (SELECT identifier FROM seen_items ORDER BY first_seen DESC LIMIT 1000)')
                conn.commit(); conn.close()
            except: pass

    def get_asset_state(self, asset):
        with self.lock:
            try:
                conn = self._get_connection(); cursor = conn.cursor()
                cursor.execute('SELECT last_price, last_tier, onchain_data FROM assets_state WHERE asset = ?', (asset,))
                row = cursor.fetchone(); conn.close()
                return {"price": row[0], "tier": row[1], "onchain": json.loads(row[2]) if row[2] else None} if row else {"price": 0, "tier": None, "onchain": None}
            except: return {"price": 0, "tier": None, "onchain": None}

    def get_asset_history(self, asset, limit=15):
        with self.lock:
            try:
                conn = self._get_connection(); cursor = conn.cursor()
                cursor.execute('SELECT price FROM price_history WHERE asset = ? ORDER BY timestamp DESC LIMIT ?', (asset, limit))
                rows = cursor.fetchall(); conn.close()
                prices = [r[0] for r in rows]
                prices.reverse() # Chronological order
                return prices
            except: return []

    def record_price_history(self, asset, price):
        with self.lock:
            try:
                conn = self._get_connection(); cursor = conn.cursor()
                now = datetime.now().isoformat()
                cursor.execute('INSERT INTO price_history (asset, price, timestamp) VALUES (?, ?, ?)', (asset, price, now))
                # Pruning: Keep only last 100 snapshots per asset
                cursor.execute('''DELETE FROM price_history WHERE id NOT IN (
                    SELECT id FROM price_history WHERE asset = ? ORDER BY timestamp DESC LIMIT 100
                ) AND asset = ?''', (asset, asset))
                conn.commit(); conn.close()
            except: pass

    # --- INTEL MANAGEMENT ---
    def add_intel(self, source, title, message):
        with self.lock:
            try:
                conn = self._get_connection(); cursor = conn.cursor()
                now = datetime.now()
                cursor.execute('INSERT INTO intel_logs (timestamp, source, title, message) VALUES (?, ?, ?, ?)', 
                               (now.isoformat(), source, title, message))
                
                # FIFO & AUTO-CLEANUP (Limit 50, Expiry 48h)
                cursor.execute('DELETE FROM intel_logs WHERE id NOT IN (SELECT id FROM intel_logs ORDER BY id DESC LIMIT 50)')
                expiry = (now - timedelta(hours=48)).isoformat()
                cursor.execute('DELETE FROM intel_logs WHERE timestamp < ?', (expiry,))
                
                conn.commit(); conn.close()
            except: pass

    def get_all_intel(self):
        with self.lock:
            try:
                conn = self._get_connection(); cursor = conn.cursor()
                cursor.execute('SELECT id, timestamp, source, title, message FROM intel_logs ORDER BY id DESC')
                rows = cursor.fetchall(); conn.close()
                return [{"id": r[0], "time_str": r[1][11:19], "source": r[2], "title": r[3], "message": r[4]} for r in rows]
            except: return []

    # --- SYSTEM STATE PERSISTENCE ---
    def get_system_state(self, key):
        with self.lock:
            try:
                conn = self._get_connection(); cursor = conn.cursor()
                cursor.execute('SELECT value FROM system_state WHERE key = ?', (key,))
                row = cursor.fetchone(); conn.close()
                return row[0] if row else None
            except: return None

    def set_system_state(self, key, value):
        with self.lock:
            try:
                conn = self._get_connection(); cursor = conn.cursor()
                now = datetime.now().isoformat()
                cursor.execute('''INSERT INTO system_state (key, value, updated_at) VALUES (?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at''', 
                    (key, value, now))
                conn.commit(); conn.close()
            except: pass

    # --- QUOTA TRACKING ---
    def get_quota(self):
        with self.lock:
            try:
                conn = self._get_connection(); cursor = conn.cursor()
                today = datetime.now().strftime("%Y-%m-%d")
                cursor.execute('SELECT value FROM system_state WHERE key = ?', (f"gemini_quota_{today}",))
                row = cursor.fetchone(); conn.close()
                return int(row[0]) if row else 0
            except: return 0

    def increment_quota(self):
        with self.lock:
            try:
                conn = self._get_connection(); cursor = conn.cursor()
                today = datetime.now().strftime("%Y-%m-%d")
                key = f"gemini_quota_{today}"
                cursor.execute('''INSERT INTO system_state (key, value, updated_at) VALUES (?, '1', ?)
                    ON CONFLICT(key) DO UPDATE SET value = CAST(value AS INTEGER) + 1''', 
                    (key, datetime.now().isoformat()))
                conn.commit(); conn.close()
            except: pass
