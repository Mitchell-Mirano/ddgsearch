import asyncio
import aiohttp
import trafilatura
import logging
import re
from typing import List, Dict, Optional, Union

logger = logging.getLogger(__name__)

async def get_html(session: aiohttp.ClientSession, url: str) -> Optional[tuple[Union[str, bytes], str]]:
    """Downloads HTML content or detects if it's a PDF.

    Args:
        session (aiohttp.ClientSession): The active HTTP session.
        url (str): The URL to download or verify.

    Returns:
        Optional[tuple[Union[str, bytes], str]]: A tuple (content, content_type). 
        If it's a PDF, content will be raw bytes.
    """
    try:
        async with session.get(url, timeout=12) as response:
            if response.status != 200:
                return None
            
            content_type = response.headers.get('Content-Type', '').lower()
            
            # Detect PDF
            if 'application/pdf' in content_type or url.lower().endswith('.pdf'):
                return await response.read(), 'application/pdf'
                
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

import io
import pypdf

def extract_pdf_content_with_meta(pdf_bytes: bytes) -> tuple[Optional[str], dict]:
    """Extracts text content and metadata from PDF bytes using pypdf.

    Args:
        pdf_bytes (bytes): The raw PDF file bytes.

    Returns:
        tuple[Optional[str], dict]: (Extracted text content, metadata dict).
    """
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
                
        meta = {}
        try:
            pm = reader.metadata
            if pm:
                meta = {
                    "title": pm.get("/Title") or pm.title,
                    "author": pm.get("/Author") or pm.author,
                    "description": pm.get("/Subject") or pm.subject,
                    "date": pm.get("/CreationDate") or (pm.creation_date.isoformat() if pm.creation_date else None),
                    "sitename": "PDF Document"
                }
                # Filter out None/empty values
                meta = {k: str(v) for k, v in meta.items() if v}
        except Exception:
            pass
            
        return "\n\n".join(text_parts) if text_parts else "", meta
    except Exception as e:
        logger.error(f"Error parsing PDF bytes: {e}")
        return None, {}

async def scrape_web_pages(pages: List[Dict], output_format: str = "markdown") -> List[Dict]:
    """Processes a list of pages and extracts their content safely.

    Args:
        pages (List[Dict]): List of dictionaries with the 'url' key.
        output_format (str): The extracted text format.

    Returns:
        List[Dict]: The list of pages with extracted content and metadata.
    """
    from ddgsearch.utils import get_random_user_agent
    headers = {
        "User-Agent": get_random_user_agent()
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        # 1. Parallel download (Network-bound)
        download_tasks = [get_html(session, item['url']) for item in pages]
        results = await asyncio.gather(*download_tasks)
        
        # 2. Sequential extraction (CPU-bound)
        for page, result in zip(pages, results):
            page['metadata'] = {}
            if result:
                content_data, content_type = result
                
                # If it's a PDF, extract its text content and metadata
                if 'application/pdf' in content_type:
                    text, meta = extract_pdf_content_with_meta(content_data)
                    page['content'] = text
                    page['metadata'] = meta
                    page['is_pdf'] = True
                else:
                    # Execute HTML content extraction
                    page['content'] = extract_content(page['url'], content_data, output_format)
                    
                    # Extract HTML metadata
                    from trafilatura.metadata import extract_metadata
                    try:
                        meta = extract_metadata(content_data)
                        if meta:
                            page['metadata'] = {
                                "title": meta.title,
                                "author": meta.author,
                                "date": meta.date,
                                "description": meta.description,
                                "sitename": meta.sitename
                            }
                            # Clean out None values
                            page['metadata'] = {k: v for k, v in page['metadata'].items() if v}
                    except Exception:
                        pass
            else:
                page['content'] = None
            
        return pages