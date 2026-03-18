import json
import threading
import time
import websocket
import utils
from core.database import SupremeDatabase

import os

# --- DEVELOPER INFO ---
# Author: myikgetzweb3
# Project: 6372 HYBRID AI SENTINEL (Market Engine Refined)

class MarketSentinel:
    def __init__(self, db: SupremeDatabase, config, ai_engine=None):
        self.db = db
        self.config = config
        self.ai = ai_engine # Reference to IntelligenceSentinel
        self.running = True
        self.ws = None
        self.alert_sound = utils.get_env("SOUND_ALERT_PATH", None)
        self.state_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "state.json")
        self.last_history_sync = {} # Track last DB write time per asset

    def _should_record_history(self, asset):
        now = time.time()
        if asset not in self.last_history_sync or now - self.last_history_sync[asset] >= 60:
            self.last_history_sync[asset] = now
            return True
        return False

    def _sync_state_json(self, asset, data_type, value):
        """Syncs key data to the legacy state.json for external audit tools"""
        try:
            state = {}
            if os.path.exists(self.state_path):
                with open(self.state_path, "r") as f:
                    try: state = json.load(f)
                    except: pass
            
            if data_type not in state: state[data_type] = {}
            state[data_type][asset] = value
            
            with open(self.state_path, "w") as f:
                json.dump(state, f, indent=2)
        except: pass

    def start(self):
        # 1. Start Binance WebSocket (Spot & Futures)
        threading.Thread(target=self._binance_ws_loop, daemon=True).start()
        # 2. Start DEX Polling
        threading.Thread(target=self._dex_polling_loop, daemon=True).start()
        # 3. Start On-chain Polling
        threading.Thread(target=self._onchain_polling_loop, daemon=True).start()

    def _onchain_polling_loop(self):
        while self.running:
            try:
                assets = self.config.get("assets", {})
                for name, cfg in assets.items():
                    onchain = cfg.get("onchain")
                    if not onchain: continue
                    
                    # 1. BTC Deep On-chain Monitoring
                    if onchain.get("network") == "bitcoin" and name == "BTC":
                        whale_data = utils.fetch_btc_whale_tx()
                        if whale_data:
                            title = f"BTC ON-CHAIN ALERT: Large movement detected in Mempool (Fee: {whale_data['val']} sat/vB)"
                            if self.ai: self.ai.analyze_external_event(title, source_type="WHALE")
                            self.db.add_intel("ON-CHAIN", "BTC Whale", title)
                            # Tag BTC sentiment as whale_buy for high-priority mempool activity
                            self.db.update_asset("BTC", onchain_data={"sentiment": "whale_buy", "timestamp": time.time()})

                    # 2. Solana / MOODENG Deep On-chain Monitoring
                    elif onchain.get("network") == "solana" and onchain.get("address"):
                        token_addr = onchain.get("address")
                        burst = utils.fetch_solana_whale_burst(token_addr)
                        if burst and name == "MOODENG":
                            title = f"MOODENG BURST: Spontaneous volume spike on {burst['pair']} (${burst['vol']:,.0f} in 5m)"
                            if self.ai: self.ai.analyze_external_event(title, source_type="WHALE")
                            self.db.add_intel("ON-CHAIN", f"{name} Burst", title)
                        
                        # Fallback to existing ratio monitoring for dashboard
                        pair_data = utils.fetch_solana_trades(token_addr)
                        if pair_data:
                            m5_buys = pair_data.get("txns", {}).get("m5", {}).get("buys", 0)
                            m5_sells = pair_data.get("txns", {}).get("m5", {}).get("sells", 0)
                            
                            sentiment = "neutral"
                            if name in ["BTC", "MOODENG"]:
                                if m5_buys > (m5_sells * 2.5) and m5_buys > 10:
                                    sentiment = "whale_buy"
                                elif m5_sells > (m5_buys * 2.5) and m5_sells > 10:
                                    sentiment = "whale_sell"

                            self.db.update_asset(name, onchain_data={
                                "m5_activity": {"buys": m5_buys, "sells": m5_sells}, 
                                "sentiment": sentiment,
                                "timestamp": time.time()
                            })

                    # 3. Base Gas Tracker (New)
                    elif onchain.get("network") == "base":
                        gas = utils.fetch_base_gas()
                        if gas > 0:
                            self.db.update_asset(name, onchain_data={"gas_gwei": gas, "timestamp": time.time()})
            except Exception as e:
                utils.logger.error(f"On-chain Loop Error: {e}")
            time.sleep(300) # Check every 5 minutes

    def _check_alerts(self, asset, price, diff_24h):
        """Logic to compare price with thresholds and send notifications"""
        self._sync_state_json(asset, "last_1h_val", price)
        
        asset_cfg = self.config.get("assets", {}).get(asset, {})
        thresholds = asset_cfg.get("thresholds", {})
        
        # Get previous state from DB
        prev = self.db.get_asset_state(asset)
        
        # --- NEW: 1% HOURLY HEARTBEAT (No AI) ---
        history_1h = self.db.get_asset_history(asset, limit=60)
        if len(history_1h) >= 60:
            price_60m_ago = history_1h[0]
            diff_1h = ((price - price_60m_ago) / price_60m_ago) * 100
            
            # Check cooldown to avoid spamming
            last_1h_notif_key = f"last_1h_notif_{asset}"
            last_notif_time = float(self.db.get_system_state(last_1h_notif_key) or 0)
            
            if abs(diff_1h) >= 1.0 and (time.time() - last_notif_time > 3300): # 55 mins cooldown
                utils.logger.info(f"Hourly Movement: {asset} {diff_1h:+.2f}%")
                dir_emoji = "🟢" if diff_1h > 0 else "🔴"
                # Combined Style 1 & 2: Tactical Flash Alert
                utils.send_notification(
                    f"⚡ [FLASH] {asset} {dir_emoji} {diff_1h:+.1f}%", 
                    f"Price: ${price:,.8f} | 1H Heartbeat", 
                    timeout=3
                )
                self.db.set_system_state(last_1h_notif_key, str(time.time()))

        # 1. Check Spikes (Sell Signals) based on 24h change
        for spike in thresholds.get("spikes", []):
            lvl = spike.get("level", 999)
            if diff_24h >= lvl and prev.get("tier") != lvl:
                msg = spike.get("msg", f"{asset} MELAMBUNG!")
                utils.send_notification(f"🚀 {msg}", f"Kenaikan: +{diff_24h:.2f}% (24j)", sound_path=self.alert_sound)
                self.db.update_asset(asset, price, tier=lvl)
                self.db.add_intel("MARKET", f"SPIKE: {asset}", f"Deteksi kenaikan {diff_24h:.2f}%. Sinyal: {spike.get('action', 'Monitor')}")
                return

        # 2. Check Dips (Buy Signals) based on 24h change
        for dip in thresholds.get("dips", []):
            lvl = dip.get("level", -999)
            if diff_24h <= lvl and prev.get("tier") != lvl:
                msg = dip.get("msg", f"{asset} DISKON!")
                utils.send_notification(f"📉 {msg}", f"Penurunan: {diff_24h:.2f}% (24j)", sound_path=self.alert_sound)
                self.db.update_asset(asset, price, tier=lvl)
                self.db.add_intel("MARKET", f"DIP: {asset}", f"Deteksi penurunan {diff_24h:.2f}%. Sinyal: {dip.get('action', 'DCA')}")
                return

        # 3. Regular Hourly update if change is significant
        last_p = prev.get("price", 0)
        if last_p > 0:
            diff_tick = ((price - last_p) / last_p) * 100
            # SANITY CHECK: If diff is impossible (e.g. > 500%), it's a data artifact
            if abs(diff_tick) > 500:
                self.db.update_asset(asset, price, tier=None)
                return

            hourly_limit = float(thresholds.get("hourly", 1.0))
            if abs(diff_tick) >= hourly_limit:
                self.db.update_asset(asset, price, tier=round(diff_tick, 2))
        else:
            # First time price entry, force STABLE
            self.db.update_asset(asset, price, tier=None)

    def _binance_ws_loop(self):
        assets = self.config.get("assets", {})
        raw_symbols = [s["symbol"].upper() for a, s in assets.items() if s.get("symbol") and not s.get("dex")]
        if not raw_symbols: return

        stream_list = [f"{s.lower()}@ticker" for s in raw_symbols]
        
        def start_socket(base_url, name):
            url = f"{base_url}/ws/{'/'.join(stream_list)}"
            
            def on_message(ws, message):
                data = json.loads(message)
                sym = data.get('s')
                # Futures uses 'lastPrice', Spot uses 'c'
                price = float(data.get('c') or data.get('lastPrice', 0))
                change_24h = float(data.get('P', 0))
                
                if price <= 0: return 

                asset_name = next((a for a, s in assets.items() if s.get("symbol") == sym), None)
                if asset_name:
                    self._check_alerts(asset_name, price, change_24h)
                    self.db.update_asset(asset_name, price)
                    if self._should_record_history(asset_name):
                        self.db.record_price_history(asset_name, price)

            def on_error(ws, error): pass
            def on_close(ws, c, m):
                if self.running: time.sleep(10); start_socket(base_url, name)

            utils.logger.info(f"Connecting to Binance {name} Stream...")
            ws = websocket.WebSocketApp(url, on_message=on_message, on_error=on_error, on_close=on_close)
            ws.run_forever()

        # Run both in separate threads
        threading.Thread(target=start_socket, args=("wss://stream.binance.com:9443", "Spot"), daemon=True).start()
        threading.Thread(target=start_socket, args=("wss://fstream.binance.com", "Futures"), daemon=True).start()

    def _dex_polling_loop(self):
        while self.running:
            try:
                assets = self.config.get("assets", {})
                for name, cfg in assets.items():
                    dex = cfg.get("dex")
                    # If it's on Binance, we skip DEX price update to avoid overwriting with low-liq DEX data
                    if cfg.get("symbol") and not dex:
                        continue
                    
                    if dex:
                        addr = dex.get("address")
                        expected_s = cfg.get("symbol")
                        if addr or name:
                            data = utils.fetch_dex_price(addr, asset_name=name, expected_sym=expected_s)
                            if data:
                                p = data["price_usd"]; c24 = data["change_24h"]
                                self._check_alerts(name, p, c24)
                                self.db.update_asset(name, p)
                                if self._should_record_history(name):
                                    self.db.record_price_history(name, p)
                    time.sleep(2)
            except Exception as e:
                utils.logger.error(f"DEX Loop Error: {e}")
            time.sleep(60)
