"""Configuration constants for the IRT CAT Engine."""
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
VOCAB_DB_PATH = PROJECT_ROOT / "9000word_full_db.csv"
GRAPH_DB_PATH = PROJECT_ROOT / "vocabulary_graph.json"

# IRT Model Parameters
IRT_MODEL = "2PL"  # "2PL" or "3PL"
THETA_RANGE = (-3.0, 3.0)
THETA_PRIOR_MEAN = 0.0
THETA_PRIOR_SD = 1.0

# 3PL guessing parameter defaults
GUESSING_C_DEFAULT = 0.0       # 2PL mode: no guessing
GUESSING_C_4CHOICE = 0.20      # 3PL mode: 4-choice items (slightly below 1/4 = 0.25)
GUESSING_C_BINARY = 0.40       # 3PL mode: binary items (Type 6 collocation)
MIN_SESSIONS_FOR_3PL = 5000    # Minimum accumulated sessions before enabling 3PL

# Difficulty (b) initialization weights
# Updated 2026-02-25: Prioritize Korean curriculum + frequency (80% combined)
B_WEIGHT_CEFR = 0.10           # CEFR level (European standard)
B_WEIGHT_FREQ = 0.40           # Frequency rank (40%)
B_WEIGHT_GSE = 0.10            # Pearson Global Scale
B_WEIGHT_CURRICULUM = 0.40     # Korean curriculum (40%)
B_WEIGHT_LEXILE = 0.00         # Lexile (disabled)

# CEFR to numeric mapping
CEFR_NUMERIC = {"A1": 0.0, "A2": 0.2, "B1": 0.45, "B2": 0.7, "C1": 0.95}

# Korean curriculum to numeric mapping
CURRICULUM_NUMERIC = {"초등": 0.1, "중등": 0.45, "고등": 0.75, "기타": 0.95}

# Question type difficulty modifiers
# Updated 2026-02-25: Adjusted for EFL learners' cognitive difficulty
# EFL difficulty order: 1 (easiest) → 3 → 4 → 5 ≈ 2 (hardest)
QUESTION_TYPE_B_MODIFIER = {
    1: 0.0,   # Korean meaning recognition (baseline - easiest for EFL)
    2: 0.6,   # English definition matching (hardest - requires English-to-English)
    3: 0.2,   # Synonym selection (2nd easiest - L1 mediation possible)
    4: 0.3,   # Antonym selection (moderate - conceptual understanding needed)
    5: 0.5,   # Sentence completion (hard - contextual usage required)
    6: 0.2,   # Collocation judgment (similar to synonyms)
}

# Discrimination (a) factors
A_BASE = 1.0
A_MIN = 0.4
A_MAX = 2.5
EDU_VALUE_BONUS = {10: 1.15, 9: 1.10, 8: 1.0, 7: 0.90, 6: 0.80}
POS_FACTOR = {
    "NOUN": 1.05, "VERB": 1.05, "ADJ": 1.0, "ADV": 0.95,
    "PREP": 0.80, "CONJ": 0.75, "DET": 0.70, "PRON": 0.75,
    "INTERJ": 0.85, "NUM": 0.80,
}
GENERAL_TOPICS = {"general", "grammar"}

# CAT Settings
CAT_MIN_ITEMS = 15
CAT_MAX_ITEMS = 40
CAT_SE_THRESHOLD = 0.30
CAT_CONVERGENCE_WINDOW = 5
CAT_CONVERGENCE_EPSILON = 0.05
CAT_TIME_LIMIT_MINUTES = 30
CAT_MAX_EXPOSURE_RATE = 0.25

# EAP Settings
EAP_QUADRATURE_POINTS = 41
EAP_QUAD_RANGE = (-4.0, 4.0)

# Content Balance Targets (for 30-item test)
CONTENT_BALANCE = {
    "pos": {"NOUN": (0.45, 0.55), "VERB": (0.25, 0.30), "ADJ": (0.15, 0.20)},
    "max_same_topic": 3,
    "question_type_receptive": (0.50, 0.60),   # Types 1-2
    "question_type_relational": (0.20, 0.30),   # Types 3-4
    "question_type_contextual": (0.15, 0.25),   # Types 5-6
}

# Theta to CEFR boundaries
THETA_CEFR_BOUNDARIES = {
    "A1": (-3.0, -1.5),
    "A2": (-1.5, -0.5),
    "B1": (-0.5, 0.5),
    "B2": (0.5, 1.5),
    "C1": (1.5, 3.0),
}

# Theta to Korean curriculum boundaries
THETA_CURRICULUM_BOUNDARIES = {
    "초등 수준 (Elementary)": (-3.0, -0.8),
    "중등 수준 (Middle School)": (-0.8, 0.3),
    "고등 수준 (High School)": (0.3, 1.2),
    "고등 이상 (Beyond High School)": (1.2, 3.0),
}

# Initial theta from profile survey
GRADE_THETA = {
    "초3-4": -2.0, "초5-6": -1.2,
    "중1": -0.5, "중2": 0.0, "중3": 0.3,
    "고1": 0.5, "고2": 0.8, "고3": 1.0,
    "대학": 1.2, "성인": 0.5,
}
SELF_ASSESS_ADJUST = {"beginner": -0.5, "intermediate": 0.0, "advanced": 0.5}
EXAM_ADJUST = {"none": -0.3, "내신": 0.0, "수능": 0.2, "TOEIC": 0.3, "TOEFL": 0.5}

# Transparent loanwords — Korean meaning is a phonetic transliteration of the English word.
# These words are trivially recognizable for Korean speakers on Type 1/2 questions,
# providing zero Fisher information. They are redirected to Type 3/5 or filtered.
TRANSPARENT_LOANWORDS: set[str] = {
    # Food & Drink
    "banana", "barbecue", "buffet", "cafe", "cake", "caramel", "cereal",
    "cheese", "chocolate", "cocktail", "coffee", "cookie", "dessert",
    "juice", "ketchup", "lemon", "mayonnaise", "muffin", "mustard",
    "orange", "pasta", "pizza", "salad", "sandwich", "steak", "syrup",
    "tomato", "vitamin", "waffle", "yogurt",
    # Technology
    "algorithm", "antenna", "battery", "bluetooth", "cable", "camera",
    "computer", "dashboard", "database", "desktop", "digital", "hardware",
    "helicopter", "internet", "keyboard", "laptop", "laser", "monitor",
    "motor", "neon", "network", "radar", "radio", "robot", "sensor",
    "server", "smartphone", "software", "tablet", "video",
    # Transportation & Places
    "apartment", "asphalt", "bus", "cabin", "campus", "cement", "concrete",
    "elevator", "escalator", "garage", "hotel", "lobby", "ramp", "resort",
    "spa", "taxi", "tent", "tile", "tower", "tunnel",
    # Sports & Arts
    "ballet", "concert", "drama", "festival", "golf", "guitar", "jazz",
    "marathon", "opera", "penguin", "piano", "pool", "rocket", "tennis",
    # Daily Life & Business
    "album", "belt", "bench", "bonus", "chart", "coupon", "crystal",
    "diamond", "icon", "image", "jacket", "logo", "mask", "menu",
    "partner", "pattern", "pedal", "plastic", "premium", "project",
    "receipt", "robot", "scarf", "slogan", "sofa", "style", "system",
    "team", "ticket", "trend", "vest", "virus",
}
LOANWORD_MAX_PER_TEST = 2          # Max loanword items per test session
LOANWORD_DISCRIMINATION_FACTOR = 0.5  # Reduce discrimination for loanwords on Type 1/2
