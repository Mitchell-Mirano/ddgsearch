import math

def entropy(text: str) -> float:
    
    tokens = text.split()
    freqs = {}
    for token in tokens:
        freqs[token] = freqs.get(token, 0) + 1
    probs = [freq / len(tokens) for freq in freqs.values()]
    return -sum(p * math.log2(p) for p in probs)