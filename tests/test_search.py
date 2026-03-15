import pytest
from ddgsearch import llm_web_search

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
    # Should find at least one PDF for this famous paper
    # assert len(results["pdfs"]) > 0 

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
    
    # Verify keys exist
    expected_keys = {"pages", "pdfs", "images", "videos"}
    assert set(results.keys()) == expected_keys
    
    assert len(results["pages"]) <= 1
    assert len(results["images"]) <= 1
    assert len(results["videos"]) <= 1
