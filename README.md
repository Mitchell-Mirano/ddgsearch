# DuckDuckGo Search for LLMs (ddgsearch)

A fast, resilient search engine and web scraping library designed to convert web results into clean, structured input for LLMs and AI agents (such as [Tesius](https://github.com/Mitchell-Mirano/Tesius)).

It features a decoupled architecture: an ultra-fast **DDG `/lite` radar** for immediate URL discovery, paired with a deep **content extraction and BM25Okapi ranking** pipeline for RAG contexts.

---

## 🚀 Key Features

- **Resilient Engine (DuckDuckGo `/lite` Primary)**: Uses DDG's clean HTML table interface with pre-warmed cookie sessions, avoiding bot challenges (`anomaly-modal / robot challenge`). Falls back to HTML endpoint if necessary.
- **Decoupled Architecture**: Retrieve instant links and snippets (`fetch_content=False`) in **< 800 ms**, or download and rank full content (`fetch_content=True`).
- **BM25Okapi Ranking & Stopword Filtering**: Built-in pure-Python BM25 ranking with bilingual (Spanish/English) stopword removal and bonuses for title and tabular/code/math matches.
- **Freshness & Regional Filters**: Native support for time ranges (`time_range="d"`, `"w"`, `"m"`, `"y"`) and regional settings (`region="es-es"`, `"wt-wt"`).
- **Specialized Search Modes**: Presets for `mode="academic"` (arXiv, ScienceDirect, academic papers) and `mode="code"` (GitHub, official documentation).
- **Smart Content Extraction**: Powered by `trafilatura` to extract clean Markdown while stripping ads, headers, and navigation menus.
- **Scientific & Technical Preservation**: Preserves mathematical formulas ($\LaTeX$) and formatted code blocks.
- **PDF Extraction**: Reads and parses PDF documents directly into Markdown with metadata via `pypdf`.

---

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

---

## 🛠️ Usage Examples

### ⚡ 1. Ultra-Fast Search (Links & Snippets Only, < 800ms)
Ideal for agents that only need URLs and previews, or that manage their own downstream scraping (like Tesius's `web_plugin`).

```python
from ddgsearch import llm_web_search

# Fast search without downloading full web pages
results = await llm_web_search(
    query="FastAPI background tasks best practices",
    limit_urls=5,
    fetch_content=False,
    include_types=["pages"]
)

for page in results["pages"]:
    print(f"[{page['title']}]({page['url']})")
    print(f"Snippet: {page['snippet']}\n")
```

### 🧠 2. Deep RAG Context with BM25 Ranking
Downloads, extracts and ranks paragraphs using **BM25Okapi** to build high-density context for LLMs.

```python
results = await llm_web_search(
    query="Explain Bell Theorem and quantum entanglement",
    limit_pages=2,
    fetch_content=True,
    include_types=["pages"]
)

for page in results["pages"]:
    print(f"Page: {page['title']} (Score: {page['score']})")
    print(page["content"])
```

### ⏱️ 3. Freshness Filter (Time Range)
Search for recent information from the past day, week, month, or year.

```python
# Search for releases or news from the past month
results = await llm_web_search(
    query="PyTorch 2.5 new features",
    time_range="m",   # 'd'=day, 'w'=week, 'm'=month, 'y'=year
    fetch_content=False
)
```

### 🔬 4. Academic & Scientific Research Mode
Automatically targets scientific repositories (arXiv, ScienceDirect, PDF papers) with preserved $\LaTeX$ formulas.

```python
results = await llm_web_search(
    query="Skyrmion lattice simulation Metropolis algorithm",
    mode="academic",
    include_types=["pages", "pdfs"],
    limit_pages=2
)
```

### 🎬 5. Multimedia Enrichment (Images & Videos)
Retrieve relevant images and videos scored against your query.

```python
results = await llm_web_search(
    query="Transformer self-attention architecture diagram",
    include_types=["images", "videos"],
    limit_images=3,
    limit_videos=2
)
```

---

## 📊 Configuration Parameters

| Parameter | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `query` | `str` | Your search query. | *(Required)* |
| `limit_urls` | `int` | Maximum URLs to retrieve in search stage. | `10` |
| `limit_pages` | `int` | Maximum web pages with content to return. | `2` |
| `fetch_content` | `bool` | If `False`, returns links/snippets immediately without downloading pages. | `True` |
| `time_range` | `str` | Time filter: `"d"` (day), `"w"` (week), `"m"` (month), `"y"` (year). | `None` |
| `region` | `str` | Regional filter (e.g. `"es-es"`, `"us-en"`, `"wt-wt"`). | `None` |
| `mode` | `str` | Search mode: `"general"`, `"academic"`, or `"code"`. | `"general"` |
| `include_types` | `list` | Types to include: `["pages", "pdfs", "images", "videos"]`. | `None` (All) |
| `max_page_text_lenght` | `int` | Character limit quota across pages. | `7500` |
| `output_format` | `str` | Output format: `"markdown"` or `"txt"`. | `"markdown"` |

---

## 🧪 Tests

Run the test suite with `uv`:

```bash
uv run pytest -o pythonpath=.
```

---

## ⚖️ License
MIT License.
