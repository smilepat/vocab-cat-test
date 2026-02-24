import { useState, useEffect, useCallback } from "react";
import { useLang } from "../i18n/LangContext";
import { t } from "../i18n/translations";
import { apiGet } from "../hooks/useApi";
import RadarChart from "./RadarChart";
import StudyCard from "./StudyCard";
import VocabMatrix from "./VocabMatrix";
import type { TestResults, VocabMatrixData } from "../types/api";

interface HistoryEntry {
  session_id: string;
  started_at: string;
  completed_at: string | null;
  cefr_level: string | null;
  accuracy: number | null;
  total_items: number | null;
  vocab_size_estimate: number | null;
}

interface UserHistory {
  user_id: string;
  total_sessions: number;
  sessions: HistoryEntry[];
}

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

interface WeekPlan {
  week: number;
  focus: string[];
  focus_labels: string[];
  daily_target: number;
  description_ko: string;
  description_en: string;
}

interface StudyPlan {
  recommendations: Recommendation[];
  total_exercises: number;
  weak_dimensions: string[];
  weekly_plan?: WeekPlan[];
}

type ResultTab = "overview" | "analysis" | "learning" | "matrix";

interface Props {
  results: TestResults;
  sessionId: string;
  userId?: string;
  onRestart: () => void;
}

const CEFR_GRADIENTS: Record<string, string> = {
  A1: "linear-gradient(135deg, #22c55e 0%, #16a34a 100%)",
  A2: "linear-gradient(135deg, #84cc16 0%, #65a30d 100%)",
  B1: "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
  B2: "linear-gradient(135deg, #f97316 0%, #ea580c 100%)",
  C1: "linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)",
};

export default function ResultsScreen({ results, sessionId, userId, onRestart }: Props) {
  const { lang } = useLang();
  const [activeTab, setActiveTab] = useState<ResultTab>("overview");
  const [history, setHistory] = useState<HistoryEntry[]>([]);

  // Learning tab state
  const [plan, setPlan] = useState<StudyPlan | null>(null);
  const [planLoading, setPlanLoading] = useState(false);
  const [planError, setPlanError] = useState<string | null>(null);
  const [activeDim, setActiveDim] = useState<string | null>(null);
  const [completedIds, setCompletedIds] = useState<Set<string>>(new Set());

  // Matrix tab state
  const [matrixData, setMatrixData] = useState<VocabMatrixData | null>(null);
  const [matrixLoading, setMatrixLoading] = useState(false);
  const [matrixError, setMatrixError] = useState<string | null>(null);

  // Load history
  useEffect(() => {
    if (!userId) return;
    apiGet<UserHistory>(`/user/${userId}/history`)
      .then((data) => {
        const prev = data.sessions
          .filter((s) => s.session_id !== results.session_id && s.completed_at)
          .slice(-5)
          .reverse();
        setHistory(prev);
      })
      .catch(() => {});
  }, [userId, results.session_id]);

  // Load study plan when learning tab is first activated
  useEffect(() => {
    if (activeTab !== "learning" || plan || planLoading) return;
    setPlanLoading(true);
    apiGet<StudyPlan>(`/learn/${sessionId}/plan`)
      .then((data) => {
        setPlan(data);
        if (data.recommendations.length > 0) {
          setActiveDim(data.recommendations[0].dimension);
        }
      })
      .catch((e) => setPlanError(e.message))
      .finally(() => setPlanLoading(false));
  }, [activeTab, sessionId, plan, planLoading]);

  // Load matrix data when matrix tab is first activated
  useEffect(() => {
    if (activeTab !== "matrix" || matrixData || matrixLoading) return;
    setMatrixLoading(true);
    apiGet<VocabMatrixData>(`/learn/${sessionId}/matrix`)
      .then((data) => setMatrixData(data))
      .catch((e) => setMatrixError(e.message))
      .finally(() => setMatrixLoading(false));
  }, [activeTab, sessionId, matrixData, matrixLoading]);

  const handleComplete = useCallback((exerciseId: string) => {
    setCompletedIds((prev) => new Set(prev).add(exerciseId));
  }, []);

  const cefrColors: Record<string, string> = {
    A1: "#4caf50", A2: "#8bc34a", B1: "#ff9800", B2: "#ff5722", C1: "#9c27b0",
  };

  const cefrProbs = results.cefr_probabilities;
  const maxProb = Math.max(cefrProbs.A1, cefrProbs.A2, cefrProbs.B1, cefrProbs.B2, cefrProbs.C1);

  // 5D dimension analysis
  const dimScores = results.dimension_scores || [];
  const withData = dimScores.filter((d) => d.score != null);
  const strongest = withData.length > 0
    ? withData.reduce((a, b) => ((a.score ?? 0) > (b.score ?? 0) ? a : b))
    : null;
  const weakest = withData.length > 0
    ? withData.reduce((a, b) => ((a.score ?? 0) < (b.score ?? 0) ? a : b))
    : null;

  const tabs: { key: ResultTab; label: string }[] = [
    { key: "overview", label: t("tabOverview", lang) },
    { key: "analysis", label: t("tabAnalysis", lang) },
    { key: "learning", label: t("tabLearning", lang) },
    { key: "matrix", label: t("tabMatrix", lang) },
  ];

  return (
    <div className="screen results">
      <h1>{t("resultsTitle", lang)}</h1>

      {/* Tab navigation */}
      <div className="results-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            type="button"
            className={`results-tab${activeTab === tab.key ? " active" : ""}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── Overview Tab ── */}
      {activeTab === "overview" && (
        <div className="tab-content">
          {/* Hero Card */}
          <div
            className="hero-card"
            style={{ background: CEFR_GRADIENTS[results.cefr_level] || CEFR_GRADIENTS.B1 }}
          >
            <div className="hero-label">{t("yourVocabLevel", lang)}</div>
            <div className="hero-cefr">{results.cefr_level}</div>
            <div className="hero-details">
              <div className="hero-detail">
                <span className="hero-detail-value">
                  {results.vocab_size_estimate.toLocaleString()}
                </span>
                <span className="hero-detail-label">{t("estimatedVocab", lang)}</span>
              </div>
              <div className="hero-divider" />
              <div className="hero-detail">
                <span className="hero-detail-value">
                  {Math.round(results.accuracy * 100)}%
                </span>
                <span className="hero-detail-label">{t("accuracy", lang)}</span>
              </div>
              <div className="hero-divider" />
              <div className="hero-detail">
                <span className="hero-detail-value">
                  {Math.round(results.reliability * 100)}%
                </span>
                <span className="hero-detail-label">{t("reliabilityLabel", lang)}</span>
              </div>
            </div>
          </div>

          {/* 5D Radar Chart */}
          {dimScores.length > 0 && (
            <div className="section radar-section">
              <h2>{t("dimensionProfile", lang)}</h2>
              <RadarChart scores={dimScores} size={300} />
            </div>
          )}

          {/* Oxford 3000 Coverage */}
          {results.oxford_coverage > 0 && (
            <div className="section oxford-section">
              <h2>{lang === "ko" ? "핵심 어휘 커버리지" : "Core Vocabulary Coverage"}</h2>
              <div className="oxford-coverage">
                <svg className="coverage-circle" viewBox="0 0 120 120">
                  <circle cx="60" cy="60" r="50" fill="none" stroke="#e2e8f0" strokeWidth="10" />
                  <circle
                    cx="60" cy="60" r="50" fill="none"
                    stroke="#3b82f6" strokeWidth="10"
                    strokeDasharray={`${results.oxford_coverage * 314} 314`}
                    strokeLinecap="round"
                    transform="rotate(-90 60 60)"
                  />
                  <text x="60" y="56" textAnchor="middle" fontSize="24" fontWeight="700" fill="#1e293b">
                    {Math.round(results.oxford_coverage * 100)}%
                  </text>
                  <text x="60" y="74" textAnchor="middle" fontSize="10" fill="#64748b">
                    {lang === "ko" ? "추정 커버리지" : "Est. Coverage"}
                  </text>
                </svg>
                <p className="oxford-desc">
                  {lang === "ko"
                    ? "A1~B1 핵심 어휘 중 알고 있을 것으로 추정되는 비율"
                    : "Estimated proportion of core A1-B1 vocabulary you know"}
                </p>
              </div>
            </div>
          )}

          {/* Insights */}
          {strongest && weakest && strongest.dimension !== weakest.dimension && (
            <div className="section">
              <h2>{t("insights", lang)}</h2>
              <div className="insight-list">
                <div className="insight-item">
                  <span className="insight-icon up">&#9650;</span>
                  <p>
                    <strong>{t("strongestDim", lang)}:</strong>{" "}
                    {lang === "ko" ? strongest.label_ko : strongest.label} ({strongest.score}%)
                  </p>
                </div>
                <div className="insight-item">
                  <span className="insight-icon down">&#9660;</span>
                  <p>
                    <strong>{t("focusDim", lang)}:</strong>{" "}
                    {lang === "ko" ? weakest.label_ko : weakest.label} ({weakest.score}%)
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* CEFR Distribution */}
          <div className="section">
            <h2>{t("cefrDist", lang)}</h2>
            <div className="cefr-bars">
              {(["A1", "A2", "B1", "B2", "C1"] as const).map((level) => {
                const prob = cefrProbs[level];
                return (
                  <div className="cefr-bar-row" key={level}>
                    <span className="cefr-label">{level}</span>
                    <div className="cefr-bar-bg">
                      <div
                        className="cefr-bar-fill"
                        style={{
                          width: `${(prob / maxProb) * 100}%`,
                          backgroundColor: cefrColors[level],
                          opacity: prob > 0.1 ? 1 : 0.4,
                        }}
                      />
                    </div>
                    <span className="cefr-pct">{Math.round(prob * 100)}%</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* ── Analysis Tab ── */}
      {activeTab === "analysis" && (
        <div className="tab-content">
          {/* Dimension Breakdown */}
          {withData.length > 0 && (
            <div className="section">
              <h2>{t("dimensionBreakdown", lang)}</h2>
              <div className="dimension-bars">
                {dimScores.map((d) => (
                  <div key={d.dimension} className="dimension-bar-row">
                    <div className="dimension-bar-header">
                      <span className="dimension-bar-label">
                        <span className="dimension-dot" style={{ backgroundColor: d.color }} />
                        {lang === "ko" ? d.label_ko : d.label}
                      </span>
                      <span className="dimension-bar-score" style={{ color: d.color }}>
                        {d.score != null ? (
                          <>{d.correct}/{d.total} &middot; {d.score}%</>
                        ) : (
                          <span className="no-data">{t("noData", lang)}</span>
                        )}
                      </span>
                    </div>
                    <div className="dimension-bar-bg">
                      <div
                        className="dimension-bar-fill"
                        style={{
                          width: `${d.score ?? 0}%`,
                          backgroundColor: d.color,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Summary cards */}
          <div className="result-cards">
            <div className="result-card">
              <div className="card-label">{t("vocabSize", lang)}</div>
              <div className="card-value">
                {results.vocab_size_estimate.toLocaleString()}
              </div>
              <div className="card-sub">{t("vocabTotal", lang)}</div>
            </div>

            <div className="result-card">
              <div className="card-label">{t("curriculumLevel", lang)}</div>
              <div className="card-value small">{results.curriculum_level}</div>
            </div>
          </div>

          {results.topic_strengths.length > 0 && (
            <div className="section">
              <h2>{t("strengths", lang)}</h2>
              <div className="topic-list">
                {results.topic_strengths.map((tp) => (
                  <div className="topic-item strength" key={tp.topic}>
                    <span>{tp.topic}</span>
                    <span>
                      {tp.correct}/{tp.total} ({Math.round(tp.rate * 100)}%)
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {results.topic_weaknesses.length > 0 && (
            <div className="section">
              <h2>{t("weaknesses", lang)}</h2>
              <div className="topic-list">
                {results.topic_weaknesses.map((tp) => (
                  <div className="topic-item weakness" key={tp.topic}>
                    <span>{tp.topic}</span>
                    <span>
                      {tp.correct}/{tp.total} ({Math.round(tp.rate * 100)}%)
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="section stats">
            <h2>{t("measureDetails", lang)}</h2>
            <table>
              <tbody>
                <tr><td>{t("thetaLabel", lang)}</td><td>{results.theta.toFixed(3)}</td></tr>
                <tr><td>{t("seLabel", lang)}</td><td>{results.se.toFixed(3)}</td></tr>
                <tr><td>{t("terminationLabel", lang)}</td><td>{results.termination_reason}</td></tr>
              </tbody>
            </table>
          </div>

          {/* Test History */}
          {history.length > 0 && (
            <div className="section">
              <h2>{t("previousAttempts", lang)}</h2>
              <div className="history-list">
                {history.map((h) => (
                  <div className="history-item" key={h.session_id}>
                    <span className="history-date">
                      {new Date(h.started_at).toLocaleDateString(lang === "ko" ? "ko-KR" : "en-US", {
                        month: "short",
                        day: "numeric",
                      })}
                    </span>
                    <span className="history-cefr" style={{ color: cefrColors[h.cefr_level ?? ""] || "#333" }}>
                      {h.cefr_level ?? "-"}
                    </span>
                    <span className="history-accuracy">
                      {h.accuracy != null ? `${Math.round(h.accuracy * 100)}%` : "-"}
                    </span>
                    <span className="history-items">
                      {h.total_items ?? "-"} {t("itemsLabel", lang)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Learning Tab ── */}
      {activeTab === "learning" && (
        <div className="tab-content">
          {planLoading && (
            <div className="learn-loading">
              <div className="spinner" />
              <p>{lang === "ko" ? "학습 계획 생성 중..." : "Generating study plan..."}</p>
            </div>
          )}

          {planError && (
            <div className="learn-empty">
              <p>{planError}</p>
            </div>
          )}

          {plan && plan.recommendations.length === 0 && (
            <div className="learn-empty">
              <h2>{lang === "ko" ? "모든 차원이 우수합니다!" : "All dimensions are strong!"}</h2>
              <p>{lang === "ko" ? "모든 영역에서 좋은 성적을 거뒀습니다." : "You scored well in all dimensions."}</p>
            </div>
          )}

          {plan && plan.recommendations.length > 0 && (() => {
            const activeRec = plan.recommendations.find((r) => r.dimension === activeDim) || plan.recommendations[0];
            const totalCompleted = completedIds.size;
            const progressPct = plan.total_exercises > 0 ? (totalCompleted / plan.total_exercises) * 100 : 0;
            const priorityLabel = (p: string) => {
              if (p === "high") return lang === "ko" ? "집중" : "High";
              if (p === "medium") return lang === "ko" ? "보통" : "Medium";
              return lang === "ko" ? "복습" : "Review";
            };

            return (
              <>
                <div className="learn-header">
                  <div className="learn-progress">
                    <div className="progress-bar">
                      <div className="progress-fill" style={{ width: `${progressPct}%`, background: "#10b981" }} />
                    </div>
                    <span className="learn-progress-text">
                      {totalCompleted}/{plan.total_exercises}
                    </span>
                  </div>
                </div>

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

                {/* Weekly Roadmap */}
                {plan.weekly_plan && plan.weekly_plan.length > 0 && (
                  <div className="section weekly-plan">
                    <h2>{t("weeklyPlan", lang)}</h2>
                    <div className="week-cards">
                      {plan.weekly_plan.map((w) => (
                        <div key={w.week} className={`week-card${w.week === 1 ? " current" : ""}`}>
                          <div className="week-number">
                            {t("week", lang)} {w.week}
                          </div>
                          <div className="week-body">
                            <div className="week-desc">
                              {lang === "ko" ? w.description_ko : w.description_en}
                            </div>
                            <div className="week-meta">
                              <span className="week-dims">
                                {w.focus_labels.join(", ")}
                              </span>
                              <span className="week-target">
                                {t("dailyTarget", lang)}: {w.daily_target} {t("exercises", lang)}
                              </span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            );
          })()}
        </div>
      )}

      {/* ── Matrix Tab ── */}
      {activeTab === "matrix" && (
        <div className="tab-content">
          {matrixLoading && (
            <div className="learn-loading">
              <div className="spinner" />
              <p>{lang === "ko" ? "어휘 매트릭스 생성 중..." : "Generating vocabulary matrix..."}</p>
            </div>
          )}
          {matrixError && (
            <div className="learn-empty">
              <p>{matrixError}</p>
            </div>
          )}
          {matrixData && <VocabMatrix data={matrixData} />}
        </div>
      )}

      <div className="action-buttons">
        <button type="button" className="primary-btn" onClick={onRestart}>
          {t("restartBtn", lang)}
        </button>
      </div>
    </div>
  );
}
