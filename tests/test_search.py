import pytest
from ddgsearch import llm_web_search, BM25Okapi
from ddgsearch.metrics import tokenize

def test_bm25_ranking_and_stopwords():
    """Unit test for BM25Okapi and stopword filtering."""
    doc1 = "Python es un lenguaje de programación interpretado y de alto nivel para ciencia de datos."
    doc2 = "La receta de cocina para hacer pan requiere harina, levadura y agua tibia."
    doc3 = "Programación avanzada en Python con librerías para aprendizaje automático y redes neuronales."

    corpus = [tokenize(d, remove_stopwords=True) for d in [doc1, doc2, doc3]]
    bm25 = BM25Okapi(corpus)

    query = "aprender programación en Python"
    q_tokens = tokenize(query, remove_stopwords=True)
    scores = bm25.get_scores(q_tokens)

    # doc1 and doc3 must have significantly higher scores than doc2 (recipe)
    assert scores[0] > scores[1]
    assert scores[2] > scores[1]

@pytest.mark.asyncio
async def test_search_only_fast():
    """Test fast search without downloading pages (fetch_content=False)."""
    query = "FastAPI web framework"
    results = await llm_web_search(query, limit_urls=3, fetch_content=False, include_types=["pages"])

    assert "pages" in results
    assert len(results["pages"]) > 0
    first = results["pages"][0]
    assert "url" in first
    assert "title" in first
    assert "snippet" in first
    assert first["url"].startswith("http")
    # Verify content was not scraped in fast search
    assert "content" not in first

@pytest.mark.asyncio
async def test_only_pages():
    """Test searching exclusively for web pages."""
    query = "Python programming"
    results = await llm_web_search(query, include_types=["pages"], limit_pages=2)

    assert "pages" in results
    assert len(results["pages"]) <= 2
    assert len(results["pdfs"]) == 0
    assert len(results["images"]) == 0
    assert len(results["videos"]) == 0

    if len(results["pages"]) > 0:
        assert results["pages"][0]["content"] is not None
        assert "score" in results["pages"][0]

@pytest.mark.asyncio
async def test_only_pdfs():
    """Test searching exclusively for PDFs (dynamic query optimization)."""
    query = "attention is all you need"
    results = await llm_web_search(query, include_types=["pdfs"], limit_urls=5)

    assert "pdfs" in results
    assert len(results["pages"]) == 0
    assert len(results["images"]) == 0
    assert len(results["videos"]) == 0

    if len(results["pdfs"]) > 0:
        pdf = results["pdfs"][0]
        assert "content" in pdf
        assert pdf["content"] != "IS_PDF"
        assert len(pdf["content"]) > 50

@pytest.mark.asyncio
async def test_only_media():
    """Test searching for images and videos only."""
    query = "cat memes"
    results = await llm_web_search(query, include_types=["images", "videos"], limit_images=2, limit_videos=2)

    assert len(results["pages"]) == 0
    assert len(results["pdfs"]) == 0
    assert "images" in results
    assert "videos" in results
    assert len(results["images"]) <= 2
    assert len(results["videos"]) <= 2

@pytest.mark.asyncio
async def test_all_types():
    """Test searching for all content types (default behavior)."""
    query = "machine learning tutorial"
    results = await llm_web_search(query, limit_pages=1, limit_images=1, limit_videos=1)

    expected_keys = {"pages", "pdfs", "images", "videos"}
    assert set(results.keys()) == expected_keys
    assert len(results["pages"]) <= 1
    assert len(results["images"]) <= 1
    assert len(results["videos"]) <= 1

@pytest.mark.asyncio
async def test_metadata_and_fallback():
    """Test that metadata is extracted and snippet fallback works."""
    query = "Advantages of Python for AI and Data Science"
    results = await llm_web_search(query, include_types=["pages"], limit_pages=2)

    assert "pages" in results
    if len(results["pages"]) > 0:
        page = results["pages"][0]
        assert "metadata" in page
        assert isinstance(page["metadata"], dict)
        assert "content" in page
        assert page["content"] is not None
        assert len(page["content"]) > 0
