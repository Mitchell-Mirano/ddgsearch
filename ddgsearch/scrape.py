import trafilatura.feeds
import re
import asyncio
import aiohttp
import trafilatura

async def get_html(session: aiohttp.ClientSession, url: str) -> str|None:
    """
    Descarga una URL y utiliza Trafilatura para extraer el contenido.
    Retorna None si el contenido es irrelevante o hay error.
    """
    try:
        async with session.get(url, timeout=12) as response:
            if response.status != 200:
                return None
            
            raw_html = await response.text()
            
            # # Ejecución en executor para no bloquear el loop
            # loop = asyncio.get_event_loop()
            # content = await loop.run_in_executor(
            #     None, 
            #     lambda: trafilatura.extract(
            #         raw_html,
            #         output_format='markdown',
            #         include_tables=True,
            #         no_fallback=False
            #     )
            # )
            
            # # Validamos que el contenido sea sustancial (mínimo 200 caracteres para ser útil)
            # if content and len(content.strip()) > 200:
            #     return content.strip()
            # return None
            
            return raw_html
    except Exception:
        return None

async def scrape_web_pages(pages: list[dict],output_format: str = "txt") -> list[dict]:
    """Procesa y filtra resultados, descartando los fallidos."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = [get_html(session, item['url']) for item in pages]
        htmls = await asyncio.gather(*tasks)
    

        for page,html in zip(pages,htmls):
            page['content'] = trafilatura.extract(html, 
                                                  output_format=output_format, 
                                                  include_tables=True, 
                                                  no_fallback=False)
            
        return pages