import asyncio
import os
import json
from ddgsearch import llm_web_search

async def main():
    query = "Advantages of Python for AI and Data Science"
    print(f"Searching resources for: {query}...\n")

    # Perform a general search (includes all types by default)
    # Default output_format is now 'markdown'
    results = await llm_web_search(
        query,
        limit_pages=2,
        limit_images=2,
        limit_videos=2
    )

    # Create results directory
    os.makedirs("results", exist_ok=True)

    # 1. Save Web Pages (Markdown)
    print(f"Web pages found: {len(results['pages'])}")
    for i, page in enumerate(results["pages"]):
        filename = f"results/web_page_{i+1}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {page['title']}\n\n")
            f.write(f"URL: {page['url']}\n")
            f.write(f"Relevance Score: {page['score']:.2f}\n\n")
            f.write(page['content'])

    # 2. Save summary of other resources (PDFs, Images, Videos)
    summary_file = "results/search_summary.json"
    summary = {
        "query": query,
        "results_stats": {
            "web_pages": len(results["pages"]),
            "pdfs": len(results["pdfs"]),
            "images": len(results["images"]),
            "videos": len(results["videos"])
        },
        "pdfs": results["pdfs"],
        "images": results["images"],
        "videos": results["videos"]
    }
    
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4, ensure_ascii=False)
    
    print(f"PDFs: {len(results['pdfs'])}")
    print(f"Images: {len(results['images'])}")
    print(f"Videos: {len(results['videos'])}")
    print(f"\nProcess completed. Check the 'results/' folder.")

if __name__ == "__main__":
    asyncio.run(main())