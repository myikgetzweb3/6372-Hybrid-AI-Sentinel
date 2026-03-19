import sqlite3
import threading
import os
import json
import utils
from datetime import datetime, timedelta

# --- 🛡️ ORIGINAL CREATOR INFO (MANDATORY) ---
# AUTHOR: myikgetzweb3
# PROJECT: 6372 HYBRID AI SENTINEL (Supreme Database v2)
# --------------------------------------------

class SupremeDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.state_json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(db_path))), "state.json")
        self.lock = threading.Lock()
        self._initialize_db()
        self.check_integrity()

    def _get_connection(self):
        return sqlite3.connect(self.db_path, check_same_thread=False, timeout=30)

    def _initialize_db(self):
        with self.lock:
            try:
                conn = self._get_connection(); cursor = conn.cursor()
                cursor.execute('PRAGMA journal_mode=WAL')
                cursor.execute('PRAGMA synchronous=NORMAL')
                
                # TABLE: ASSETS (v2 with change_24h)
                cursor.execute('''CREATE TABLE IF NOT EXISTS assets_state (
                    asset TEXT PRIMARY KEY, last_price REAL, last_tier REAL, 
                    change_24h REAL, onchain_data TEXT, last_update TIMESTAMP)''')
                
                # Check if change_24h column exists, if not add it (migration)
                cursor.execute("PRAGMA table_info(assets_state)")
                cols = [c[1] for r in cursor.fetchall() for c in [r]]
                if "change_24h" not in cols:
                    cursor.execute("ALTER TABLE assets_state ADD COLUMN change_24h REAL DEFAULT 0")

                cursor.execute('''CREATE TABLE IF NOT EXISTS seen_items (identifier TEXT PRIMARY KEY, first_seen TIMESTAMP)''')
                cursor.execute('''CREATE TABLE IF NOT EXISTS price_history (id INTEGER PRIMARY KEY AUTOINCREMENT, asset TEXT, price REAL, timestamp TIMESTAMP)''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_history_asset ON price_history(asset, timestamp)')
                cursor.execute('''CREATE TABLE IF NOT EXISTS intel_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TIMESTAMP, source TEXT, title TEXT, message TEXT)''')
                cursor.execute('''CREATE TABLE IF NOT EXISTS system_state (key TEXT PRIMARY KEY, value TEXT, updated_at TIMESTAMP)''')
                cursor.execute('''CREATE TABLE IF NOT EXISTS paper_trades (id INTEGER PRIMARY KEY AUTOINCREMENT, asset TEXT, type TEXT, price REAL, timestamp TIMESTAMP, pnl REAL)''')
                cursor.execute('''CREATE TABLE IF NOT EXISTS heartbeat (subsystem TEXT PRIMARY KEY, last_pulse TIMESTAMP)''')
                conn.commit(); conn.close()
            except Exception as e:
                utils.logger.error(f"DB Init Error: {e}")

    def check_integrity(self):
        with self.lock:
            try:
                conn = self._get_connection()
                res = conn.execute("PRAGMA integrity_check").fetchone()
                conn.close()
                return res[0] == "ok"
            except: return False

    def sync_state_json(self):
        try:
            with self.lock:
                conn = self._get_connection(); cursor = conn.cursor()
                cursor.execute("SELECT asset, last_price FROM assets_state")
                rows = cursor.fetchall(); conn.close()
                data = {"last_1h_val": {r[0]: r[1] for r in rows}, "updated_at": datetime.now().isoformat()}
                with open(self.state_json_path, 'w') as f: json.dump(data, f, indent=2)
        except: pass

    def update_asset(self, asset, price=None, tier=None, onchain_data=None, change_24h=None):
        with self.lock:
            conn = None
            try:
                conn = self._get_connection(); cursor = conn.cursor()
                now = datetime.now().isoformat()
                cursor.execute('SELECT last_price, onchain_data FROM assets_state WHERE asset = ?', (asset,))
                row = cursor.fetchone()
                if not row:
                    p_val = price if price is not None else 0
                    cursor.execute('''INSERT INTO assets_state (asset, last_price, last_tier, change_24h, onchain_data, last_update)
                        VALUES (?, ?, ?, ?, ?, ?)''', (asset, p_val, None, change_24h or 0, json.dumps(onchain_data) if onchain_data else None, now))
                else:
                    old_onchain = json.loads(row[1]) if row[1] else {}
                    fields = []; params = []
                    if price is not None: fields.append("last_price = ?"); params.append(price)
                    
                    # ALWAYS Update Tier (to allow recovery to STABIL/None)
                    fields.append("last_tier = ?"); params.append(tier)
                    
                    if change_24h is not None: fields.append("change_24h = ?"); params.append(change_24h)
                    if onchain_data is not None: 
                        old_onchain.update(onchain_data)
                        fields.append("onchain_data = ?"); params.append(json.dumps(old_onchain))
                    fields.append("last_update = ?"); params.append(now)
                    params.append(asset)
                    cursor.execute(f"UPDATE assets_state SET {', '.join(fields)} WHERE asset = ?", tuple(params))
                conn.commit()
            except Exception as e:
                utils.logger.error(f"DB Update Error ({asset}): {e}")
            finally:
                if conn: conn.close()

    def get_asset_state(self, asset):
        with self.lock:
            try:
                conn = self._get_connection(); cursor = conn.cursor()
                cursor.execute('SELECT last_price, last_tier, onchain_data, change_24h FROM assets_state WHERE asset = ?', (asset,))
                row = cursor.fetchone(); conn.close()
                return {"price": row[0], "tier": row[1], "onchain": json.loads(row[2]) if row[2] else None, "change_24h": row[3] or 0} if row else {"price": 0, "tier": None, "onchain": None, "change_24h": 0}
            except: return {"price": 0, "tier": None, "onchain": None, "change_24h": 0}

    def get_asset_history(self, asset, limit=15):
        with self.lock:
            try:
                conn = self._get_connection(); cursor = conn.cursor()
                cursor.execute('SELECT price FROM price_history WHERE asset = ? ORDER BY timestamp DESC LIMIT ?', (asset, limit))
                rows = cursor.fetchall(); conn.close()
                prices = [r[0] for r in rows]; prices.reverse()
                return prices
            except: return []

    def get_price_one_hour_ago(self, asset):
        with self.lock:
            try:
                conn = self._get_connection(); cursor = conn.cursor()
                one_hour_ago = (datetime.now() - timedelta(minutes=60)).isoformat()
                cursor.execute('SELECT price FROM price_history WHERE asset = ? AND timestamp <= ? ORDER BY timestamp DESC LIMIT 1', (asset, one_hour_ago))
                row = cursor.fetchone(); conn.close()
                return row[0] if row else None
            except: return None

    def record_price_history(self, asset, price):
        with self.lock:
            try:
                conn = self._get_connection(); cursor = conn.cursor()
                now = datetime.now().isoformat()
                cursor.execute('INSERT INTO price_history (asset, price, timestamp) VALUES (?, ?, ?)', (asset, price, now))
                cursor.execute('DELETE FROM price_history WHERE id NOT IN (SELECT id FROM price_history WHERE asset = ? ORDER BY timestamp DESC LIMIT 100) AND asset = ?', (asset, asset))
                conn.commit(); conn.close()
            except: pass

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
                cursor.execute('INSERT OR IGNORE INTO seen_items (identifier, first_seen) VALUES (?, ?)', (identifier, datetime.now().isoformat()))
                cursor.execute('DELETE FROM seen_items WHERE identifier NOT IN (SELECT identifier FROM seen_items ORDER BY first_seen DESC LIMIT 1000)')
                conn.commit(); conn.close()
            except: pass

    def add_intel(self, source, title, message):
        with self.lock:
            try:
                conn = self._get_connection(); cursor = conn.cursor()
                now = datetime.now()
                cursor.execute('INSERT INTO intel_logs (timestamp, source, title, message) VALUES (?, ?, ?, ?)', (now.isoformat(), source, title, message))
                cursor.execute('DELETE FROM intel_logs WHERE id NOT IN (SELECT id FROM intel_logs ORDER BY id DESC LIMIT 50)')
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

    def update_heartbeat(self, subsystem):
        with self.lock:
            try:
                conn = self._get_connection(); cursor = conn.cursor()
                now = datetime.now().isoformat()
                cursor.execute('INSERT INTO heartbeat (subsystem, last_pulse) VALUES (?, ?) ON CONFLICT(subsystem) DO UPDATE SET last_pulse = excluded.last_pulse', (subsystem, now))
                conn.commit(); conn.close()
            except: pass

    def get_heartbeats(self):
        with self.lock:
            try:
                conn = self._get_connection(); cursor = conn.cursor()
                cursor.execute('SELECT subsystem, last_pulse FROM heartbeat')
                rows = cursor.fetchall(); conn.close()
                return {r[0]: r[1] for r in rows}
            except: return {}

    def record_paper_trade(self, asset, trade_type, price):
        with self.lock:
            try:
                conn = self._get_connection(); cursor = conn.cursor()
                now = datetime.now().isoformat()
                pnl = 0.0
                if trade_type == "SELL":
                    cursor.execute('SELECT price FROM paper_trades WHERE asset = ? AND type = "BUY" ORDER BY timestamp DESC LIMIT 1', (asset,))
                    last_buy = cursor.fetchone()
                    if last_buy: pnl = ((price - last_buy[0]) / last_buy[0]) * 100
                cursor.execute('INSERT INTO paper_trades (asset, type, price, timestamp, pnl) VALUES (?, ?, ?, ?, ?)', (asset, trade_type, price, now, pnl))
                conn.commit(); conn.close()
            except: pass

    def get_paper_trade_stats(self):
        with self.lock:
            try:
                conn = self._get_connection(); cursor = conn.cursor()
                cursor.execute('SELECT SUM(pnl) FROM paper_trades WHERE type = "SELL"')
                row = cursor.fetchone(); conn.close()
                return float(row[0]) if row and row[0] is not None else 0.0
            except: return 0.0

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
                    ON CONFLICT(key) DO UPDATE SET value = CAST(value AS INTEGER) + 1''', (key, datetime.now().isoformat()))
                conn.commit(); conn.close()
            except: pass
