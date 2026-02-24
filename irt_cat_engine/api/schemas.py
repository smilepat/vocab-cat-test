"""Pydantic schemas for API request/response models."""
from pydantic import BaseModel, Field


# ── Request Models ──

class TestStartRequest(BaseModel):
    """Request to start a new test session."""
    user_id: str | None = None
    nickname: str | None = None
    grade: str = Field(default="중2", description="학년: 초3-4, 초5-6, 중1, 중2, 중3, 고1, 고2, 고3, 대학, 성인")
    self_assess: str = Field(default="intermediate", description="자기평가: beginner, intermediate, advanced")
    exam_experience: str = Field(default="none", description="시험경험: none, 내신, 수능, TOEIC, TOEFL")
    question_type: int = Field(default=0, description="문항유형: 0=혼합(추천), 1-6 개별 유형")


class TestRespondRequest(BaseModel):
    """Request to submit a response."""
    item_id: int
    is_correct: bool
    is_dont_know: bool = False
    response_time_ms: int | None = None


# ── Response Models ──

class ItemResponse(BaseModel):
    """An item presented to the test-taker."""
    item_id: int
    word: str
    question_type: int
    stem: str | None = None
    correct_answer: str | None = None
    distractors: list[str] | None = None
    options: list[str] | None = None
    pos: str = ""
    cefr: str = ""
    explanation: str | None = None


class TestProgressResponse(BaseModel):
    """Current test progress info."""
    items_completed: int
    total_correct: int
    accuracy: float
    current_theta: float
    current_se: float
    is_complete: bool


class TestStartResponse(BaseModel):
    """Response when starting a new test."""
    session_id: str
    user_id: str
    initial_theta: float
    first_item: ItemResponse
    progress: TestProgressResponse


class TestRespondResponse(BaseModel):
    """Response after submitting an answer."""
    is_complete: bool
    progress: TestProgressResponse
    next_item: ItemResponse | None = None
    results: "TestResultsResponse | None" = None


class CEFRProbabilities(BaseModel):
    A1: float = 0.0
    A2: float = 0.0
    B1: float = 0.0
    B2: float = 0.0
    C1: float = 0.0


class TopicAnalysis(BaseModel):
    topic: str
    correct: int
    total: int
    rate: float


class DimensionScore(BaseModel):
    """Score for a single vocabulary dimension."""
    dimension: str
    label: str
    label_ko: str
    color: str
    correct: int
    total: int
    score: int | None = None  # 0-100 percentage, None if no items


class TestResultsResponse(BaseModel):
    """Full diagnostic report."""
    session_id: str
    theta: float
    se: float
    reliability: float
    cefr_level: str
    cefr_probabilities: CEFRProbabilities
    curriculum_level: str
    vocab_size_estimate: int
    total_items: int
    total_correct: int
    accuracy: float
    termination_reason: str
    topic_strengths: list[TopicAnalysis]
    topic_weaknesses: list[TopicAnalysis]
    dimension_scores: list[DimensionScore] = []
    oxford_coverage: float = 0.0
    estimated_vocabulary: int = 0


class UserHistoryEntry(BaseModel):
    """A single test session in user history."""
    session_id: str
    started_at: str
    completed_at: str | None
    final_theta: float | None
    cefr_level: str | None
    curriculum_level: str | None
    vocab_size_estimate: int | None
    total_items: int | None
    accuracy: float | None


class UserHistoryResponse(BaseModel):
    """User's test history."""
    user_id: str
    total_sessions: int
    sessions: list[UserHistoryEntry]


class RecalibrateResponse(BaseModel):
    """Response from parameter recalibration."""
    items_recalibrated: int
    message: str


# ── Vocabulary Matrix Models ──

class MatrixWord(BaseModel):
    """A single word in the vocabulary matrix."""
    word: str
    meaning_ko: str
    cefr: str
    pos: str
    freq_rank: int
    current_state: str
    current_probability: float
    goal_state: str
    goal_probability: float
    has_irt_params: bool


class MatrixStateCounts(BaseModel):
    """Count of words in each knowledge state."""
    not_known: int = 0
    emerging: int = 0
    developing: int = 0
    comfortable: int = 0
    mastered: int = 0


class MatrixSummary(BaseModel):
    """Summary statistics for the matrix."""
    counts: MatrixStateCounts
    total: int


class MatrixGoalSummary(BaseModel):
    """Summary for the goal state."""
    counts: MatrixStateCounts
    total: int
    words_changed: int


class KnowledgeState(BaseModel):
    """Knowledge state definition."""
    key: str
    label: str
    label_ko: str
    color: str
    min_p: float
    max_p: float


class VocabMatrixResponse(BaseModel):
    """Full vocabulary matrix response."""
    words: list[MatrixWord]
    total_sampled: int
    current_theta: float
    goal_theta: float
    goal_cefr: str
    summary: MatrixSummary
    goal_summary: MatrixGoalSummary
    states: list[KnowledgeState]
