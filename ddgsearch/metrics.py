import math
import re
from typing import List, Dict, Optional, Set

# Curated bilingual (Spanish & English) stopwords to filter out noise
STOPWORDS: Set[str] = {
    # Spanish stopwords
    "de", "la", "el", "los", "las", "un", "una", "unos", "unas", "y", "en", "a",
    "para", "por", "con", "que", "se", "su", "sus", "del", "al", "como", "más",
    "pero", "o", "no", "si", "sobre", "entre", "este", "esta", "estos", "estas",
    "lo", "ya", "ha", "han", "ser", "es", "son", "fue", "era", "muy", "hasta",
    "desde", "cuando", "donde", "quien", "cual", "cuales", "todo", "toda", "todos",
    # English stopwords
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "by", "from", "as", "is", "was", "are", "were", "been", "be", "have",
    "has", "had", "it", "its", "that", "this", "these", "those", "which", "who",
    "whom", "what", "where", "when", "why", "how", "all", "any", "both", "each",
    "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only",
    "own", "same", "so", "than", "too", "very", "can", "will", "just", "into"
}

def tokenize(text: str, remove_stopwords: bool = True) -> List[str]:
    """Tokenizes text into words, optionally removing common stopwords."""
    if not text:
        return []
    words = re.findall(r'\b[a-zA-Z0-9áéíóúÁÉÍÓÚñÑüÜ_-]+\b', text.lower())
    if remove_stopwords:
        words = [w for w in words if w not in STOPWORDS and len(w) > 1]
    return words

class BM25Okapi:
    """Lightweight pure-Python BM25Okapi implementation for ranking chunks."""

    def __init__(self, corpus: List[List[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.doc_lengths = [len(doc) for doc in corpus]
        self.avgdl = sum(self.doc_lengths) / self.corpus_size if self.corpus_size > 0 else 0.0

        # Term document frequencies
        self.doc_freqs: Dict[str, int] = {}
        for doc in corpus:
            unique_terms = set(doc)
            for term in unique_terms:
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1

        # Calculate IDF with standard Okapi smoothing
        self.idf: Dict[str, float] = {}
        for term, freq in self.doc_freqs.items():
            self.idf[term] = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0)

    def get_scores(self, query_tokens: List[str]) -> List[float]:
        """Calculates BM25 relevance score for each document in the corpus."""
        scores = [0.0] * self.corpus_size
        if not query_tokens or self.avgdl == 0.0:
            return scores

        for term in query_tokens:
            if term not in self.idf:
                continue
            idf_val = self.idf[term]
            for doc_idx in range(self.corpus_size):
                doc_len = self.doc_lengths[doc_idx]
                # Frequency of term in this doc
                tf = query_tokens.count(term)
                # Compute term score with length normalization
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avgdl))
                scores[doc_idx] += idf_val * (numerator / denominator)
        return scores

def split_into_paragraphs(text: str, min_length: int = 100) -> List[str]:
    """Splits a document text into cohesive paragraphs.

    Filters out paragraphs shorter than min_length to remove boilerplate.
    """
    if not text:
        return []
    
    raw_paras = text.split("\n\n")
    paragraphs = []
    for p in raw_paras:
        cleaned = p.strip()
        if len(cleaned) >= min_length:
            paragraphs.append(cleaned)
    return paragraphs

def calculate_relevance_score(text: str, query: str) -> float:
    """Calculates term frequency relevance filtered by stopwords."""
    if not text or not query:
        return 0.0
    query_tokens = set(tokenize(query, remove_stopwords=True))
    text_tokens = tokenize(text, remove_stopwords=True)
    if not text_tokens or not query_tokens:
        return 0.0
    matches = sum(1 for word in text_tokens if word in query_tokens)
    return matches / math.sqrt(len(text_tokens))

def entropy(text: str) -> float:
    """Retained for backward compatibility. Computes Shannon entropy."""
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

def quality_score(text: str, query: str, title: str = "") -> float:
    """Calculates a comprehensive quality score combining BM25 relevance and structure bonuses."""
    q_tokens = tokenize(query, remove_stopwords=True)
    t_tokens = tokenize(text, remove_stopwords=True)
    if not t_tokens or not q_tokens:
        return 0.0

    bm25 = BM25Okapi([t_tokens])
    score = bm25.get_scores(q_tokens)[0] if bm25.corpus_size > 0 else 0.0

    # Boost score if query terms appear in page title
    if title:
        title_tokens = set(tokenize(title, remove_stopwords=True))
        if any(token in title_tokens for token in q_tokens):
            score *= 1.3

    # Boost score if text contains tabular data, math formulas or code
    if "|" in text or "$$" in text or "```" in text:
        score *= 1.2

    return score
