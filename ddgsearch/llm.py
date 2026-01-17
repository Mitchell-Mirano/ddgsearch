import re
from ddgsearch.ddg import search_urls
from ddgsearch.scrape import scrape_web_pages
from ddgsearch.metrics import entropy

async def llm_web_search(query: str,
                          limit_urls: int = 10,
                          limit_pages: int = 3,
                          output_format: str = "txt",
                          min_page_text_lenght: int = 200,
                          max_page_text_lenght: int = 2000
                          ) -> list[dict]|None:
    
    fuentes = await search_urls(query, limit=limit_urls, options=["pages"])
    pages = fuentes.get("pages", [])

    if not pages:
        print("No se encontraron enlaces.")
        return

    scraped_pages = await scrape_web_pages(pages, output_format=output_format)

    final_results = []
    
    for result in scraped_pages:
        if result['content'] and len(result['content']) > min_page_text_lenght:
            result['content'] = result['content'].strip()
            result['score'] = entropy(result['content'])
            if query.lower() in result['title'].lower():
                result['score'] += 1
            result['content'] = result['content'] if len(result['content']) < max_page_text_lenght else result['content'][:max_page_text_lenght]
            final_results.append(result)

    final_results = sorted(final_results, key=lambda x: x['score'], reverse=True)[:limit_pages]

    return final_results