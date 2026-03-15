import asyncio
import aiohttp
import re
import logging
import html
import random
from urllib.parse import quote, urlparse, unquote
from typing import List, Dict, Optional

# Basic logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DDGSearchEngine:
    """DuckDuckGo search engine.

    This class handles interaction with DuckDuckGo to obtain results
    from pages, images, and videos without the need for an official API Key.
    """

    def __init__(self):
        """Initializes the search engine with standard headers."""
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": "https://duckduckgo.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

    async def _get_vqd(self, session: aiohttp.ClientSession, query: str) -> Optional[str]:
        """Obtains the VQD token required for searches in DDG.

        Args:
            session (aiohttp.ClientSession): The active HTTP session.
            query (str): The search query.

        Returns:
            Optional[str]: The VQD token or None if not found.
        """
        url = f"https://duckduckgo.com/?q={quote(query)}&t=h_"
        try:
            async with session.get(url, timeout=5) as resp:
                text = await resp.text()
                match = re.search(r"vqd=([^&'\"]+)", text)
                if not match:
                    match = re.search(r'vqd\s*[:=]\s*\'([^\']+)\'', text)
                return match.group(1) if match else None
        except Exception as e:
            logger.debug(f"Error obtaining VQD: {e}")
            return None

    async def search_pages(self, session: aiohttp.ClientSession, query: str, limit: int = 5) -> List[Dict]:
        """Searches for web pages in DuckDuckGo.

        Args:
            session (aiohttp.ClientSession): The active HTTP session.
            query (str): The search query.
            limit (int): Maximum number of results to return.

        Returns:
            List[Dict]: List of results with 'title' and 'url'.
        """
        url = f"https://duckduckgo.com/html/?q={quote(query)}"
        try:
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    return []
                raw_html = await resp.text()
                
                # Robust regex to capture titles and URLs
                pattern = re.compile(r'class="result__a" href=".*?uddg=([^"&]+).*?">(.*?)</a>', re.DOTALL)
                matches = pattern.findall(raw_html)
                
                results = []
                seen_domains = set()
                for raw_url, title in matches:
                    actual_url = unquote(raw_url)
                    if "duckduckgo.com/y.js" in actual_url:
                        continue
                    
                    domain = urlparse(actual_url).netloc
                    if domain and domain not in seen_domains:
                        seen_domains.add(domain)
                        results.append({
                            "title": html.unescape(re.sub(r'<.*?>', '', title)).strip(),
                            "url": actual_url
                        })
                    if len(results) >= limit:
                        break
                return results
        except Exception as e:
            logger.error(f"Error in page search: {e}")
            return []

    async def _safe_json(self, resp: aiohttp.ClientResponse) -> Dict:
        """Safely parses JSON from an HTTP response.

        Args:
            resp (aiohttp.ClientResponse): The aiohttp response object.

        Returns:
            Dict: The JSON content or an empty dictionary if it fails.
        """
        try:
            return await resp.json(content_type=None)
        except Exception:
            return {}

    async def search_images(self, session: aiohttp.ClientSession, query: str, limit: int = 5) -> List[Dict]:
        """Searches for images in DuckDuckGo.

        Args:
            session (aiohttp.ClientSession): The active HTTP session.
            query (str): The search query.
            limit (int): Maximum number of results.

        Returns:
            List[Dict]: List of images with 'title' and 'url'.
        """
        vqd = await self._get_vqd(session, query)
        if not vqd:
            return []
        
        await asyncio.sleep(random.uniform(0.3, 0.7))  # Anti-block
        params = {"l": "wt-wt", "o": "json", "q": query, "vqd": vqd, "f": ",,,", "p": "1"}
        try:
            async with session.get("https://duckduckgo.com/i.js", params=params) as resp:
                data = await self._safe_json(resp)
                results = data.get("results", [])
                return [{"title": html.unescape(r.get("title", "")), "url": r.get("image", "")} for r in results[:limit]]
        except Exception as e:
            logger.error(f"Error in image search: {e}")
            return []

    async def search_videos(self, session: aiohttp.ClientSession, query: str, limit: int = 5) -> List[Dict]:
        """Searches for videos in DuckDuckGo.

        Args:
            session (aiohttp.ClientSession): The active HTTP session.
            query (str): The search query.
            limit (int): Maximum number of results.

        Returns:
            List[Dict]: List of videos with 'title', 'url', and 'duration'.
        """
        vqd = await self._get_vqd(session, query)
        if not vqd:
            return []
        
        await asyncio.sleep(random.uniform(0.3, 0.7))  # Anti-block
        params = {"l": "wt-wt", "o": "json", "q": query, "vqd": vqd, "p": "1"}
        try:
            async with session.get("https://duckduckgo.com/v.js", params=params) as resp:
                data = await self._safe_json(resp)
                results = data.get("results", [])
                return [{
                    "title": html.unescape(r.get("title", "")), 
                    "url": r.get("content", ""), 
                    "duration": r.get("duration", "N/A")
                } for r in results[:limit]]
        except Exception as e:
            logger.error(f"Error in video search: {e}")
            return []

async def search_urls(query: str, options: Optional[List[str]] = None, limit: int = 10) -> Dict[str, List[Dict]]:
    """High-level function to search for different media types in DDG.

    Args:
        query (str): The search query.
        options (Optional[List[str]]): Search types ["pages", "images", "videos"].
        limit (int): Base result limit per type.

    Returns:
        Dict[str, List[Dict]]: Dictionary with organized results by type.
            - pages: [{'title': str, 'url': str}]
            - images: [{'title': str, 'url': str}]
            - videos: [{'title': str, 'url': str, 'duration': str}]
    """
    if options is None:
        options = ["pages", "images", "videos"]
    
    result_data = {}
    engine = DDGSearchEngine()
    
    async with aiohttp.ClientSession(headers=engine.headers, cookie_jar=aiohttp.CookieJar()) as session:
        for option in options:
            # For pages we usually want more overhead for later filtering
            actual_limit = limit if option == "pages" else min(limit, 10)
            
            if option == "pages":
                result_data[option] = await engine.search_pages(session, query, actual_limit)
            elif option == "images":
                result_data[option] = await engine.search_images(session, query, actual_limit)
            elif option == "videos":
                result_data[option] = await engine.search_videos(session, query, actual_limit)
        return result_data