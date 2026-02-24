"""Load vocabulary_graph.json and provide graph-based queries for distractor generation."""
import json
from pathlib import Path
from collections import defaultdict

from ..config import GRAPH_DB_PATH


class VocabGraph:
    """In-memory vocabulary graph for semantic relationship queries."""

    def __init__(self):
        self._synonyms: dict[str, set[str]] = defaultdict(set)
        self._antonyms: dict[str, set[str]] = defaultdict(set)
        self._hypernyms: dict[str, set[str]] = defaultdict(set)
        self._hyponyms: dict[str, set[str]] = defaultdict(set)
        self._word_props: dict[str, dict] = {}
        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def load(self, path: Path | None = None):
        """Load graph from JSON file."""
        if self._loaded:
            return

        if path is None:
            path = GRAPH_DB_PATH

        if not path.exists():
            return

        with open(path, "r", encoding="utf-8") as f:
            graph = json.load(f)

        # Index word nodes
        for node in graph.get("nodes", []):
            if node.get("type") == "Word":
                word_id = node["id"]  # e.g., "word:the"
                word_text = node.get("properties", {}).get("text", "").lower()
                if word_text:
                    self._word_props[word_text] = node.get("properties", {})

        # Index edges by relationship type
        for edge in graph.get("edges", []):
            src = edge.get("source", "").replace("word:", "").lower()
            tgt = edge.get("target", "").replace("word:", "").lower()
            etype = edge.get("type", "")

            if not src or not tgt:
                continue

            if etype == "SYNONYM_OF":
                self._synonyms[src].add(tgt)
                self._synonyms[tgt].add(src)
            elif etype == "ANTONYM_OF":
                self._antonyms[src].add(tgt)
                self._antonyms[tgt].add(src)
            elif etype == "HYPERNYM_OF":
                self._hypernyms[src].add(tgt)
                self._hyponyms[tgt].add(src)
            elif etype == "HYPONYM_OF":
                self._hyponyms[src].add(tgt)
                self._hypernyms[tgt].add(src)

        self._loaded = True

    def get_synonyms(self, word: str) -> set[str]:
        return self._synonyms.get(word.lower(), set())

    def get_antonyms(self, word: str) -> set[str]:
        return self._antonyms.get(word.lower(), set())

    def get_hypernyms(self, word: str) -> set[str]:
        return self._hypernyms.get(word.lower(), set())

    def get_hyponyms(self, word: str) -> set[str]:
        return self._hyponyms.get(word.lower(), set())

    def get_siblings(self, word: str) -> set[str]:
        """Get words that share a hypernym (semantic siblings)."""
        siblings = set()
        for hypernym in self.get_hypernyms(word):
            for sibling in self._hyponyms.get(hypernym, set()):
                if sibling != word.lower():
                    siblings.add(sibling)
        return siblings

    def get_semantic_neighbors(self, word: str, max_depth: int = 2) -> set[str]:
        """Get words within N hops of semantic distance.

        Useful for generating plausible distractors that are semantically
        related but not synonymous.
        """
        visited = {word.lower()}
        frontier = {word.lower()}

        for _ in range(max_depth):
            next_frontier = set()
            for w in frontier:
                for neighbor in (
                    self._synonyms.get(w, set())
                    | self._hypernyms.get(w, set())
                    | self._hyponyms.get(w, set())
                ):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        next_frontier.add(neighbor)
            frontier = next_frontier

        visited.discard(word.lower())
        return visited

    def get_graph_distractors(
        self,
        word: str,
        exclude: set[str] | None = None,
        max_count: int = 10,
    ) -> list[str]:
        """Get distractor candidates using graph relationships.

        Strategy D: Words that share a hypernym but are NOT synonyms.
        These are semantically related (plausible) but incorrect.
        """
        word_lower = word.lower()
        synonyms = self.get_synonyms(word_lower)
        exclude_set = {word_lower} | synonyms | (exclude or set())

        candidates = set()

        # 1. Siblings (share hypernym, not synonyms)
        for sib in self.get_siblings(word_lower):
            if sib not in exclude_set:
                candidates.add(sib)

        # 2. If not enough, use 2-hop neighbors
        if len(candidates) < max_count:
            for neighbor in self.get_semantic_neighbors(word_lower, max_depth=2):
                if neighbor not in exclude_set:
                    candidates.add(neighbor)
                    if len(candidates) >= max_count * 2:
                        break

        return list(candidates)[:max_count]

    @property
    def word_count(self) -> int:
        return len(self._word_props)

    @property
    def synonym_pair_count(self) -> int:
        return sum(len(v) for v in self._synonyms.values()) // 2

    @property
    def antonym_pair_count(self) -> int:
        return sum(len(v) for v in self._antonyms.values()) // 2


# Singleton
vocab_graph = VocabGraph()
