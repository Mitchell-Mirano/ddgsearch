import re
from typing import List, Dict, Optional, Union
from ddgsearch.ddg import search_urls
from ddgsearch.scrape import scrape_web_pages
from ddgsearch.metrics import quality_score, split_into_paragraphs

async def llm_web_search(query: str,
                          limit_urls: int = 10,
                          limit_pages: int = 2,
                          limit_images: int = 2,
                          limit_videos: int = 2,
                          output_format: str = "markdown",
                          min_page_text_lenght: int = 500,
                          max_page_text_lenght: int = 7500,
                          include_types: Optional[List[str]] = None
                          ) -> Dict[str, List[Dict]]:
    """Performs an integral web search optimized for LLMs.

    Searches and organizes results into categories based on requested types.

    Args:
        query (str): The search query.
        limit_urls (int): Maximum page URLs to evaluate for text/PDFs.
        limit_pages (int): Maximum web pages with content to return.
        limit_images (int): Maximum images to return.
        limit_videos (int): Maximum videos to return.
        output_format (str): Content format (txt or markdown).
        min_page_text_lenght (int): Minimum length to consider a page useful.
        max_page_text_lenght (int): Maximum length for extracted content per page base.
        include_types (List[str], optional): Types to include: ["pages", "pdfs", "images", "videos"].
                                           Defaults to all.

    Returns:
        Dict[str, List[Dict]]: Dictionary with keys 'pages', 'pdfs', 'images', 'videos'.
    """
    
    if include_types is None:
        include_types = ["pages", "pdfs", "images", "videos"]
    
    result_dict = {
        "pages": [],
        "pdfs": [],
        "images": [],
        "videos": []
    }

    # 1. Media Search (Images and Videos) - Original Query
    media_options = [opt for opt in ["images", "videos"] if opt in include_types]
    if media_options:
        # Request double results for relevance filtering margin
        media_results = await search_urls(query, limit=max(limit_images, limit_videos) * 2, options=media_options)
        
        query_words = set(re.sub(r'[^\w\s]', '', query.lower()).split())
        
        def calculate_media_score(title: str) -> float:
            if not title: return 0.0
            title_words = set(re.sub(r'[^\w\s]', '', title.lower()).split())
            matches = query_words.intersection(title_words)
            return len(matches) / len(query_words) if query_words else 0.0

        raw_images = media_results.get("images", [])
        for img in raw_images:
            img['relevance_score'] = calculate_media_score(img.get('title', ''))
        
        # Filter and sort images
        result_dict["images"] = sorted(
            [img for img in raw_images if img['relevance_score'] > 0 or not query_words],
            key=lambda x: x['relevance_score'], 
            reverse=True
        )[:limit_images]

        raw_videos = media_results.get("videos", [])
        for vid in raw_videos:
            vid['relevance_score'] = calculate_media_score(vid.get('title', ''))
            
        # Filter and sort videos
        result_dict["videos"] = sorted(
            [vid for vid in raw_videos if vid['relevance_score'] > 0 or not query_words],
            key=lambda x: x['relevance_score'], 
            reverse=True
        )[:limit_videos]

    # 2. Text and PDF Search
    if "pages" in include_types or "pdfs" in include_types:
        effective_query = query
        # If user searches exclusively for PDFs, we optimize the query
        if "pdfs" in include_types and "pages" not in include_types:
            if "filetype:pdf" not in query.lower():
                effective_query = f"{query} filetype:pdf"
        
        raw_pages = await search_urls(effective_query, limit=limit_urls, options=["pages"])
        pages_to_process = raw_pages.get("pages", [])[:limit_urls]
        
        if pages_to_process:
            # 3. Scrape and parse HTML and PDFs
            scraped_data = await scrape_web_pages(pages_to_process, output_format=output_format)
            
            # Track all found PDFs for metadata fallback
            all_found_pdfs = []
            for item in scraped_data:
                if item.get('is_pdf', False) or ".pdf" in item["url"].lower():
                    all_found_pdfs.append({
                        "title": item["title"],
                        "url": item["url"],
                        "type": "PDF",
                        "metadata": item.get("metadata", {})
                    })
            
            # 4. Paragraph Chunking and Selection
            all_paragraphs = []
            for item in scraped_data:
                content = item.get('content')
                
                # Fallback to search snippet if scraping failed or returned too little content
                if not content or len(content.strip()) < 100:
                    snippet = item.get('snippet')
                    if snippet:
                        content = f"[Search Snippet Fallback]: {snippet}"
                        
                if not content:
                    continue
                
                is_pdf = item.get('is_pdf', False) or ".pdf" in item["url"].lower()
                
                # Split content into paragraphs
                paragraphs = split_into_paragraphs(content, min_length=100)
                
                for p_idx, p in enumerate(paragraphs):
                    p_score = quality_score(p, query)
                    # Boost score if query words are in the title
                    if any(word.lower() in item['title'].lower() for word in query.split()):
                        p_score *= 1.2
                        
                    all_paragraphs.append({
                        "text": p,
                        "score": p_score,
                        "page_url": item["url"],
                        "page_title": item["title"],
                        "is_pdf": is_pdf,
                        "p_idx": p_idx
                    })

            # Sort all paragraphs by relevance/quality score descending
            sorted_paras = sorted(all_paragraphs, key=lambda x: x['score'], reverse=True)
            
            # Allocate paragraphs until the character budget quota is reached
            total_quota = limit_pages * max_page_text_lenght
            selected_paras = []
            for p in sorted_paras:
                p_len = len(p["text"])
                if total_quota - p_len < 0:
                    if total_quota >= 100:
                        p["text"] = p["text"][:total_quota]
                        selected_paras.append(p)
                    break
                selected_paras.append(p)
                total_quota -= p_len

            # 5. Group selected paragraphs back by page
            from collections import defaultdict
            pages_dict = defaultdict(list)
            pdfs_dict = defaultdict(list)
            
            for p in selected_paras:
                if p["is_pdf"]:
                    pdfs_dict[p["page_url"]].append(p)
                else:
                    pages_dict[p["page_url"]].append(p)

            # Assemble pages
            final_pages = []
            for url, paras in pages_dict.items():
                paras_sorted = sorted(paras, key=lambda x: x["p_idx"])
                assembled_content = "\n\n...\n\n" + "\n\n...\n\n".join([p["text"] for p in paras_sorted])
                max_score = max(p["score"] for p in paras)
                
                orig_item = next((item for item in scraped_data if item["url"] == url), {})
                
                final_pages.append({
                    "title": paras[0]["page_title"],
                    "url": url,
                    "score": max_score,
                    "content": assembled_content,
                    "metadata": orig_item.get("metadata", {})
                })
            
            result_dict["pages"] = sorted(final_pages, key=lambda x: x["score"], reverse=True)[:limit_pages]

            # Assemble PDFs
            final_pdfs = []
            for url, paras in pdfs_dict.items():
                paras_sorted = sorted(paras, key=lambda x: x["p_idx"])
                assembled_content = "\n\n...\n\n" + "\n\n...\n\n".join([p["text"] for p in paras_sorted])
                max_score = max(p["score"] for p in paras)
                
                orig_item = next((item for item in scraped_data if item["url"] == url), {})
                
                final_pdfs.append({
                    "title": paras[0]["page_title"],
                    "url": url,
                    "type": "PDF",
                    "score": max_score,
                    "content": assembled_content,
                    "metadata": orig_item.get("metadata", {})
                })

            # Merge final PDFs with all found PDFs metadata fallback
            pdf_map = {pdf["url"]: pdf for pdf in all_found_pdfs}
            for final_pdf in final_pdfs:
                pdf_map[final_pdf["url"]] = final_pdf
            
            result_dict["pdfs"] = list(pdf_map.values())[:2]

    return result_dict