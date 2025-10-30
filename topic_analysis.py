from collections import Counter
import re

def top_keywords(texts, n=30, stopwords=None):
    stopwords = stopwords or set()
    words = []
    for t in texts:
        tokens = re.findall(r"\w+", t.lower())
        words.extend([w for w in tokens if w not in stopwords and len(w)>2])
    c = Counter(words)
    return c.most_common(n)