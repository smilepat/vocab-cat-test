"""Map ~3,300 raw topics to ~25 consolidated categories for content balancing."""

# 25 consolidated categories with keyword patterns
# Each category: list of substring patterns that match raw topic strings
TOPIC_CATEGORIES = {
    "daily_life": [
        "daily life", "home", "household", "routine", "lifestyle", "shopping",
        "domestic", "chores", "cleaning", "hygiene", "accommodation",
        "hobbies", "hobby", "leisure", "holiday", "celebration",
        "greet", "life",
    ],
    "emotions": [
        "emotion", "feeling", "mood", "happiness", "sadness", "anger", "fear",
        "anxiety", "joy", "love", "grief", "psychological", "mental health",
        "sorrow", "pleasure", "despair", "hope", "surprise", "disgust",
        "frustration", "sympathy", "empathy", "passion",
    ],
    "action": [
        "action", "movement", "motion", "activity", "physical",
        "gesture", "posture", "speed", "continuation", "cessation",
        "destruction", "creation", "impact", "cause and effect",
    ],
    "personality": [
        "personality", "character", "behavior", "attitude", "habit",
        "trait", "temperament", "manner", "identity", "reputation",
        "quality", "intensity",
    ],
    "cognition": [
        "thinking", "thought", "logic", "reasoning", "analysis",
        "perception", "sense", "opinion", "idea", "concept",
        "abstract", "imagination", "decision", "choice", "judgment",
        "problem", "solution", "intelligence", "memory", "attention",
        "evaluation", "comparison", "possibility", "planning",
        "skill", "ability", "control", "importance", "success",
        "achievement", "mistake", "challenge", "support",
        "connection", "distribution", "accumulation", "signaling",
        "representation", "information", "agreement",
    ],
    "nature": [
        "nature", "environment", "weather", "climate", "geography",
        "landscape", "earth", "geology", "ocean", "sea", "mountain",
        "river", "forest", "ecology", "space", "global",
    ],
    "animals": [
        "animal", "bird", "fish", "insect", "mammal", "reptile",
        "pet", "wildlife", "creature", "species", "genetic",
    ],
    "plants": [
        "plant", "flower", "tree", "garden", "vegetation",
        "farming", "agriculture", "crop", "harvest",
    ],
    "health": [
        "health", "body", "medicine", "medical", "disease", "illness",
        "hospital", "doctor", "treatment", "anatomy", "organ",
        "injury", "symptom", "therapy", "drug", "death",
        "safety", "accident",
    ],
    "food": [
        "food", "cooking", "drink", "meal", "recipe", "kitchen",
        "taste", "nutrition", "diet", "restaurant", "cuisine",
    ],
    "society": [
        "society", "culture", "community", "social", "tradition",
        "custom", "population", "demographic", "civilization",
        "people", "gender", "class", "royalty", "fantasy",
        "mythology", "magic", "story", "stories",
    ],
    "communication": [
        "communication", "language", "speech", "media", "conversation",
        "writing", "reading", "alphabet", "grammar", "word",
        "letter", "message", "news", "sound", "humor",
    ],
    "education": [
        "education", "school", "learning", "academic", "study",
        "student", "teacher", "university", "exam", "knowledge",
    ],
    "science": [
        "science", "biology", "physics", "chemistry", "research",
        "experiment", "technology", "tech", "computer", "digital",
        "engineering", "data", "software", "internet", "math",
        "geometry", "energy", "construction", "architecture",
        "building", "structure",
    ],
    "time": [
        "time", "history", "change", "age", "period", "season",
        "calendar", "schedule", "past", "future", "duration",
        "event",
    ],
    "crime": [
        "crime", "law", "punishment", "justice", "court", "police",
        "prison", "legal", "judge", "trial", "rule",
    ],
    "government": [
        "government", "politic", "state", "nation", "policy",
        "democracy", "election", "parliament", "authority", "power",
        "administration", "regulation",
    ],
    "travel": [
        "transport", "travel", "vehicle", "location", "place",
        "city", "country", "map", "road", "journey", "destination",
        "tourism", "direction", "navigation",
    ],
    "relationships": [
        "relationship", "family", "friend", "marriage", "parent",
        "child", "sibling", "partner", "neighbor",
    ],
    "business": [
        "business", "finance", "economic", "money", "job", "work",
        "career", "employment", "trade", "market", "company",
        "industry", "commerce", "banking", "investment", "profit",
        "economy", "possession",
    ],
    "sports": [
        "sport", "game", "exercise", "competition", "athlete",
        "fitness", "team", "match", "race", "olympic",
    ],
    "religion": [
        "religion", "faith", "church", "spiritual", "god",
        "prayer", "worship", "belief", "sacred", "philosophy",
        "christianity", "islam", "buddhis",
    ],
    "ethics": [
        "ethic", "moral", "value", "virtue", "conscience",
        "responsibility", "duty", "right", "wrong",
    ],
    "conflict": [
        "conflict", "war", "military", "army", "battle",
        "weapon", "violence", "fight", "attack", "defense",
        "soldier", "navy",
    ],
    "arts": [
        "art", "music", "entertainment", "performance", "literature",
        "theater", "film", "movie", "dance", "paint", "sculpture",
        "creative", "design", "photograph", "sing", "craft",
    ],
    "appearance": [
        "appearance", "description", "fashion", "beauty", "clothing",
        "cloth", "wear", "dress", "style", "color", "shape",
        "size", "material", "texture", "fabric", "accessori",
    ],
    "numbers": [
        "number", "quantity", "measurement", "math", "count",
        "calculation", "statistic", "amount", "unit",
    ],
    "objects": [
        "object", "tool", "device", "machine", "equipment",
        "instrument", "container", "furniture",
    ],
}

# Fallback category for unmatched topics
DEFAULT_CATEGORY = "general"

# Cache for fast lookup
_cache: dict[str, str] = {}


def map_topic(raw_topic: str) -> str:
    """Map a raw topic string to a consolidated category.

    Handles pipe-separated multi-topics by taking the first match.
    """
    if not raw_topic or raw_topic.strip() in ("", "N/A", "None", "general"):
        return DEFAULT_CATEGORY

    key = raw_topic.strip().lower()

    if key in _cache:
        return _cache[key]

    # Handle pipe-separated topics (e.g., "animals|nature")
    parts = key.replace("|", ",").split(",")

    for part in parts:
        part = part.strip()
        for category, patterns in TOPIC_CATEGORIES.items():
            for pattern in patterns:
                if pattern in part:
                    _cache[key] = category
                    return category

    _cache[key] = DEFAULT_CATEGORY
    return DEFAULT_CATEGORY


def get_all_categories() -> list[str]:
    """Return sorted list of all consolidated category names."""
    return sorted(list(TOPIC_CATEGORIES.keys()) + [DEFAULT_CATEGORY])


def build_topic_stats(raw_topics: list[str]) -> dict[str, dict]:
    """Build mapping statistics from a list of raw topics.

    Returns dict with coverage info per category.
    """
    category_counts: dict[str, int] = {}
    unmapped = []

    for raw in raw_topics:
        cat = map_topic(raw)
        category_counts[cat] = category_counts.get(cat, 0) + 1
        if cat == DEFAULT_CATEGORY and raw.strip().lower() not in ("", "general", "n/a", "none"):
            unmapped.append(raw.strip().lower())

    return {
        "categories": dict(sorted(category_counts.items(), key=lambda x: -x[1])),
        "total_categories": len(category_counts),
        "unmapped_count": len(unmapped),
        "unmapped_sample": sorted(set(unmapped))[:20],
    }
