"""Distractor generation engine for vocabulary test items."""
import random
from ..data.load_vocabulary import VocabWord
from ..data.graph_connector import VocabGraph


class DistractorEngine:
    """Generate distractors for vocabulary test items using metadata + graph."""

    def __init__(self, vocab: list[VocabWord], graph: VocabGraph | None = None):
        self.vocab = vocab
        self._graph = graph
        # Build indices for fast lookup
        self._by_pos: dict[str, list[VocabWord]] = {}
        self._by_cefr: dict[str, list[VocabWord]] = {}
        self._by_topic: dict[str, list[VocabWord]] = {}
        self._by_word: dict[str, VocabWord] = {}
        self._synonym_sets: dict[str, set[str]] = {}
        self._antonym_sets: dict[str, set[str]] = {}

        for w in vocab:
            self._by_pos.setdefault(w.pos, []).append(w)
            self._by_cefr.setdefault(w.cefr, []).append(w)
            primary_topic = w.topic.split(",")[0].strip().split("|")[0].strip() if w.topic else ""
            if primary_topic:
                self._by_topic.setdefault(primary_topic, []).append(w)
            self._by_word[w.word_display.lower()] = w
            self._synonym_sets[w.word_display.lower()] = {
                s.lower() for s in w.synonym
            }
            self._antonym_sets[w.word_display.lower()] = {
                a.lower() for a in w.antonym
            }

    def _is_synonym_of(self, word1: str, word2: str) -> bool:
        """Check if two words are synonyms."""
        w1 = word1.lower()
        w2 = word2.lower()
        return (
            w2 in self._synonym_sets.get(w1, set()) or
            w1 in self._synonym_sets.get(w2, set())
        )

    def _shares_meaning(self, word1: VocabWord, word2: VocabWord) -> bool:
        """Check if two words share overlapping Korean meanings."""
        if not word1.meaning_ko or not word2.meaning_ko:
            return False
        m1_parts = set(word1.meaning_ko.replace(",", " ").split())
        m2_parts = set(word2.meaning_ko.replace(",", " ").split())
        # Remove very common particles
        common_particles = {"을", "를", "이", "가", "의", "에", "로", "~", "하다", "되다"}
        m1_parts -= common_particles
        m2_parts -= common_particles
        overlap = m1_parts & m2_parts
        return len(overlap) >= 2

    def _get_adjacent_cefr(self, cefr: str) -> list[str]:
        """Get adjacent CEFR levels."""
        levels = ["A1", "A2", "B1", "B2", "C1"]
        try:
            idx = levels.index(cefr)
        except ValueError:
            return levels
        result = [cefr]
        if idx > 0:
            result.append(levels[idx - 1])
        if idx < len(levels) - 1:
            result.append(levels[idx + 1])
        return result

    def generate_meaning_distractors(
        self,
        target: VocabWord,
        n: int = 3,
        field: str = "meaning_ko",
    ) -> list[str]:
        """Strategy A: Same POS + adjacent CEFR, exclude synonyms.

        For Type 1 (Korean meaning) or Type 2 (English definition) questions.
        Returns list of distractor meanings (Korean or English).
        """
        adjacent_cefrs = self._get_adjacent_cefr(target.cefr)
        target_word_lower = target.word_display.lower()

        # Candidate pool: same POS, adjacent CEFR
        candidates = []
        for cefr in adjacent_cefrs:
            for w in self._by_cefr.get(cefr, []):
                if w.pos != target.pos:
                    continue
                if w.word_display.lower() == target_word_lower:
                    continue
                if self._is_synonym_of(target.word_display, w.word_display):
                    continue
                # Check word family overlap
                target_family = {f.lower() for f in target.word_family}
                if w.word_display.lower() in target_family:
                    continue
                if self._shares_meaning(target, w):
                    continue
                candidates.append(w)

        # Prefer same-topic candidates
        primary_topic = target.topic.split(",")[0].strip().split("|")[0].strip() if target.topic else ""
        same_topic = [c for c in candidates if primary_topic and primary_topic in c.topic]
        other_topic = [c for c in candidates if c not in same_topic]

        # Select: prefer same topic, fill with others
        selected: list[VocabWord] = []
        pool = same_topic.copy()
        random.shuffle(pool)

        for c in pool:
            if len(selected) >= n:
                break
            # Ensure distractors aren't synonyms of each other
            is_ok = True
            for existing in selected:
                if self._is_synonym_of(c.word_display, existing.word_display):
                    is_ok = False
                    break
            if is_ok:
                selected.append(c)

        # Fill remaining from other topics
        if len(selected) < n:
            random.shuffle(other_topic)
            for c in other_topic:
                if len(selected) >= n:
                    break
                is_ok = True
                for existing in selected:
                    if self._is_synonym_of(c.word_display, existing.word_display):
                        is_ok = False
                        break
                if is_ok:
                    selected.append(c)

        if field == "meaning_ko":
            return [w.meaning_ko for w in selected[:n]]
        else:
            return [w.definition_en for w in selected[:n]]

    def generate_synonym_distractors(self, target: VocabWord, n: int = 3) -> list[str]:
        """Strategy B: For synonym questions. Distractors are non-synonyms.

        Returns list of distractor words (not synonyms of target).
        """
        adjacent_cefrs = self._get_adjacent_cefr(target.cefr)
        target_synonym_set = {s.lower() for s in target.synonym}

        candidates = []
        for cefr in adjacent_cefrs:
            for w in self._by_cefr.get(cefr, []):
                if w.pos != target.pos:
                    continue
                w_lower = w.word_display.lower()
                if w_lower == target.word_display.lower():
                    continue
                if w_lower in target_synonym_set:
                    continue
                if self._is_synonym_of(target.word_display, w.word_display):
                    continue
                candidates.append(w)

        random.shuffle(candidates)
        selected = []
        for c in candidates:
            if len(selected) >= n:
                break
            is_ok = True
            for existing in selected:
                if self._is_synonym_of(c.word_display, existing.word_display):
                    is_ok = False
                    break
            if is_ok:
                selected.append(c)

        return [w.word_display for w in selected[:n]]

    def generate_antonym_distractors(self, target: VocabWord, n: int = 3) -> list[str]:
        """For antonym questions. Distractors are non-antonyms of target.

        Uses graph data when available for better semantic plausibility.
        """
        target_antonym_set = {a.lower() for a in target.antonym}
        target_synonym_set = {s.lower() for s in target.synonym}
        exclude = target_antonym_set | target_synonym_set | {target.word_display.lower()}

        candidates: list[VocabWord] = []

        # Strategy D: graph-based siblings (share hypernym, not antonyms/synonyms)
        if self._graph and self._graph.is_loaded:
            graph_candidates = self._graph.get_graph_distractors(
                target.word_display, exclude=exclude, max_count=20
            )
            for gc in graph_candidates:
                w = self._by_word.get(gc)
                if w and w.pos == target.pos and gc not in exclude:
                    candidates.append(w)

        # Fallback: same POS + adjacent CEFR
        if len(candidates) < n * 2:
            adjacent_cefrs = self._get_adjacent_cefr(target.cefr)
            for cefr in adjacent_cefrs:
                for w in self._by_cefr.get(cefr, []):
                    if w.pos != target.pos:
                        continue
                    wl = w.word_display.lower()
                    if wl in exclude:
                        continue
                    if wl not in {c.word_display.lower() for c in candidates}:
                        candidates.append(w)

        random.shuffle(candidates)
        selected = []
        for c in candidates:
            if len(selected) >= n:
                break
            is_ok = True
            for existing in selected:
                if self._is_synonym_of(c.word_display, existing.word_display):
                    is_ok = False
                    break
            if is_ok:
                selected.append(c)

        return [w.word_display for w in selected[:n]]

    def generate_graph_distractors(self, target: VocabWord, n: int = 3) -> list[str]:
        """Strategy D: Graph-based distractors using hypernym siblings.

        Falls back to Strategy A if graph is unavailable.
        """
        if not self._graph or not self._graph.is_loaded:
            return self.generate_synonym_distractors(target, n)

        exclude = (
            {target.word_display.lower()}
            | self._synonym_sets.get(target.word_display.lower(), set())
            | self._antonym_sets.get(target.word_display.lower(), set())
        )

        graph_candidates = self._graph.get_graph_distractors(
            target.word_display, exclude=exclude, max_count=20
        )

        # Filter to same POS and in our vocab
        valid = []
        for gc in graph_candidates:
            w = self._by_word.get(gc)
            if w and w.pos == target.pos:
                valid.append(w)

        random.shuffle(valid)
        selected = []
        for v in valid:
            if len(selected) >= n:
                break
            is_ok = all(
                not self._is_synonym_of(v.word_display, s.word_display)
                for s in selected
            )
            if is_ok:
                selected.append(v)

        # Fallback if not enough
        if len(selected) < n:
            fallback = self.generate_synonym_distractors(target, n - len(selected))
            existing_words = {s.word_display.lower() for s in selected}
            for fb in fallback:
                if fb.lower() not in existing_words:
                    selected.append(self._by_word.get(fb.lower(), VocabWord(
                        word_display=fb, freq_rank=0, pos="", cefr="", meaning_ko="", definition_en=""
                    )))

        return [w.word_display if isinstance(w, VocabWord) else w for w in selected[:n]]

    def generate_sentence_distractors(self, target: VocabWord, n: int = 3) -> list[str]:
        """For sentence completion (Type 5). Use graph distractors when available."""
        if self._graph and self._graph.is_loaded:
            return self.generate_graph_distractors(target, n)
        return self.generate_synonym_distractors(target, n)

    def generate_item(
        self,
        target: VocabWord,
        question_type: int,
    ) -> dict | None:
        """Generate a complete test item with question, correct answer, and distractors.

        Returns dict with: stem, correct_answer, distractors, metadata

        Loanwords (e.g. computer→컴퓨터) are redirected from Type 1/2 to Type 3/5
        because their Korean meaning is a transparent transliteration, making the
        answer trivially obvious without any English knowledge.
        """
        # Redirect loanwords away from meaning-matching questions
        if target.is_loanword and question_type in (1, 2):
            if target.synonym:
                return self.generate_item(target, question_type=3)
            if target.sentence_1 or target.sentence_2:
                return self.generate_item(target, question_type=5)
            return None

        if question_type == 1:
            # Korean meaning recognition
            distractors = self.generate_meaning_distractors(target, n=3, field="meaning_ko")
            if len(distractors) < 3:
                return None
            return {
                "stem": f"다음 단어 '{target.word_display}'의 뜻으로 가장 알맞은 것을 고르세요.",
                "correct_answer": target.meaning_ko,
                "distractors": distractors,
                "word": target.word_display,
                "question_type": 1,
            }

        elif question_type == 2:
            # English definition matching
            distractors = self.generate_meaning_distractors(target, n=3, field="definition_en")
            if len(distractors) < 3:
                return None
            return {
                "stem": f"Choose the correct English definition of '{target.word_display}'.",
                "correct_answer": target.definition_en,
                "distractors": distractors,
                "word": target.word_display,
                "question_type": 2,
            }

        elif question_type == 3:
            # Synonym selection
            if not target.synonym:
                return None
            correct = random.choice(target.synonym)
            distractors = self.generate_synonym_distractors(target, n=3)
            if len(distractors) < 3:
                return None
            return {
                "stem": f"다음 단어 '{target.word_display}'와 의미가 가장 비슷한 유의어를 고르세요.",
                "correct_answer": correct,
                "distractors": distractors,
                "word": target.word_display,
                "question_type": 3,
            }

        elif question_type == 4:
            # Antonym selection
            if not target.antonym:
                return None
            correct = random.choice(target.antonym)
            distractors = self.generate_antonym_distractors(target, n=3)
            if len(distractors) < 3:
                return None
            return {
                "stem": f"다음 단어 '{target.word_display}'와 의미가 반대인 반의어를 고르세요.",
                "correct_answer": correct,
                "distractors": distractors,
                "word": target.word_display,
                "question_type": 4,
            }

        elif question_type == 5:
            # Sentence completion
            sentence = target.sentence_1 or target.sentence_2
            if not sentence:
                return None
            # Create blank by replacing the word in the sentence
            blanked = sentence.replace(target.word_display, "______")
            if blanked == sentence:
                # Try case-insensitive
                import re
                blanked = re.sub(
                    re.escape(target.word_display), "______", sentence, flags=re.IGNORECASE, count=1
                )
            if blanked == sentence:
                return None
            distractors = self.generate_sentence_distractors(target, n=3)
            if len(distractors) < 3:
                return None
            return {
                "stem": f"문맥상 빈칸에 들어갈 가장 적절한 단어를 고르세요.\n\n{blanked}",
                "correct_answer": target.word_display,
                "distractors": distractors,
                "word": target.word_display,
                "question_type": 5,
            }

        elif question_type == 6:
            # Collocation judgment
            if not target.collocation:
                return None
            correct_coll = random.choice(target.collocation)
            return {
                "stem": f"다음 연어 표현이 올바른지 판단하세요: '{correct_coll}'",
                "correct_answer": "올바름",
                "distractors": ["올바르지 않음"],
                "word": target.word_display,
                "question_type": 6,
            }

        return None
