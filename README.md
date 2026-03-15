# DuckDuckGo Search for LLMs (ddgsearch)

A specialized search engine library designed to convert web results into clean, structured input for LLMs. It handles web page scraping, formula preservation ($\LaTeX$), source code extraction, and multi-media resource organization.

## 🚀 Key Features

-   **Comprehensive Search**: Retrieve web pages, PDFs, images, and videos in a single call.
-   **Smart Content Extraction**: Powered by `trafilatura` to extract the main content while removing ads and clutter.
-   **Scientific & Technical Support**: Preserves mathematical formulas ($\LaTeX$) and code blocks with syntax highlighting.
-   **Relevance-Based Multimedia**: Images and videos are ranked using a `relevance_score` based on your query.
-   **Dynamic Token/Character Quota**: Intelligently allocates a total character budget across the most relevant results.
-   **Highly Flexible**: Choose exactly which types of content to include to optimize for speed and performance.
-   **Lightweight**: No heavy DOM dependencies; uses optimized Regex for scientific pre-processing.

## 📦 Installation

### From Source
```bash
# Using uv (recommended)
uv pip install -e .

# Using standard pip
pip install -e .
```

### From GitHub
```bash
# Using uv
uv add git+https://github.com/Mitchell-Mirano/ddgsearch.git

# Using pip
pip install git+https://github.com/Mitchell-Mirano/ddgsearch.git
```

## 🛠️ Usage Examples

### 🧠 1. RAG Context Preparation
Perfect for retrieving dense, clean text to feed into an LLM.

```python
from ddgsearch import llm_web_search

# Get a large amount of text from a single high-quality source
results = await llm_web_search(
    query="Explain the Bell Theorem and its implications",
    include_types=["pages"],
    limit_pages=1,
    max_page_text_lenght=15000 
)

context = results["pages"][0]["content"]
```

### 🔬 2. Technical Research (PDFs & Formulas)
Search for papers and mathematical explanations with preserved $\LaTeX$ syntax.

```python
results = await llm_web_search(
    query="Schrödinger equation derivatives",
    include_types=["pages", "pdfs"],
    limit_urls=10 
)

# Mathematical formulas will look like $$ \frac{-\hbar^2}{2m} ... $$
print(f"PDFs found: {len(results['pdfs'])}")
```

### 🎬 3. Multimedia Enrichment
Retrieve highly relevant images and videos with scoring verification.

```python
results = await llm_web_search(
    query="Transformer architecture diagram",
    include_types=["images", "videos"],
    limit_images=3,
    limit_videos=2
)

for img in results["images"]:
    print(f"Image score ({img['relevance_score']}): {img['url']}")
```

### 💻 4. Code Extraction
Automatically wraps source code in triple backticks for easy LLM parsing.

```python
results = await llm_web_search(
    query="Quicksort implementation in Python",
    include_types=["pages"],
    limit_pages=1
)
```

## 📊 Configuration

| Parameter | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `query` | `str` | Your search query. | (Required) |
| `limit_pages` | `int` | Max number of web pages to return. | `2` |
| `limit_images` | `int` | Max number of images. | `2` |
| `limit_videos` | `int` | Max number of videos. | `2` |
| `include_types` | `list` | Types to include: `["pages", "pdfs", "images", "videos"]`. | `None` (All) |
| `max_page_text_lenght` | `int` | Total character limit quota across pages. | `7500` |
| `output_format` | `str` | Output format: `"markdown"` or `"txt"`. | `"markdown"` |

## 🧪 Tests

```bash
uv run pytest tests/test_search.py
```

## ⚖️ License
MIT License.