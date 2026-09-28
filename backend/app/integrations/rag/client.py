from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass
from functools import lru_cache
from app.core.config import settings

@dataclass
class Chunk:
    source: str
    text: str

class LocalRAG:
    def __init__(self):
        self.chunks: list[Chunk] = []
        self.vectorizer = None
        self.matrix = None
        self._load()

    def _load(self):
        root = settings.rag_path
        if not root.is_absolute():
            root = Path(__file__).resolve().parents[3] / root
        root.mkdir(parents=True, exist_ok=True)
        for path in sorted(root.glob("*.txt")):
            raw = path.read_text(encoding="utf-8", errors="ignore")
            for part in [p.strip() for p in raw.split("\n\n") if p.strip()]:
                self.chunks.append(Chunk(path.name, part))
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
            self.matrix = self.vectorizer.fit_transform([c.text for c in self.chunks]) if self.chunks else None
        except Exception:
            self.vectorizer = None
            self.matrix = None

    def retrieve(self, query: str, top_k: int = 3) -> list[Chunk]:
        if not self.chunks:
            return []
        if self.vectorizer is not None and self.matrix is not None:
            from sklearn.metrics.pairwise import cosine_similarity
            q = self.vectorizer.transform([query])
            scores = cosine_similarity(q, self.matrix).ravel()
            order = scores.argsort()[::-1][:top_k]
            return [self.chunks[i] for i in order if scores[i] > 0]
        terms = set(query.lower().split())
        ranked = sorted(self.chunks, key=lambda c: len(terms & set(c.text.lower().split())), reverse=True)
        return ranked[:top_k]

@lru_cache(maxsize=1)
def get_rag() -> LocalRAG:
    return LocalRAG()
