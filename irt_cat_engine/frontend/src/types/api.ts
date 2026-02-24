export interface TestStartRequest {
  nickname?: string;
  user_id?: string;
  grade: string;
  self_assess: string;
  exam_experience: string;
  question_type: number;
}

export interface ItemResponse {
  item_id: number;
  word: string;
  question_type: number;
  stem: string | null;
  correct_answer: string | null;
  distractors: string[] | null;
  options: string[] | null;
  pos: string;
  cefr: string;
  explanation: string | null;
}

export interface TestProgress {
  items_completed: number;
  total_correct: number;
  accuracy: number;
  current_theta: number;
  current_se: number;
  is_complete: boolean;
}

export interface TestStartResponse {
  session_id: string;
  user_id: string;
  initial_theta: number;
  first_item: ItemResponse;
  progress: TestProgress;
}

export interface CEFRProbabilities {
  A1: number;
  A2: number;
  B1: number;
  B2: number;
  C1: number;
}

export interface TopicAnalysis {
  topic: string;
  correct: number;
  total: number;
  rate: number;
}

export interface DimensionScore {
  dimension: string;
  label: string;
  label_ko: string;
  color: string;
  correct: number;
  total: number;
  score: number | null;
}

export interface TestResults {
  session_id: string;
  theta: number;
  se: number;
  reliability: number;
  cefr_level: string;
  cefr_probabilities: CEFRProbabilities;
  curriculum_level: string;
  vocab_size_estimate: number;
  total_items: number;
  total_correct: number;
  accuracy: number;
  termination_reason: string;
  topic_strengths: TopicAnalysis[];
  topic_weaknesses: TopicAnalysis[];
  dimension_scores: DimensionScore[];
  oxford_coverage: number;
  estimated_vocabulary: number;
}

export interface TestRespondResponse {
  is_complete: boolean;
  progress: TestProgress;
  next_item: ItemResponse | null;
  results: TestResults | null;
}

// Vocabulary Matrix types

export interface MatrixWord {
  word: string;
  meaning_ko: string;
  cefr: string;
  pos: string;
  freq_rank: number;
  current_state: string;
  current_probability: number;
  goal_state: string;
  goal_probability: number;
  has_irt_params: boolean;
}

export interface MatrixStateCounts {
  not_known: number;
  emerging: number;
  developing: number;
  comfortable: number;
  mastered: number;
}

export interface KnowledgeState {
  key: string;
  label: string;
  label_ko: string;
  color: string;
  min_p: number;
  max_p: number;
}

export interface VocabMatrixData {
  words: MatrixWord[];
  total_sampled: number;
  current_theta: number;
  goal_theta: number;
  goal_cefr: string;
  summary: { counts: MatrixStateCounts; total: number };
  goal_summary: { counts: MatrixStateCounts; total: number; words_changed: number };
  states: KnowledgeState[];
}
