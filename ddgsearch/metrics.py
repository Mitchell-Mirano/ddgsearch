import math
import re

def calculate_relevance_score(text: str, query: str) -> float:
    """Calculates text relevance with respect to the query.

    Args:
        text (str): The extracted content from the page.
        query (str): The original user query.

    Returns:
        float: A relevance score based on term frequency.
    """
    if not text or not query:
        return 0.0
    
    query_words = set(re.findall(r'\w+', query.lower()))
    text_words = re.findall(r'\w+', text.lower())
    
    if not text_words:
        return 0.0
        
    matches = sum(1 for word in text_words if word in query_words)
    # Score normalized by the square root of the length to avoid penalizing reasonable short texts
    return matches / math.sqrt(len(text_words))

def entropy(text: str) -> float:
    """Calculates Shannon entropy to measure lexical richness of the text.

    Args:
        text (str): The text to analyze.

    Returns:
        float: The Shannon entropy value.
    """
    if not text:
        return 0.0
        
    tokens = text.split()
    if not tokens:
        return 0.0
        
    freqs = {}
    for token in tokens:
        freqs[token] = freqs.get(token, 0) + 1
    
    probs = [freq / len(tokens) for freq in freqs.values()]
    return -sum(p * math.log2(p) for p in probs)

def quality_score(text: str, query: str) -> float:
    """Calculates a comprehensive quality score for the LLM context.

    Combines simple semantic relevance with lexical richness (entropy).

    Args:
        text (str): The page content.
        query (str): The user query.

    Returns:
        float: Final quality score.
    """
    rel = calculate_relevance_score(text, query)
    ent = entropy(text)
    
    # We combine: relevance is a priority, entropy acts as a quality multiplier.
    # A relevant text but with little richness (repetitive) will lower its score.
    return rel * (min(ent, 5.0) / 5.0)