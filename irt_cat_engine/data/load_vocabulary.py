"""Load and clean the vocabulary database from TSV."""
import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

from ..config import VOCAB_DB_PATH, TRANSPARENT_LOANWORDS


@dataclass
class VocabWord:
    """A vocabulary word with all its metadata."""
    word_display: str
    freq_rank: int
    pos: str
    cefr: str
    meaning_ko: str
    definition_en: str

    # Difficulty indicators
    freq_grade: str = ""
    kr_curriculum: str = ""
    grade_range: str = ""
    gse: float | None = None
    lexile: str = ""

    # Relationships
    synonym: list[str] = field(default_factory=list)
    antonym: list[str] = field(default_factory=list)
    hypernym: list[str] = field(default_factory=list)
    hyponym: list[str] = field(default_factory=list)
    word_family: list[str] = field(default_factory=list)
    collocation: list[str] = field(default_factory=list)

    # Learning content
    sentence_1: str = ""
    sentence_2: str = ""
    sentence_3: str = ""
    error_pattern: str = ""

    # Metadata
    topic: str = ""
    domain: str = ""
    register: str = ""
    educational_value: int | None = None
    oxford3000: str = ""
    ngsl: str = ""
    stem: str = ""

    # Loanword flag — set after loading
    is_loanword: bool = False


def _parse_pipe_list(value: str) -> list[str]:
    """Parse pipe-delimited or comma-delimited list into clean list."""
    if not value or value.strip() in ("N/A", "null", "None", "none", ""):
        return []
    # Try pipe first, then comma
    if "|" in value:
        items = value.split("|")
    elif ", " in value:
        items = value.split(", ")
    else:
        items = [value]
    return [item.strip() for item in items if item.strip() and item.strip() not in ("N/A", "null", "None")]


def _parse_gse(value: str) -> float | None:
    """Parse GSE value, handling dirty data."""
    if not value or value.strip() in ("N/A", "null", "None", "none", ""):
        return None
    # Remove non-numeric characters except decimal point
    cleaned = re.sub(r'[^\d.]', '', value.strip())
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_educational_value(value: str) -> int | None:
    """Parse educational_value, handling dirty data (timestamps leaked in)."""
    if not value or value.strip() in ("N/A", "null", "None", "none", ""):
        return None
    cleaned = value.strip()
    # Check if it looks like a date/timestamp
    if "-" in cleaned and len(cleaned) > 4:
        return None
    if ":" in cleaned:
        return None
    try:
        val = int(float(cleaned))
        if 1 <= val <= 10:
            return val
        return None
    except ValueError:
        return None


def _clean_freq_grade(value: str) -> str:
    """Clean freq_grade, mapping dirty values to standard categories."""
    if not value:
        return ""
    cleaned = value.strip()
    # Map known dirty values
    mapping = {
        "intermediate": "중빈도",
        "advanced": "저빈도",
        "None": "",
        "null": "",
        "초등": "",
        "중등": "",
        "고등": "",
        "일반": "중빈도",
        "기타": "",
    }
    if cleaned in mapping:
        return mapping[cleaned]
    # If it's a bare number, ignore it
    try:
        int(cleaned)
        return ""
    except ValueError:
        pass
    # Valid values
    if cleaned in ("최고빈도", "고빈도", "중빈도", "저빈도"):
        return cleaned
    return ""


def _parse_lexile_midpoint(value: str) -> float | None:
    """Parse Lexile value and return midpoint for range values."""
    if not value or value.strip() in ("N/A", "null", "None", "none", "Yes", ""):
        return None
    cleaned = value.strip().replace("L", "").replace("+", "")
    # Handle range like "400-600"
    if "-" in cleaned:
        parts = cleaned.split("-")
        try:
            return (float(parts[0]) + float(parts[1])) / 2.0
        except (ValueError, IndexError):
            return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def load_vocabulary(path: Path | None = None) -> list[VocabWord]:
    """Load vocabulary database from TSV file."""
    if path is None:
        path = VOCAB_DB_PATH

    words = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for i, row in enumerate(reader):
            try:
                freq_rank = int(row.get("freq_rank", 0) or 0) or (i + 1)
            except (ValueError, TypeError):
                freq_rank = i + 1

            word = VocabWord(
                word_display=row.get("word_display", "").strip(),
                freq_rank=freq_rank,
                pos=row.get("pos", "").strip(),
                cefr=row.get("cefr", "").strip(),
                meaning_ko=row.get("meaning_ko", "").strip(),
                definition_en=row.get("definition_en", "").strip(),
                freq_grade=_clean_freq_grade(row.get("freq_grade", "")),
                kr_curriculum=row.get("kr_curriculum", "").strip(),
                grade_range=row.get("grade_range", "").strip(),
                gse=_parse_gse(row.get("gse", "")),
                lexile=row.get("lexile", "").strip(),
                synonym=_parse_pipe_list(row.get("synonym", "")),
                antonym=_parse_pipe_list(row.get("antonym", "")),
                hypernym=_parse_pipe_list(row.get("hypernym", "")),
                hyponym=_parse_pipe_list(row.get("hyponym", "")),
                word_family=_parse_pipe_list(row.get("word_family", "")),
                collocation=_parse_pipe_list(row.get("collocation", "")),
                sentence_1=row.get("sentence_1", "").strip(),
                sentence_2=row.get("sentence_2", "").strip(),
                sentence_3=row.get("sentence_3", "").strip(),
                error_pattern=row.get("error_pattern", "").strip(),
                topic=row.get("topic", "").strip(),
                domain=row.get("domain", "").strip(),
                register=row.get("register", "").strip(),
                educational_value=_parse_educational_value(row.get("educational_value", "")),
                oxford3000=row.get("oxford3000", "").strip(),
                ngsl=row.get("ngsl", "").strip(),
                stem=row.get("stem", "").strip(),
            )

            if word.word_display:
                words.append(word)

    # Flag transparent loanwords
    for word in words:
        if word.word_display.lower() in TRANSPARENT_LOANWORDS:
            word.is_loanword = True

    return words


def get_vocab_stats(words: list[VocabWord]) -> dict:
    """Get summary statistics of the loaded vocabulary."""
    return {
        "total_words": len(words),
        "cefr_distribution": _count_by(words, lambda w: w.cefr),
        "pos_distribution": _count_by(words, lambda w: w.pos),
        "curriculum_distribution": _count_by(words, lambda w: w.kr_curriculum),
        "with_synonyms": sum(1 for w in words if w.synonym),
        "with_antonyms": sum(1 for w in words if w.antonym),
        "with_gse": sum(1 for w in words if w.gse is not None),
        "with_sentences": sum(1 for w in words if w.sentence_1),
    }


def _count_by(words: list[VocabWord], key_fn) -> dict[str, int]:
    counts: dict[str, int] = {}
    for w in words:
        k = key_fn(w)
        counts[k] = counts.get(k, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: -x[1]))
