import asyncio
import os
from ddgsearch import llm_text_search

if __name__ == "__main__":

    outout_format = "markdown"
    query = "Python"

    results = asyncio.run(llm_text_search(query,
                                                                                    limit_urls=15,
                                                                                    limit_pages=2,
                                                                                    output_format=outout_format,
                                                                                    min_length=200,
                                                                                    max_length=7500
                                                                                    ))

    if results:
        os.makedirs("results", exist_ok=True)

        for result in results:
            
            score = result["entropy"]
            title = result["title"]

            with open(f"results/[{score:.2f}]{title}.md", "w", encoding="utf-8") as f:
                f.write(f"# {result['title']}\n\n")
                f.write(f"## URL: {result['url']}\n\n")
                f.write(f"## Score: {score:.2f}\n\n")
                f.write(result["content"])