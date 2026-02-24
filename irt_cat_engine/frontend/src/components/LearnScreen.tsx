import { useState, useEffect, useCallback } from "react";
import { useLang } from "../i18n/LangContext";
import { t } from "../i18n/translations";
import { apiGet } from "../hooks/useApi";
import StudyCard from "./StudyCard";

interface Exercise {
  id: string;
  dimension: string;
  word: string;
  cefr: string;
  type: string;
  prompt: string;
  prompt_en?: string;
  options: string[];
  correct_index: number;
  explanation: string;
}

interface Recommendation {
  dimension: string;
  label: string;
  label_ko: string;
  color: string;
  score: number | null;
  priority: string;
  tip_ko: string;
  tip_en: string;
  exercises: Exercise[];
}

interface StudyPlan {
  recommendations: Recommendation[];
  total_exercises: number;
  weak_dimensions: string[];
}

interface Props {
  sessionId: string;
  onBack: () => void;
}

export default function LearnScreen({ sessionId, onBack }: Props) {
  const { lang } = useLang();
  const [plan, setPlan] = useState<StudyPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeDim, setActiveDim] = useState<string | null>(null);
  const [completedIds, setCompletedIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    apiGet<StudyPlan>(`/learn/${sessionId}/plan`)
      .then((data) => {
        setPlan(data);
        if (data.recommendations.length > 0) {
          setActiveDim(data.recommendations[0].dimension);
        }
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [sessionId]);

  const handleComplete = useCallback((exerciseId: string) => {
    setCompletedIds((prev) => new Set(prev).add(exerciseId));
  }, []);

  if (loading) {
    return (
      <div className="screen learn">
        <div className="learn-loading">
          <div className="spinner" />
          <p>{lang === "ko" ? "학습 계획 생성 중..." : "Generating study plan..."}</p>
        </div>
      </div>
    );
  }

  if (error || !plan) {
    return (
      <div className="screen learn">
        <div className="learn-empty">
          <p>{error || (lang === "ko" ? "학습 계획을 불러올 수 없습니다." : "Could not load study plan.")}</p>
          <button type="button" className="primary-btn" onClick={onBack}>
            {t("restartBtn", lang)}
          </button>
        </div>
      </div>
    );
  }

  if (plan.recommendations.length === 0) {
    return (
      <div className="screen learn">
        <div className="learn-empty">
          <h2>{lang === "ko" ? "모든 차원이 우수합니다!" : "All dimensions are strong!"}</h2>
          <p>{lang === "ko" ? "모든 영역에서 좋은 성적을 거뒀습니다." : "You scored well in all dimensions."}</p>
          <button type="button" className="primary-btn" onClick={onBack}>
            {t("restartBtn", lang)}
          </button>
        </div>
      </div>
    );
  }

  const activeRec = plan.recommendations.find((r) => r.dimension === activeDim) || plan.recommendations[0];
  const totalCompleted = completedIds.size;
  const progressPct = plan.total_exercises > 0 ? (totalCompleted / plan.total_exercises) * 100 : 0;

  const priorityLabel = (p: string) => {
    if (p === "high") return lang === "ko" ? "집중" : "High";
    if (p === "medium") return lang === "ko" ? "보통" : "Medium";
    return lang === "ko" ? "복습" : "Review";
  };

  return (
    <div className="screen learn">
      <div className="learn-header">
        <h1>{lang === "ko" ? "맞춤 학습 계획" : "Personalized Study Plan"}</h1>
        <div className="learn-progress">
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progressPct}%`, background: "#10b981" }} />
          </div>
          <span className="learn-progress-text">
            {totalCompleted}/{plan.total_exercises}
          </span>
        </div>
      </div>

      {/* Dimension tabs */}
      <div className="dimension-tabs">
        {plan.recommendations.map((rec) => {
          const isActive = rec.dimension === activeDim;
          const dimCompleted = rec.exercises.filter((e) => completedIds.has(e.id)).length;
          const allDone = dimCompleted === rec.exercises.length;
          return (
            <button
              type="button"
              key={rec.dimension}
              className={`dimension-tab${isActive ? " active" : ""}${allDone ? " done" : ""}`}
              style={isActive ? { borderColor: rec.color, color: rec.color } : {}}
              onClick={() => setActiveDim(rec.dimension)}
            >
              {lang === "ko" ? rec.label_ko : rec.label}
              <span className={`priority-badge ${rec.priority}`}>{priorityLabel(rec.priority)}</span>
            </button>
          );
        })}
      </div>

      {/* Active dimension section */}
      <div className="learn-section">
        <div className="learn-section-header">
          <span className="dimension-dot" style={{ backgroundColor: activeRec.color }} />
          <h2>{lang === "ko" ? activeRec.label_ko : activeRec.label}</h2>
          {activeRec.score != null && (
            <span className="learn-score" style={{ color: activeRec.color }}>
              {activeRec.score}%
            </span>
          )}
        </div>
        <p className="learn-tip">{lang === "ko" ? activeRec.tip_ko : activeRec.tip_en}</p>

        <div className="study-cards">
          {activeRec.exercises.map((ex) => (
            <StudyCard
              key={ex.id}
              exercise={ex}
              color={activeRec.color}
              completed={completedIds.has(ex.id)}
              onComplete={handleComplete}
            />
          ))}
        </div>
      </div>

      <button type="button" className="primary-btn" onClick={onBack} style={{ marginTop: 24 }}>
        {t("restartBtn", lang)}
      </button>
    </div>
  );
}
