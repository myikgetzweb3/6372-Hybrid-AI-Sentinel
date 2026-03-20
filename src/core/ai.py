import threading
import time
import asyncio
import utils
from core.database import SupremeDatabase

# --- DEVELOPER INFO ---
# Author: myikgetzweb3
# Project: 6372-Hybrid-AI-Sentinel (Intelligence Core - Pure Output v2)

class IntelligenceSentinel:
    def __init__(self, db: SupremeDatabase, config):
        self.db = db
        self.config = config
        self.running = True

    def start(self):
        pass

    async def start_async(self):
        await self._news_loop()

    async def _news_loop(self):
        while self.running:
            self.db.update_heartbeat("AI")
            try:
                sources = self.config.get("sources", {})
                await self._process_x_accounts(sources)
                await self._process_youtube_channels(sources)
                await self._process_generic_rss(sources)
            except Exception as e:
                utils.logger.error(f"News Loop Error: {e}")
            await asyncio.sleep(300)

    async def _process_x_accounts(self, sources):
        instances = sources.get("nitter_instances", ["https://nitter.net"])
        for acc in sources.get("x_accounts", []):
            handle = acc.get("handle")
            name = acc.get("name", handle)
            if not handle: continue
            urls = [f"{inst}/{handle}/rss" for inst in instances[:2]]
            # Pass specific name like 'X: EliZ Alpha'
            await self._fetch_and_analyze(urls, source_type=f"X: {name}")

    async def _process_youtube_channels(self, sources):
        for ch in sources.get("youtube", []):
            c_id = ch.get("channel_id")
            name = ch.get("name", "YouTube")
            if c_id:
                url = f"https://www.youtube.com/feeds/videos.xml?channel_id={c_id}"
                # Pass specific name like 'YT: EliZ Alpha'
                await self._fetch_and_analyze([url], source_type=f"YT: {name}")

    async def _process_generic_rss(self, sources):
        for feed in sources.get("rss_feeds", []):
            url = feed if isinstance(feed, str) else feed.get("url")
            name = "RSS" if isinstance(feed, str) else feed.get("name", "News")
            if url:
                await self._fetch_and_analyze([url], source_type=f"RSS: {name}")

    async def _fetch_and_analyze(self, urls, source_type):
        tasks = [utils.fetch_rss_async(url) for url in urls]
        results = await asyncio.gather(*tasks)
        all_entries = []
        for res in results:
            if res: all_entries.extend(res); break

        for entry in all_entries:
            link = entry.get('link')
            if link and not self.db.is_already_seen(link):
                self.db.mark_as_seen(link)
                threading.Thread(target=self._analyze_signal, args=(entry.get('title', ''), link, source_type), daemon=True).start()

    def _analyze_signal(self, title, link, source_type, is_whale_event=False):
        title_l = title.lower()
        is_btc = any(kw in title_l for kw in ["btc", "bitcoin"])
        is_moodeng = any(kw in title_l for kw in ["moodeng", "hippo", "🦛"])
        is_eliz_source = (source_type == "X") 
        
        context = "Market"
        if is_btc: context = "Bitcoin"
        elif is_moodeng: context = "MOODENG"

        should_process = is_whale_event or is_btc or is_moodeng
        if not should_process: return 

        # 1. Local Tactical Decoding (Ollama)
        prompt_local = self.config.get("ai_prompts", {}).get("local", "").replace("{text}", title)
        ollama_res = utils.call_ollama(prompt_local)
        
        # 2. Strategic Synergy (Gemini)
        gemini_res = ""
        daily_quota = self.db.get_quota()
        quota_limit = int(utils.get_env("GEMINI_QUOTA_LIMIT", "1500"))

        if daily_quota < quota_limit:
            utils.logger.info(f"AI SYNERGY TRIGGERED ({context}): {title[:40]}...")
            prompt_online = self.config.get("ai_prompts", {}).get("online", "").replace("{text}", title)
            gemini_res = utils.call_gemini(prompt_online)
            self.db.increment_quota()

        # 3. Formulate PURE Output (No system prompts)
        if is_whale_event:
            title_final = f"🐋 [WHALE] {context.upper()} INTEL"
        else:
            title_final = f"💎 [SYNERGY] {context.upper()} ALPHA"
        
        # Clean analysis message
        final_analysis = f"{ollama_res}"
        if gemini_res:
            final_analysis += f"\n\n🌍 VERIFIKASI INTEL: {gemini_res}"
        
        # Dispatch Notification & Store to DB
        utils.send_notification(title_final, final_analysis, timeout=60)
        self.db.add_intel(source_type, title, final_analysis)

    def analyze_external_event(self, title, source_type="ON-CHAIN"):
        """Method to allow MarketSentinel to trigger AI Synergy for whales"""
        self._analyze_signal(title, "", source_type, is_whale_event=True)
