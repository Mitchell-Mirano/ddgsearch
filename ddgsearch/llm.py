import re
from typing import List, Dict, Optional, Union
from ddgsearch.ddg import search_urls
from ddgsearch.scrape import scrape_web_pages
from ddgsearch.metrics import quality_score

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
            # 3. Scrape and separate HTML from PDFs
            scraped_data = await scrape_web_pages(pages_to_process, output_format=output_format)
            
            temp_pages = []
            for item in scraped_data:
                content = item.get('content')
                
                # Case A: It's a PDF
                if content == "IS_PDF":
                    if "pdfs" in include_types:
                        result_dict["pdfs"].append({
                            "title": item["title"],
                            "url": item["url"],
                            "type": "PDF"
                        })
                    continue
                    
                # Case B: Processable web content
                if "pages" in include_types and content and len(content) > min_page_text_lenght:
                    content = content.strip()
                    score = quality_score(content, query)
                    if any(word.lower() in item['title'].lower() for word in query.split()):
                        score *= 1.2
                    
                    item['score'] = score
                    item['content'] = content # Save all for now to allocate quota later
                    temp_pages.append(item)

            # 4. Dynamic Text Quota Allocation
            # Sort by score for better page priority
            sorted_candidates = sorted(temp_pages, key=lambda x: x['score'], reverse=True)[:limit_pages]
            
            total_quota = limit_pages * max_page_text_lenght
            pages_with_allocated_content = []
            
            for page in sorted_candidates:
                if total_quota <= 0:
                    break
                
                content = page['content']
                # If page fits in remaining quota, take it all
                # If larger, take what is left of the quota
                take_length = min(len(content), total_quota)
                page['content'] = content[:take_length]
                total_quota -= take_length
                
                if take_length >= min_page_text_lenght:
                    pages_with_allocated_content.append(page)

            result_dict["pages"] = pages_with_allocated_content
            # Limit PDFs
            result_dict["pdfs"] = result_dict["pdfs"][:2]

    return result_dict