import asyncio
import aiohttp
import trafilatura
import logging
import re
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

async def get_html(session: aiohttp.ClientSession, url: str) -> Optional[tuple[str, str]]:
    """Downloads HTML content or detects if it's a PDF.

    Args:
        session (aiohttp.ClientSession): The active HTTP session.
        url (str): The URL to download or verify.

    Returns:
        Optional[tuple[str, str]]: A tuple (content, content_type). 
        If it's a PDF, content will be "IS_PDF".
    """
    try:
        async with session.get(url, timeout=12) as response:
            if response.status != 200:
                return None
            
            content_type = response.headers.get('Content-Type', '').lower()
            
            # Detect PDF
            if 'application/pdf' in content_type:
                return "IS_PDF", content_type
                
            # Only allow HTML/XHTML for text scraping
            if 'text/html' not in content_type and 'application/xhtml+xml' not in content_type:
                return None
                
            return await response.text(), content_type
    except Exception:
        return None

def preprocess_html(html_content: str) -> str:
    """Pre-processes HTML using regex to preserve formulas before trafilatura extraction.

    Args:
        html_content (str): The raw HTML.

    Returns:
        str: Modified HTML with protected formulas.
    """
    if not html_content:
        return ""

    # 1. Wikipedia Math: Replace formula images with their LaTeX content (alt attribute)
    # Search for common math image patterns in wikis and other sites
    html_content = re.sub(
        r'<img[^>]*?class="[^"]*?math[^"]*?"[^>]*?alt="([^"]+)"[^>]*?>',
        r' <div>\n\n$$\1$$\n\n</div> ',
        html_content,
        flags=re.IGNORECASE
    )

    # 2. MathML / Annotations: Capture LaTeX representations inside <annotation> tags
    html_content = re.sub(
        r'<annotation[^>]*encoding="application/x-tex"[^>]*>(.*?)</annotation>',
        r' <span>$\1$</span> ',
        html_content,
        flags=re.DOTALL | re.IGNORECASE
    )

    # 3. Inline Code: Ensure <code> is not lost (some scrapers clean it poorly)
    # Wrap in a marker that trafilatura respects
    html_content = re.sub(
        r'<code>(.*?)</code>',
        r' <b>`\1`</b> ',
        html_content,
        flags=re.DOTALL | re.IGNORECASE
    )

    return html_content

def extract_content(url: str, html: str, output_format: str = "markdown") -> Optional[str]:
    """Extracts relevant content from HTML using trafilatura.

    Args:
        url (str): The URL for logging purposes.
        html (str): The raw HTML content.
        output_format (str): The output format (txt, markdown, etc.).

    Returns:
        Optional[str]: The extracted text or None.
    """
    if not html or len(html) < 100:
        return None
        
    try:
        # Pre-processing for formulas
        processed_html = preprocess_html(html)
        
        # Final extraction
        content = trafilatura.extract(
            processed_html, 
            output_format=output_format, 
            include_tables=True, 
            no_fallback=False
        )
        return content
    except Exception as e:
        logger.error(f"Error parsing {url}: {e}")
        return None

async def scrape_web_pages(pages: List[Dict], output_format: str = "markdown") -> List[Dict]:
    """Processes a list of pages and extracts their content safely.

    Args:
        pages (List[Dict]): List of dictionaries with the 'url' key.
        output_format (str): The extracted text format.

    Returns:
        List[Dict]: The list of pages with extracted content.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        # 1. Parallel download (Network-bound)
        download_tasks = [get_html(session, item['url']) for item in pages]
        results = await asyncio.gather(*download_tasks)
        
        # 2. Sequential extraction (CPU-bound)
        for page, result in zip(pages, results):
            if result:
                content_data, _ = result
                
                # If it's a PDF, assign the marker directly without extracting text
                if content_data == "IS_PDF":
                    page['content'] = "IS_PDF"
                else:
                    # Execute HTML content extraction
                    page['content'] = extract_content(page['url'], content_data, output_format)
            else:
                page['content'] = None
            
        return pages