import asyncio
import aiohttp
import trafilatura

async def fetch_and_clean_content(session: aiohttp.ClientSession, url: str) -> str:
    """
    Descarga una URL y utiliza Trafilatura para extraer el contenido.
    Retorna None si el contenido es irrelevante o hay error.
    """
    try:
        async with session.get(url, timeout=12) as response:
            if response.status != 200:
                return None
            
            raw_html = await response.text()
            
            # Ejecución en executor para no bloquear el loop
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(
                None, 
                lambda: trafilatura.extract(
                    raw_html,
                    output_format='markdown',
                    include_tables=True,
                    no_fallback=False
                )
            )
            
            # Validamos que el contenido sea sustancial (mínimo 200 caracteres para ser útil)
            if content and len(content.strip()) > 200:
                return content.strip()
            return None
            
    except Exception:
        return None

async def scrape_web_page(results_list: list[dict]):
    """Procesa y filtra resultados, descartando los fallidos."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = [fetch_and_clean_content(session, item['url']) for item in results_list]
        contents = await asyncio.gather(*tasks)
        
        final_results = []
        for i, content in enumerate(contents):
            # SOLO agregamos a la lista final si hay contenido real
            if content:
                results_list[i]['content'] = content
                final_results.append(results_list[i])
            
        return final_results