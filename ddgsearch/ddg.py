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
    """DuckDuckGo search engine with /lite and HTML engines.

    This class handles interaction with DuckDuckGo to obtain results
    from pages, images, and videos without the need for an official API Key.
    """

    def __init__(self):
        """Initializes the search engine with standard headers."""
        from ddgsearch.utils import get_random_user_agent
        self.headers = {
            "User-Agent": get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "Referer": "https://lite.duckduckgo.com/",
            "Origin": "https://lite.duckduckgo.com",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
        }

    async def _get_vqd(self, session: aiohttp.ClientSession, query: str) -> Optional[str]:
        """Obtains the VQD token required for media searches in DDG."""
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

    async def _prewarm_session(self, session: aiohttp.ClientSession) -> None:
        """Pre-warms the session by visiting DDG Lite to establish session cookies."""
        try:
            async with session.get("https://lite.duckduckgo.com/lite/", timeout=5) as resp:
                await resp.read()
        except Exception as e:
            logger.debug(f"Pre-warm session note: {e}")

    async def search_pages_lite(self,
                                session: aiohttp.ClientSession,
                                query: str,
                                limit: int = 5,
                                time_range: Optional[str] = None,
                                region: Optional[str] = None) -> List[Dict]:
        """Searches for web pages using DuckDuckGo /lite endpoint (clean HTML, highly resilient).

        Args:
            session (aiohttp.ClientSession): The active HTTP session.
            query (str): The search query.
            limit (int): Maximum number of results to return.
            time_range (Optional[str]): Time filter ('d'=day, 'w'=week, 'm'=month, 'y'=year).
            region (Optional[str]): Regional filter (e.g. 'es-es', 'us-en', 'wt-wt').

        Returns:
            List[Dict]: List of results with 'title', 'url', and 'snippet'.
        """
        await self._prewarm_session(session)

        post_data = {"q": query}
        if time_range:
            post_data["df"] = time_range
        if region:
            post_data["kl"] = region

        url = "https://lite.duckduckgo.com/lite/"
        try:
            async with session.post(url, data=post_data, timeout=8) as resp:
                if resp.status != 200:
                    return []
                raw_html = await resp.text()

                if "anomaly" in raw_html.lower() and "result-link" not in raw_html:
                    logger.warning("DDG Lite returned bot anomaly challenge.")
                    return []

                # Find all result-link anchors and result-snippet table cells
                link_matches = re.findall(
                    r'<a\s+([^>]*class=[\'"]result-link[\'"][^>]*)>(.*?)</a>',
                    raw_html,
                    re.DOTALL | re.IGNORECASE
                )
                snippet_matches = re.findall(
                    r'<td[^>]+class=[\'"]result-snippet[\'"][^>]*>(.*?)</td>',
                    raw_html,
                    re.DOTALL | re.IGNORECASE
                )

                results = []
                for i in range(len(link_matches)):
                    attrs, raw_title = link_matches[i]
                    href_match = re.search(r'href=[\'"]([^\'"]+)[\'"]', attrs)
                    if not href_match:
                        continue

                    actual_url = href_match.group(1)
                    if "uddg=" in actual_url:
                        uddg_match = re.search(r'uddg=([^&]+)', actual_url)
                        if uddg_match:
                            actual_url = unquote(uddg_match.group(1))

                    if not actual_url.startswith("http"):
                        continue

                    domain = urlparse(actual_url).netloc
                    domain_count = sum(1 for r in results if urlparse(r["url"]).netloc == domain)
                    if domain and domain_count >= 2:
                        continue

                    title_text = html.unescape(re.sub(r'<.*?>', '', raw_title)).strip()
                    raw_snippet = snippet_matches[i] if i < len(snippet_matches) else ""
                    snippet_text = html.unescape(re.sub(r'<.*?>', '', raw_snippet)).strip()

                    results.append({
                        "title": title_text,
                        "url": actual_url,
                        "snippet": snippet_text
                    })

                    if len(results) >= limit:
                        break

                return results
        except Exception as e:
            logger.debug(f"Error in DDG Lite search: {e}")
            return []

    async def search_pages_html(self, session: aiohttp.ClientSession, query: str, limit: int = 5) -> List[Dict]:
        """Fallback search using DuckDuckGo standard HTML endpoint."""
        url = f"https://duckduckgo.com/html/?q={quote(query)}"
        try:
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    return []
                raw_html = await resp.text()

                blocks = raw_html.split("result__body")
                results = []

                for block in blocks[1:]:
                    url_match = re.search(r'class="result__a"\s+href=".*?uddg=([^"&]+)', block)
                    title_match = re.search(r'class="result__a"[^>]*>(.*?)</a>', block, re.DOTALL)
                    snippet_match = re.search(r'class="result__snippet"[^>]*>(.*?)</(?:a|div)>', block, re.DOTALL)

                    if url_match and title_match:
                        actual_url = unquote(url_match.group(1))
                        if "duckduckgo.com/y.js" in actual_url:
                            continue

                        domain = urlparse(actual_url).netloc
                        domain_count = sum(1 for r in results if urlparse(r["url"]).netloc == domain)
                        if domain and domain_count < 2:
                            title_text = html.unescape(re.sub(r'<.*?>', '', title_match.group(1))).strip()
                            snippet_text = ""
                            if snippet_match:
                                snippet_text = html.unescape(re.sub(r'<.*?>', '', snippet_match.group(1))).strip()

                            results.append({
                                "title": title_text,
                                "url": actual_url,
                                "snippet": snippet_text
                            })

                    if len(results) >= limit:
                        break
                return results
        except Exception as e:
            logger.error(f"Error in HTML fallback search: {e}")
            return []

    async def search_pages(self,
                           session: aiohttp.ClientSession,
                           query: str,
                           limit: int = 5,
                           time_range: Optional[str] = None,
                           region: Optional[str] = None) -> List[Dict]:
        """Searches for web pages with automatic /lite primary engine and HTML fallback."""
        # Primary: /lite (fast, clean, resilient)
        results = await self.search_pages_lite(session, query, limit=limit, time_range=time_range, region=region)
        if results:
            return results

        # Fallback: HTML endpoint
        logger.info("DDG Lite returned no results; falling back to HTML endpoint.")
        return await self.search_pages_html(session, query, limit=limit)

    async def _safe_json(self, resp: aiohttp.ClientResponse) -> Dict:
        """Safely parses JSON from an HTTP response."""
        try:
            return await resp.json(content_type=None)
        except Exception:
            return {}

    async def search_images(self, session: aiohttp.ClientSession, query: str, limit: int = 5) -> List[Dict]:
        """Searches for images in DuckDuckGo."""
        vqd = await self._get_vqd(session, query)
        if not vqd:
            return []

        await asyncio.sleep(random.uniform(0.3, 0.7))
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
        """Searches for videos in DuckDuckGo."""
        vqd = await self._get_vqd(session, query)
        if not vqd:
            return []

        await asyncio.sleep(random.uniform(0.3, 0.7))
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

async def search_urls(query: str,
                      options: Optional[List[str]] = None,
                      limit: int = 10,
                      time_range: Optional[str] = None,
                      region: Optional[str] = None) -> Dict[str, List[Dict]]:
    """High-level function to search for different media types in DDG.

    Args:
        query (str): The search query.
        options (Optional[List[str]]): Search types ["pages", "images", "videos"].
        limit (int): Base result limit per type.
        time_range (Optional[str]): Optional time filter ('d', 'w', 'm', 'y').
        region (Optional[str]): Optional region filter.

    Returns:
        Dict[str, List[Dict]]: Dictionary with organized results by type.
    """
    if options is None:
        options = ["pages", "images", "videos"]

    result_data = {}
    engine = DDGSearchEngine()

    async with aiohttp.ClientSession(headers=engine.headers, cookie_jar=aiohttp.CookieJar()) as session:
        for option in options:
            actual_limit = limit if option == "pages" else min(limit, 10)

            if option == "pages":
                result_data[option] = await engine.search_pages(
                    session, query, actual_limit, time_range=time_range, region=region
                )
            elif option == "images":
                result_data[option] = await engine.search_images(session, query, actual_limit)
            elif option == "videos":
                result_data[option] = await engine.search_videos(session, query, actual_limit)
        return result_data
