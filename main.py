import asyncio
import os
from ddgsearch import llm_search

if __name__ == "__main__":
    query = "Python"

    results = asyncio.run(llm_search(query,limit=15))

    if results:
        os.makedirs("results", exist_ok=True)

        for result in results:

            title = result["title"]

            with open(f"results/{title}.md", "w", encoding="utf-8") as f:
                f.write(f"# {result['title']}\n\n")
                f.write(f"[{result['url']}]\n\n")
                f.write(result["content"])