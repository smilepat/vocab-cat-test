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

export default function SurveyScreen({ onStart, loading }: Props) {
  const { lang } = useLang();
  const [nickname, setNickname] = useState("");
  const [grade, setGrade] = useState("중2");
  const [selfAssess, setSelfAssess] = useState("intermediate");
  const [examExp, setExamExp] = useState("none");
  const [questionType, setQuestionType] = useState(0);

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
      <h1>{t("appTitle", lang)}</h1>
      <p className="subtitle">{t("surveySubtitle", lang)}</p>

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

        <button type="submit" className="primary-btn" disabled={loading}>
          {loading ? t("loadingBtn", lang) : t("startBtn", lang)}
        </button>
      </form>
    </div>
  );
}
