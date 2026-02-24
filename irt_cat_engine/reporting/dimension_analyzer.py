"""5D Vocabulary Dimension Analyzer.

Maps question types to vocabulary dimensions and computes per-dimension scores.
Dimensions are analyzed post-hoc after a test completes — the IRT adaptive
algorithm continues to select items based on Fisher information, not by dimension.
"""

# Question type → dimension mapping
# Types 1-6 cover 3 of 5 dimensions; form and pragmatic need new question types
QUESTION_TYPE_TO_DIMENSION: dict[int, str] = {
    1: "semantic",      # 한국어 뜻 고르기
    2: "semantic",      # 영어 정의 매칭
    3: "relational",    # 동의어 선택
    4: "relational",    # 반의어 선택
    5: "contextual",    # 문장 빈칸 채우기
    6: "contextual",    # 연어 판단
}

DIMENSIONS = [
    {"key": "semantic",    "label": "Semantic",    "label_ko": "의미 이해",  "color": "#3b82f6"},
    {"key": "contextual",  "label": "Contextual",  "label_ko": "문맥 사용",  "color": "#10b981"},
    {"key": "form",        "label": "Form",        "label_ko": "형태 변환",  "color": "#f59e0b"},
    {"key": "relational",  "label": "Relational",  "label_ko": "관계어",    "color": "#ef4444"},
    {"key": "pragmatic",   "label": "Pragmatic",   "label_ko": "화용 맥락",  "color": "#8b5cf6"},
]

DIMENSION_KEYS = [d["key"] for d in DIMENSIONS]


def compute_dimension_scores(
    items_administered: list,
    responses: list[int],
) -> list[dict]:
    """Compute per-dimension scores from administered items.

    Args:
        items_administered: List of ItemParameters with question_type attribute.
        responses: List of 0/1 responses matching items_administered.

    Returns:
        List of dimension score dicts, one per dimension.
        Dimensions with no items have score=None.
    """
    # Accumulate per-dimension stats
    dim_stats: dict[str, dict] = {d["key"]: {"correct": 0, "total": 0} for d in DIMENSIONS}

    for item, response in zip(items_administered, responses):
        dimension = QUESTION_TYPE_TO_DIMENSION.get(item.question_type)
        if dimension and dimension in dim_stats:
            dim_stats[dimension]["total"] += 1
            if response == 1:
                dim_stats[dimension]["correct"] += 1

    # Build result list
    result = []
    for dim in DIMENSIONS:
        key = dim["key"]
        stats = dim_stats[key]
        total = stats["total"]
        correct = stats["correct"]
        score = round(correct / total * 100) if total > 0 else None

        result.append({
            "dimension": key,
            "label": dim["label"],
            "label_ko": dim["label_ko"],
            "color": dim["color"],
            "correct": correct,
            "total": total,
            "score": score,
        })

    return result
