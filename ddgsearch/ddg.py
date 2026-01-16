import asyncio
import aiohttp
import re
import logging
import html
from urllib.parse import quote, urlparse, unquote
import random

logging.basicConfig(level=logging.INFO)

class DDGSearchEngine:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": "https://duckduckgo.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

    async def _get_vqd(self, session: aiohttp.ClientSession, query: str) -> str:
        url = f"https://duckduckgo.com/?q={quote(query)}&t=h_"
        try:
            async with session.get(url, timeout=5) as resp:
                text = await resp.text()
                match = re.search(r"vqd=([^&'\"]+)", text)
                if not match:
                    match = re.search(r'vqd\s*[:=]\s*\'([^\']+)\'', text)
                return match.group(1) if match else None
        except Exception:
            return None

    async def search_pages(self, session: aiohttp.ClientSession, query: str, limit: int = 5) -> list[dict]:
        url = f"https://duckduckgo.com/html/?q={quote(query)}"
        try:
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200: return []
                raw_html = await resp.text()
                
                pattern = re.compile(r'class="result__a" href=".*?uddg=([^"&]+).*?">(.*?)</a>', re.DOTALL)
                matches = pattern.findall(raw_html)
                
                results = []
                seen_domains = set()
                for raw_url, title in matches:
                    actual_url = unquote(raw_url)
                    if "duckduckgo.com/y.js" in actual_url: continue
                    
                    domain = urlparse(actual_url).netloc
                    if domain and domain not in seen_domains:
                        seen_domains.add(domain)
                        results.append({
                            "title": html.unescape(re.sub(r'<.*?>', '', title)).strip(),
                            "url": actual_url
                        })
                    if len(results) >= limit: break
                return results
        except Exception as e:
            logging.error(f"Error en páginas: {e}")
            return []

    async def _safe_json(self, resp):
        """Maneja de forma segura el parseo de JSON."""
        try:
            return await resp.json(content_type=None)
        except Exception:
            # Si falla, devolvemos un diccionario vacío para no romper el bucle
            return {}

    async def search_images(self, session: aiohttp.ClientSession, query: str, limit: int = 5) -> list[dict]:
        vqd = await self._get_vqd(session, query)
        if not vqd: return []
        
        await asyncio.sleep(random.uniform(0.3,0.7)) # Anti-block delay
        params = {"l": "wt-wt", "o": "json", "q": query, "vqd": vqd, "f": ",,,", "p": "1"}
        async with session.get("https://duckduckgo.com/i.js", params=params) as resp:
            data = await self._safe_json(resp)
            results = data.get("results", [])
            return [{"title": html.unescape(r.get("title", "")), "url": r.get("image", "")} for r in results[:limit]]

    async def search_videos(self, session: aiohttp.ClientSession, query: str, limit: int = 5) -> list[dict]:
        vqd = await self._get_vqd(session, query)
        if not vqd: return []
        
        await asyncio.sleep(random.uniform(0.3,0.7)) # Anti-block delay
        params = {"l": "wt-wt", "o": "json", "q": query, "vqd": vqd, "p": "1"}
        async with session.get("https://duckduckgo.com/v.js", params=params) as resp:
            data = await self._safe_json(resp)
            results = data.get("results", [])
            return [{
                "title": html.unescape(r.get("title", "")), 
                "url": r.get("content", ""), 
                "duration": r.get("duration", "N/A")
            } for r in results[:limit]]

async def search_urls(query: str,options:list[str] = [], limit: int = 10) -> dict[str, list[dict]]:

    if not options:
        options = ["pages", "images", "videos"]
    
    result_data = {}

    engine = DDGSearchEngine()
    async with aiohttp.ClientSession(headers=engine.headers, cookie_jar=aiohttp.CookieJar()) as session:
        # Ejecución secuencial controlada para evitar bloqueos
        for option in options:
            if option == "pages":
                result_data[option] = await engine.search_pages(session, query, limit)
            elif option == "images":
                result_data[option] = await engine.search_images(session, query, 2)
            elif option == "videos":
                result_data[option] = await engine.search_videos(session, query, 2)
        return result_data