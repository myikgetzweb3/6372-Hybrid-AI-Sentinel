import threading
import time
import asyncio
import utils
from core.database import SupremeDatabase

# --- DEVELOPER INFO ---
# Author: myikgetzweb3
# Project: 6372-Hybrid-AI-Sentinel (Intelligence Core)

class IntelligenceSentinel:
    def __init__(self, db: SupremeDatabase, config):
        self.db = db
        self.config = config
        self.running = True

    def start(self):
        # Synchronous entry point if needed
        pass

    async def start_async(self):
        await self._news_loop()

    async def _news_loop(self):
        while self.running:
            self.db.update_heartbeat("AI")
            try:
                sources = self.config.get("sources", {})
                # 1. Process EliZ & Socials
                await self._process_x_accounts(sources)
                await self._process_youtube_channels(sources)
                # 2. Process Trusted RSS (for MOODENG)
                await self._process_generic_rss(sources)
            except Exception as e:
                utils.logger.error(f"News Loop Error: {e}")
            await asyncio.sleep(300) # Check every 5 minutes

    async def _process_x_accounts(self, sources):
        instances = sources.get("nitter_instances", ["https://nitter.net"])
        rsshub_instances = ["https://rsshub.app", "https://rsshub.moeyy.cn"]
        for acc in sources.get("x_accounts", []):
            handle = acc.get("handle")
            if not handle: continue
            urls = [f"{nitter}/{handle}/rss" for nitter in instances[:2]]
            urls += [f"{hub}/twitter/user/{handle}" for hub in rsshub_instances]
            await self._fetch_and_analyze(urls, source_type="X")

    async def _process_youtube_channels(self, sources):
        for ch in sources.get("youtube", []):
            c_id = ch.get("channel_id")
            if c_id:
                url = f"https://www.youtube.com/feeds/videos.xml?channel_id={c_id}"
                await self._fetch_and_analyze([url], source_type="YT")

    async def _process_generic_rss(self, sources):
        for url in sources.get("rss_feeds", []):
            await self._fetch_and_analyze([url], source_type="RSS")

    async def _fetch_and_analyze(self, urls, source_type):
        tasks = [utils.fetch_rss_async(url) for url in urls]
        # We process as soon as we get results from ANY source for a specific account/feed
        results = await asyncio.gather(*tasks)
        
        all_entries = []
        for res in results:
            if res:
                all_entries.extend(res)
                break # Found valid RSS for this source set, move on

        for entry in all_entries:
            link = entry.get('link')
            if link and not self.db.is_already_seen(link):
                # Mark as seen IMMEDIATELY to prevent double processing while AI is thinking
                self.db.mark_as_seen(link)
                # Run analysis in a thread to keep the async event loop moving
                threading.Thread(target=self._analyze_signal, args=(entry.get('title', ''), link, source_type), daemon=True).start()

    def _analyze_signal(self, title, link, source_type, is_whale_event=False):
        # 1. Precise Detection
        title_l = title.lower()
        is_btc = any(kw in title_l for kw in ["btc", "bitcoin"])
        is_moodeng = any(kw in title_l for kw in ["moodeng", "hippo", "🦛"])
        
        # Check for other coins to avoid "leakage" from generic sources
        other_coins = ["eth", "ethereum", "solana", "sol", "doge", "hype", "kaito", "quack", "fhe", "edgen", "magic eden"]
        mentions_others = any(kw in title_l for kw in other_coins)

        priority_handles = [s.get("handle", "").lower() for s in self.config.get("sources", {}).get("x_accounts", []) if s.get("priority")]
        is_eliz_source = any(h in (link or "").lower() for h in priority_handles if h) or source_type == "ELIZ"
        
        is_technical_data = is_whale_event or source_type == "ON-CHAIN"

        # --- ABSOLUTE GATEKEEPER LOGIC ---
        should_process = False
        context = ""

        # RULE A: EliZ is Master. Process everything she says.
        if is_eliz_source:
            should_process = True
            context = "EliZ Alpha"
        
        # RULE B: MOODENG Global. Process news about Moodeng from anywhere.
        elif is_moodeng:
            # If it's a generic source and mostly talks about other coins, skip
            if mentions_others and not is_technical_data:
                # Only process if Moodeng is likely the focus (at the start of title)
                if not title_l.startswith("moodeng") and "🦛" not in title:
                    return 
            should_process = True
            context = "MOODENG"

        # RULE C: BTC Selective. Process only if EliZ (handled above) or raw On-chain.
        elif is_btc and is_technical_data:
            should_process = True
            context = "Bitcoin Intel"

        # RULE D: Everything else is BLOCKED.
        if not should_process:
            return 

        # 2. Local Analysis (Ollama) - SPONTANEOUS TACTICAL BRIEFING
        role = f"analis {context} senior"
        if is_technical_data:
            role = f"spesialis On-chain {context}"
        
        prompt_local = f"TUGAS PRIORITAS: Anda adalah {role} yang sedang memantau data blockchain live. Berikan deskripsi SPONTAN, INSTRUKSI AKSI TAJAM, dan dampak harga untuk data ini: '{title}'. Jawab langsung ke poin, maksimal 2 kalimat."
        ollama_res = utils.call_ollama(prompt_local)
        
        # 3. Synergy Check (Gemini) - STRATEGIC TRUTH VERIFICATION
        gemini_res = ""
        daily_quota = self.db.get_quota()
        quota_limit = int(utils.get_env("GEMINI_QUOTA_LIMIT", "1500"))

        if daily_quota < quota_limit:
            utils.logger.info(f"AI SYNERGY TRIGGERED ({context}): {title[:40]}...")
            prompt_online = f"URGENT {context}: Sebagai {role}, bedah secara teknis kejadian ini: {title}. Berikan deskripsi spontan tentang validitas dan potensi pergerakan pasar. Jawab 1 kalimat tegas."
            gemini_res = utils.call_gemini(prompt_online)
            self.db.increment_quota()

        # 4. Spontaneous Notification Dispatch
        notify_timeout = 60 
        
        if is_whale_event:
            title_final = f"🐋 [WHALE] {context.upper()} INTEL"
        else:
            title_final = f"💎 [SYNERGY] {context.upper()} ALPHA"
        
        # Combined spontaneous output
        spontaneous_report = f"{ollama_res}"
        if gemini_res:
            spontaneous_report += f"\n\n🌍 INTEL VERIFIED: {gemini_res}"
        
        utils.send_notification(title_final, spontaneous_report, timeout=notify_timeout)
        self.db.add_intel(source_type, title, spontaneous_report)

    def analyze_external_event(self, title, source_type="ON-CHAIN"):
        """Method to allow MarketSentinel to trigger AI Synergy for whales"""
        self._analyze_signal(title, "", source_type, is_whale_event=True)
