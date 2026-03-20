import json
import threading
import time
import asyncio
import websocket
import utils
from core.database import SupremeDatabase
import os

# --- DEVELOPER INFO ---
# Author: myikgetzweb3
# Project: 6372 HYBRID AI SENTINEL (Market Engine - Analytics Fixed)

class MarketSentinel:
    def __init__(self, db: SupremeDatabase, config, ai_engine=None):
        self.db = db
        self.config = config
        self.ai = ai_engine
        self.running = True
        self.alert_sound = utils.get_env("SOUND_ALERT_PATH", None)
        self.state_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "state.json")
        self.last_history_sync = {}
        self.last_notified_diffs = {}

    def _should_record_history(self, asset):
        now = time.time()
        if asset not in self.last_history_sync or now - self.last_history_sync[asset] >= 60:
            self.last_history_sync[asset] = now
            return True
        return False

    def start(self):
        utils.logger.info("Starting Binance WebSocket Streams...")
        threading.Thread(target=self._binance_ws_loop, daemon=True).start()

    async def start_async(self):
        utils.logger.info("Starting Market Observation Hub...")
        await asyncio.gather(
            self._dex_polling_loop(),
            self._onchain_polling_loop()
        )

    def _check_alerts(self, asset, price, diff_24h):
        # Always sync state.json for external tools
        if asset == "BTC": self.db.sync_state_json()

        asset_cfg = self.config.get("assets", {}).get(asset, {})
        thresholds = asset_cfg.get("thresholds", {})
        prev = self.db.get_asset_state(asset)
        prev_tier = prev.get("tier")

        # 1. Hourly Momentum (Delta Real-time Logic)
        p_1h = self.db.get_price_one_hour_ago(asset)
        if p_1h and p_1h > 0:
            diff_1h = ((price - p_1h) / p_1h) * 100
            last_diff = self.last_notified_diffs.get(asset, 0.0)
            delta = diff_1h - last_diff

            h_threshold = thresholds.get("hourly", 1.0)
            if abs(delta) >= h_threshold:
                utils.logger.info(f"Hourly Movement: {asset} {diff_1h:+.2f}% (Delta: {delta:+.2f}%)")

                emoji = "🟢" if delta > 0 else "🔴"
                direction = utils.get_locale("up") if delta > 0 else utils.get_locale("down")
                title = f"{emoji} {asset} {direction} {abs(delta):.2f}%"
                body = f"${price:,.4f}"
                utils.send_notification(title, body, sound_path=self.alert_sound)
                self.last_notified_diffs[asset] = diff_1h
        # 2. Alert & Tier Logic
        triggered_lvl = None
        
        # Check Spikes (Prioritas Tinggi ke Rendah)
        for spike in sorted(thresholds.get("spikes", []), key=lambda x: x['level'], reverse=True):
            if diff_24h >= spike['level']:
                triggered_lvl = spike['level']
                if prev_tier != triggered_lvl:
                    utils.send_notification(f"🚀 {spike.get('msg')}", f"Up: {diff_24h:.2f}%", sound_path=self.alert_sound)
                    self.db.record_paper_trade(asset, "SELL", price)
                break

        # Check Dips (Prioritas Rendah ke Tinggi)
        if triggered_lvl is None:
            for dip in sorted(thresholds.get("dips", []), key=lambda x: x['level']):
                if diff_24h <= dip['level']:
                    triggered_lvl = dip['level']
                    if prev_tier != triggered_lvl:
                        utils.send_notification(f"📉 {dip.get('msg')}", f"Down: {diff_24h:.2f}%", sound_path=self.alert_sound)
                        self.db.record_paper_trade(asset, "BUY", price)
                    break

        # 3. DB Sync & Auto-Recovery to STABIL (None)
        # Jika triggered_lvl tetap None, berarti harga masuk zona STABIL
        self.db.update_asset(asset, price, tier=triggered_lvl, change_24h=diff_24h)
        return triggered_lvl is not None

    def _binance_ws_loop(self):
        assets = self.config.get("assets", {})
        raw_symbols = [s["symbol"].upper() for a, s in assets.items() if s.get("symbol") and not s.get("dex")]
        if not raw_symbols: return
        stream_names = "/".join([f"{s.lower()}@ticker" for s in raw_symbols])
        
        def start_socket(base_url, name):
            url = f"{base_url}/stream?streams={stream_names}"
            def on_message(ws, message):
                try:
                    raw_data = json.loads(message)
                    data = raw_data.get('data', {})
                    sym = data.get('s')
                    price = float(data.get('c', 0))
                    change_24h = float(data.get('P', 0))
                    if price <= 0 or not sym: return 
                    asset_name = next((a for a, s in assets.items() if s.get("symbol") == sym), None)
                    if asset_name:
                        # Update DB with REAL change_24h
                        self.db.update_asset(asset_name, price, change_24h=change_24h)
                        self._check_alerts(asset_name, price, change_24h)
                        if self._should_record_history(asset_name):
                            self.db.record_price_history(asset_name, price)
                except Exception as e:
                    utils.logger.error(f"WS Msg Error ({name}): {e}")
            def on_error(ws, error): utils.logger.error(f"Binance {name} WS Error: {error}")
            def on_close(ws, c, m):
                if self.running: time.sleep(5); start_socket(base_url, name)
            utils.logger.info(f"Connecting to Binance {name} WebSocket...")
            ws = websocket.WebSocketApp(url, on_message=on_message, on_error=on_error, on_close=on_close)
            ws.run_forever()

        threading.Thread(target=start_socket, args=("wss://stream.binance.com:9443", "Spot"), daemon=True).start()
        threading.Thread(target=start_socket, args=("wss://fstream.binance.com", "Futures"), daemon=True).start()

    async def _onchain_polling_loop(self):
        while self.running:
            self.db.update_heartbeat("MARKET")
            try:
                assets = self.config.get("assets", {})
                for name, cfg in assets.items():
                    onchain = cfg.get("onchain") or {}
                    network = onchain.get("network")
                    if not network:
                        if name in ["ETH", "QUACK", "FHE"]: network = "ethereum"
                        elif name in ["SOL", "FART", "MOODENG"]: network = "solana"
                        elif name in ["BTC"]: network = "bitcoin"
                        elif name in ["EDGEN"]: network = "bsc"
                        elif name in ["KAITO", "HYPE"]: network = "base"
                        elif name in ["DOGE"]: network = "dogecoin"

                    if network == "bitcoin":
                        whale = await utils.fetch_btc_whale_tx_async()
                        if whale: self.db.update_asset(name, onchain_data={"unconfirmed": f"Fee:{whale['val']} sat/vB", "timestamp": time.time()})
                    elif network == "solana":
                        addr = onchain.get("address") or (cfg.get("dex") or {}).get("address")
                        if addr:
                            burst = await utils.fetch_solana_whale_burst_async(addr)
                            if burst: self.db.add_intel("ON-CHAIN", f"{name} Burst", f"Spontaneous Vol: ${burst['vol']:,.0f}")
                    elif network in ["ethereum", "base", "bsc"]:
                        gas = await utils.fetch_base_gas_async()
                        self.db.update_asset(name, onchain_data={"gas_gwei": gas, "timestamp": time.time()})
            except Exception as e:
                utils.logger.error(f"On-chain Engine Error: {e}")
            await asyncio.sleep(300)

    async def _dex_polling_loop(self):
        while self.running:
            try:
                assets = self.config.get("assets", {})
                for name, cfg in assets.items():
                    dex = cfg.get("dex")
                    query = dex.get("address") if dex else name
                    data = await utils.fetch_dex_price_async(query, asset_name=name, expected_sym=cfg.get("symbol"))
                    if data:
                        # 1. Tentukan Sentimen Whale (Rasio > 2.5x)
                        buys, sells = data.get("buys", 0), data.get("sells", 0)
                        sentiment = "neutral"
                        if buys > (sells * 2.5) and buys > 10: sentiment = "whale_buy"
                        elif sells > (buys * 2.5) and sells > 10: sentiment = "whale_sell"

                        # 2. Update DB dengan statistik & sentimen baru
                        self.db.update_asset(name, onchain_data={
                            "m5_activity": {"buys": buys, "sells": sells},
                            "sentiment": sentiment,
                            "timestamp": time.time()
                        }, change_24h=data.get("change_24h", 0))
                        
                        # Update DB with REAL change_24h from DEX
                        if dex:
                            self.db.update_asset(name, data["price_usd"], change_24h=data.get("change_24h", 0))
                            self._check_alerts(name, data["price_usd"], data.get("change_24h", 0))
                            if self._should_record_history(name):
                                self.db.record_price_history(name, data["price_usd"])
                    await asyncio.sleep(0.5)
            except Exception as e:
                utils.logger.error(f"DEX Loop Error: {e}")
            await asyncio.sleep(10) # Lebih agresif (10 detik) untuk koin DEX
