import { useState } from "react";
import { useLang } from "../i18n/LangContext";
import { t } from "../i18n/translations";
import type { TranslationKey } from "../i18n/translations";

interface Props {
  onStart: (profile: {
    nickname: string;
    grade: string;
    self_assess: string;
    exam_experience: string;
    question_type: number;
  }) => void;
  onStartGoalLearning: (goal: { id: string; name: string; count: number; nickname?: string }) => void;
  loading: boolean;
}

const GRADE_VALUES = [
  "초3-4", "초5-6", "중1", "중2", "중3", "고1", "고2", "고3", "대학", "성인",
] as const;

const SELF_ASSESS_VALUES = [
  { value: "beginner", labelKey: "beginner" as TranslationKey, descKey: "beginnerDesc" as TranslationKey },
  { value: "intermediate", labelKey: "intermediate" as TranslationKey, descKey: "intermediateDesc" as TranslationKey },
  { value: "advanced", labelKey: "advanced" as TranslationKey, descKey: "advancedDesc" as TranslationKey },
];

const EXAM_VALUES = [
  { value: "none", labelKey: "examNone" as TranslationKey },
  { value: "내신", labelKey: "exam내신" as TranslationKey },
  { value: "수능", labelKey: "exam수능" as TranslationKey },
  { value: "TOEIC", labelKey: "examTOEIC" as TranslationKey },
  { value: "TOEFL", labelKey: "examTOEFL" as TranslationKey },
];

const QUESTION_TYPE_VALUES = [
  { value: 0, labelKey: "qtype.0" as TranslationKey },
  { value: 1, labelKey: "qtype.1" as TranslationKey },
  { value: 2, labelKey: "qtype.2" as TranslationKey },
  { value: 3, labelKey: "qtype.3" as TranslationKey },
  { value: 4, labelKey: "qtype.4" as TranslationKey },
  { value: 5, labelKey: "qtype.5" as TranslationKey },
  { value: 6, labelKey: "qtype.6" as TranslationKey },
];

const LEARNING_GOALS = [
  { id: "elementary", name: "초등 어휘", nameEn: "Elementary Vocabulary", count: 800, available: true },
  { id: "middle", name: "중학교과 어휘", nameEn: "Middle School Vocabulary", count: 1200, available: true },
  { id: "high", name: "고등학교 어휘", nameEn: "High School Vocabulary", count: 1000, available: true },
  { id: "suneung", name: "수능 어휘", nameEn: "CSAT Vocabulary", count: 5000, available: true },
  { id: "toeic", name: "토익 어휘", nameEn: "TOEIC Vocabulary", count: 0, available: false },
  { id: "toefl", name: "토플 어휘", nameEn: "TOEFL Vocabulary", count: 0, available: false },
];

export default function SurveyScreen({ onStart, onStartGoalLearning, loading }: Props) {
  const { lang } = useLang();
  const [nickname, setNickname] = useState("");
  const [grade, setGrade] = useState("중2");
  const [selfAssess, setSelfAssess] = useState("intermediate");
  const [examExp, setExamExp] = useState("none");
  const [questionType, setQuestionType] = useState(0);
  const [showGoalModal, setShowGoalModal] = useState(false);
  const [selectedGoal, setSelectedGoal] = useState<typeof LEARNING_GOALS[0] | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onStart({
      nickname: nickname || (lang === "ko" ? "익명" : "Anonymous"),
      grade,
      self_assess: selfAssess,
      exam_experience: examExp,
      question_type: questionType,
    });
  };

  return (
    <div className="screen survey">
      <div style={{ display: "flex", alignItems: "flex-start", gap: "16px", marginBottom: "12px", flexWrap: "wrap" }}>
        <div style={{ flex: "1", minWidth: "200px" }}>
          <h1 style={{ marginBottom: "8px" }}>{t("appTitle", lang)}</h1>
          <p className="subtitle" style={{ marginBottom: "0" }}>{t("surveySubtitle", lang)}</p>
        </div>
        <button
          type="button"
          className="goal-quick-btn"
          onClick={() => setShowGoalModal(true)}
          style={{
            padding: "12px 20px",
            border: "2px solid var(--primary)",
            borderRadius: "10px",
            background: selectedGoal ? "#eef2ff" : "white",
            color: "var(--primary)",
            cursor: "pointer",
            fontSize: "14px",
            fontWeight: "600",
            transition: "all 0.2s",
            whiteSpace: "nowrap",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "4px",
            minWidth: "180px",
          }}
        >
          <div style={{ fontSize: "16px" }}>📚</div>
          <div>{lang === "ko" ? "테스트 없이" : "Skip Test"}</div>
          <div>{lang === "ko" ? "학습목표 설정하기" : "Set Learning Goal"}</div>
          {selectedGoal && (
            <div style={{ fontSize: "12px", marginTop: "4px", color: "var(--primary)", fontWeight: "700" }}>
              ✓ {lang === "ko" ? selectedGoal.name : selectedGoal.nameEn}
            </div>
          )}
        </button>
      </div>

      <div className="feature-cards">
        <div className="feature-card">
          <div className="feature-icon">&#9881;</div>
          <div className="feature-text">
            <strong>{t("feature.adaptiveTitle", lang)}</strong>
            <span>{t("feature.adaptiveDesc", lang)}</span>
          </div>
        </div>
        <div className="feature-card">
          <div className="feature-icon">&#9733;</div>
          <div className="feature-text">
            <strong>{t("feature.dimensionTitle", lang)}</strong>
            <span>{t("feature.dimensionDesc", lang)}</span>
          </div>
        </div>
        <div className="feature-card">
          <div className="feature-icon">&#9998;</div>
          <div className="feature-text">
            <strong>{t("feature.recommendTitle", lang)}</strong>
            <span>{t("feature.recommendDesc", lang)}</span>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="field">
          <label>{t("nickname", lang)}</label>
          <input
            type="text"
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
            placeholder={t("nicknamePlaceholder", lang)}
          />
        </div>

        <div className="field">
          <label>{t("gradeLabel", lang)}</label>
          <div className="option-grid">
            {GRADE_VALUES.map((g) => (
              <button
                key={g}
                type="button"
                className={`option-btn ${grade === g ? "selected" : ""}`}
                onClick={() => setGrade(g)}
              >
                {t(`grade.${g}` as TranslationKey, lang)}
              </button>
            ))}
          </div>
        </div>

        <div className="field">
          <label>{t("selfAssessLabel", lang)}</label>
          <div className="option-grid cols-3">
            {SELF_ASSESS_VALUES.map((s) => (
              <button
                key={s.value}
                type="button"
                className={`option-btn tall ${selfAssess === s.value ? "selected" : ""}`}
                onClick={() => setSelfAssess(s.value)}
              >
                <strong>{t(s.labelKey, lang)}</strong>
                <span className="desc">{t(s.descKey, lang)}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="field">
          <label>{t("examLabel", lang)}</label>
          <div className="option-grid cols-5">
            {EXAM_VALUES.map((e) => (
              <button
                key={e.value}
                type="button"
                className={`option-btn ${examExp === e.value ? "selected" : ""}`}
                onClick={() => setExamExp(e.value)}
              >
                {t(e.labelKey, lang)}
              </button>
            ))}
          </div>
        </div>

        <div className="field">
          <label>{t("questionTypeLabel", lang)}</label>
          <div className="option-grid">
            {QUESTION_TYPE_VALUES.map((qt) => (
              <button
                key={qt.value}
                type="button"
                className={`option-btn ${questionType === qt.value ? "selected" : ""}`}
                onClick={() => setQuestionType(qt.value)}
              >
                {t(qt.labelKey, lang)}
              </button>
            ))}
          </div>
        </div>

        {selectedGoal ? (
          <>
            <button
              type="button"
              className="primary-btn"
              onClick={() => {
                onStartGoalLearning({
                  id: selectedGoal.id,
                  name: lang === "ko" ? selectedGoal.name : selectedGoal.nameEn,
                  count: selectedGoal.count,
                  nickname: nickname || (lang === "ko" ? "익명" : "Anonymous"),
                });
              }}
              disabled={loading}
              style={{ marginTop: "16px" }}
            >
              {loading ? t("loadingBtn", lang) : (lang === "ko" ? "🎯 학습 진행" : "🎯 Start Learning")}
            </button>
            <button type="submit" className="secondary-btn" disabled={loading} style={{ marginTop: "12px" }}>
              {loading ? t("loadingBtn", lang) : (lang === "ko" ? "📊 IRT 어휘 진단 테스트" : "📊 IRT Diagnostic Test")}
            </button>
          </>
        ) : (
          <button type="submit" className="primary-btn" disabled={loading}>
            {loading ? t("loadingBtn", lang) : t("startBtn", lang)}
          </button>
        )}
      </form>

      {/* Learning Goal Modal */}
      {showGoalModal && (
        <div className="matrix-modal-overlay" onClick={() => setShowGoalModal(false)}>
          <div className="matrix-modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: "500px" }}>
            <button
              className="matrix-modal-close"
              onClick={() => setShowGoalModal(false)}
            >
              ×
            </button>
            <h2 style={{ fontSize: "22px", fontWeight: "700", marginBottom: "8px" }}>
              {lang === "ko" ? "학습 목표 선택" : "Choose Learning Goal"}
            </h2>
            <p style={{ fontSize: "14px", color: "var(--text-sub)", marginBottom: "20px" }}>
              {lang === "ko"
                ? "진단 테스트 없이 바로 어휘 학습을 시작할 수 있습니다."
                : "Start learning vocabulary directly without a diagnostic test."}
            </p>

            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {LEARNING_GOALS.map((goal) => (
                <button
                  key={goal.id}
                  className={`goal-card ${!goal.available ? "disabled" : ""}`}
                  disabled={!goal.available}
                  onClick={() => {
                    if (goal.available) {
                      setSelectedGoal(goal);
                      setShowGoalModal(false);
                    }
                  }}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "16px 20px",
                    border: goal.available ? "2px solid var(--border)" : "2px solid #e5e7eb",
                    borderRadius: "12px",
                    background: goal.available ? "var(--card)" : "#f9fafb",
                    cursor: goal.available ? "pointer" : "not-allowed",
                    transition: "all 0.2s",
                    opacity: goal.available ? 1 : 0.5,
                  }}
                  onMouseEnter={(e) => {
                    if (goal.available) {
                      e.currentTarget.style.borderColor = "var(--primary)";
                      e.currentTarget.style.background = "#f8fafc";
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (goal.available) {
                      e.currentTarget.style.borderColor = "var(--border)";
                      e.currentTarget.style.background = "var(--card)";
                    }
                  }}
                >
                  <div style={{ textAlign: "left" }}>
                    <div style={{ fontSize: "16px", fontWeight: "600", marginBottom: "4px" }}>
                      {lang === "ko" ? goal.name : goal.nameEn}
                    </div>
                    <div style={{ fontSize: "13px", color: "var(--text-sub)" }}>
                      {goal.available
                        ? `${goal.count}${lang === "ko" ? "개 단어" : " words"}`
                        : lang === "ko" ? "준비 중..." : "Coming soon..."}
                    </div>
                  </div>
                  {goal.available && (
                    <div style={{ fontSize: "20px", color: "var(--primary)" }}>→</div>
                  )}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
