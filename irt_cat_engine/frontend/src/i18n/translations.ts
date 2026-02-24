export type Lang = "ko" | "en";

export const translations = {
  // App-level
  appTitle: { ko: "IRT 어휘 진단 테스트", en: "IRT Vocabulary Diagnostic Test" },
  langSwitch: { ko: "English", en: "한국어" },
  serverError: { ko: "서버 연결 실패", en: "Server connection failed" },
  responseFailed: { ko: "응답 전송 실패", en: "Failed to submit response" },

  // Survey Screen
  surveySubtitle: {
    ko: "적응형 검사로 영어 어휘력을 정밀하게 측정합니다",
    en: "Precisely measure your English vocabulary with adaptive testing",
  },
  nickname: { ko: "닉네임", en: "Nickname" },
  nicknamePlaceholder: { ko: "닉네임을 입력하세요 (선택)", en: "Enter nickname (optional)" },
  gradeLabel: { ko: "학년", en: "Grade Level" },
  selfAssessLabel: { ko: "영어 어휘 수준 자기평가", en: "Self-assessed Vocabulary Level" },
  examLabel: { ko: "영어 시험 경험", en: "Exam Experience" },
  startBtn: { ko: "테스트 시작", en: "Start Test" },
  loadingBtn: { ko: "준비 중...", en: "Loading..." },

  // Grades
  "grade.초3-4": { ko: "초등 3-4학년", en: "Elem 3-4" },
  "grade.초5-6": { ko: "초등 5-6학년", en: "Elem 5-6" },
  "grade.중1": { ko: "중학교 1학년", en: "Middle 1" },
  "grade.중2": { ko: "중학교 2학년", en: "Middle 2" },
  "grade.중3": { ko: "중학교 3학년", en: "Middle 3" },
  "grade.고1": { ko: "고등학교 1학년", en: "High 1" },
  "grade.고2": { ko: "고등학교 2학년", en: "High 2" },
  "grade.고3": { ko: "고등학교 3학년", en: "High 3" },
  "grade.대학": { ko: "대학생", en: "College" },
  "grade.성인": { ko: "성인", en: "Adult" },

  // Self-assess
  beginner: { ko: "초급", en: "Beginner" },
  beginnerDesc: { ko: "기본 단어만 알고 있어요", en: "I know only basic words" },
  intermediate: { ko: "중급", en: "Intermediate" },
  intermediateDesc: { ko: "일상 단어는 대부분 알아요", en: "I know most everyday words" },
  advanced: { ko: "고급", en: "Advanced" },
  advancedDesc: { ko: "학술/전문 단어도 잘 알아요", en: "I know academic/specialized words" },

  // Exam experience
  examNone: { ko: "없음", en: "None" },
  exam내신: { ko: "내신 시험", en: "School Exam" },
  exam수능: { ko: "수능", en: "CSAT" },
  examTOEIC: { ko: "TOEIC", en: "TOEIC" },
  examTOEFL: { ko: "TOEFL", en: "TOEFL" },

  // Question type selection
  questionTypeLabel: { ko: "문항 유형", en: "Question Type" },
  "qtype.0": { ko: "혼합 (추천)", en: "Mixed (Recommended)" },
  "qtypeDesc.0": {
    ko: "다양한 유형의 문항으로 종합 평가",
    en: "Comprehensive assessment with various question types",
  },

  // Test Screen
  questionNum: { ko: "번 문항", en: " " },
  accuracyLabel: { ko: "정답률", en: "Accuracy" },
  "qtype.1": { ko: "한국어 뜻 고르기", en: "Korean Meaning" },
  "qtype.2": { ko: "영어 정의 매칭", en: "English Definition" },
  "qtype.3": { ko: "동의어 선택", en: "Synonym" },
  "qtype.4": { ko: "반의어 선택", en: "Antonym" },
  "qtype.5": { ko: "문장 빈칸 채우기", en: "Sentence Fill" },
  "qtype.6": { ko: "연어 판단", en: "Collocation" },
  dontKnow: { ko: "모름", en: "Don't Know" },

  // Results Screen
  resultsTitle: { ko: "진단 결과", en: "Diagnostic Results" },
  cefrLevel: { ko: "CEFR 레벨", en: "CEFR Level" },
  reliabilityLabel: { ko: "신뢰도", en: "Reliability" },
  vocabSize: { ko: "추정 어휘 크기", en: "Estimated Vocabulary" },
  vocabTotal: { ko: "/ 9,183 단어", en: "/ 9,183 words" },
  curriculumLevel: { ko: "교육과정 수준", en: "Curriculum Level" },
  accuracy: { ko: "정답률", en: "Accuracy" },
  itemsLabel: { ko: "문항", en: "items" },
  cefrDist: { ko: "CEFR 확률 분포", en: "CEFR Probability Distribution" },
  strengths: { ko: "강점 영역", en: "Strengths" },
  weaknesses: { ko: "보완 영역", en: "Areas to Improve" },
  measureDetails: { ko: "측정 상세", en: "Measurement Details" },
  thetaLabel: { ko: "능력 추정치 (theta)", en: "Ability Estimate (theta)" },
  seLabel: { ko: "표준 오차 (SE)", en: "Standard Error (SE)" },
  terminationLabel: { ko: "종료 사유", en: "Termination Reason" },
  restartBtn: { ko: "다시 테스트하기", en: "Restart Test" },

  // 5D Dimension Analysis
  dimensionProfile: { ko: "5차원 어휘 프로필", en: "5D Vocabulary Profile" },
  dimensionBreakdown: { ko: "차원별 상세", en: "Dimension Breakdown" },
  insights: { ko: "분석 인사이트", en: "Insights" },
  strongestDim: { ko: "강점 차원", en: "Strongest" },
  focusDim: { ko: "집중 필요", en: "Focus Area" },
  noData: { ko: "데이터 부족", en: "No data" },
  startLearning: { ko: "학습 시작", en: "Start Learning" },

  // Test Screen — answer feedback
  nextQuestion: { ko: "다음 문항", en: "Next Question" },
  seeResults: { ko: "결과 보기", en: "See Results" },

  // Learn Screen
  gotIt: { ko: "확인", en: "Got it!" },

  // History
  previousAttempts: { ko: "이전 테스트 기록", en: "Previous Attempts" },

  // Phase 7 — Tabs
  tabOverview: { ko: "종합", en: "Overview" },
  tabAnalysis: { ko: "분석", en: "Analysis" },
  tabLearning: { ko: "학습", en: "Learning" },

  // Phase 7 — Hero card
  yourVocabLevel: { ko: "영어 어휘 수준", en: "Your English Vocabulary Level" },
  estimatedVocab: { ko: "추정 어휘 수", en: "Estimated Vocabulary" },
  wordsKnown: { ko: "단어", en: "words" },

  // Phase 7 — Feature cards (SurveyScreen)
  "feature.adaptiveTitle": { ko: "적응형 테스트", en: "Adaptive Testing" },
  "feature.adaptiveDesc": {
    ko: "AI가 실력에 맞춰 문제 난이도를 실시간으로 조절합니다",
    en: "AI adjusts question difficulty in real-time based on your level",
  },
  "feature.dimensionTitle": { ko: "5차원 분석", en: "5D Analysis" },
  "feature.dimensionDesc": {
    ko: "의미·문맥·형태·관계·화용 5가지 차원으로 어휘력을 분석합니다",
    en: "Analyzes vocabulary across 5 dimensions: semantic, contextual, form, relational, pragmatic",
  },
  "feature.recommendTitle": { ko: "맞춤 학습", en: "Personalized Learning" },
  "feature.recommendDesc": {
    ko: "약점 기반 맞춤 학습 계획을 제공합니다",
    en: "Provides a study plan tailored to your weak areas",
  },

  // Phase 7 — Weekly plan
  weeklyPlan: { ko: "주간 학습 로드맵", en: "Weekly Study Roadmap" },
  week: { ko: "주차", en: "Week" },
  dailyTarget: { ko: "일일 목표", en: "Daily Target" },
  exercises: { ko: "연습", en: "exercises" },
  retestRecommended: { ko: "재테스트 권장", en: "Retest Recommended" },

  // Matrix tab
  tabMatrix: { ko: "어휘 매트릭스", en: "Matrix" },
} as const;

export type TranslationKey = keyof typeof translations;

export function t(key: TranslationKey, lang: Lang): string {
  return translations[key][lang];
}
