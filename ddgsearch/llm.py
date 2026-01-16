from ddgsearch.ddg import search_urls
from ddgsearch.scrape import scrape_web_page

async def llm_search(query: str,limit: int = 5) -> list[dict]|None:
    
    data = await search_urls(query, limit=limit, options=["pages"])
    pages = data.get("pages", [])

    if not pages:
        print("No se encontraron enlaces.")
        return

    results_with_content = await scrape_web_page(pages)

    if not results_with_content:
        print("❌ No se pudo extraer contenido útil de ninguna de las fuentes.")
        return

    return results_with_content 