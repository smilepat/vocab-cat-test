import { useState } from "react";
import type { LearningCard, GoalSessionProgress } from "../types/api";

interface Props {
  lang: "ko" | "en";
  sessionId: string;
  goalName: string;
  targetWordCount: number;
  currentCard: LearningCard;
  progress: GoalSessionProgress;
  onSubmit: (selfRating: number, isCorrect: boolean) => void;
  onExit: () => void;
}

export default function GoalLearningScreen({
  lang,
  goalName,
  targetWordCount,
  currentCard,
  progress,
  onSubmit,
  onExit,
}: Props) {
  const [showAnswer, setShowAnswer] = useState(false);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);

  const handleReveal = () => {
    setShowAnswer(true);
  };

  const handleSelfAssess = (rating: number) => {
    const isCorrect = selectedOption === currentCard.correct_answer;
    onSubmit(rating, isCorrect || rating >= 2);
    // Reset for next card
    setShowAnswer(false);
    setSelectedOption(null);
  };

  const handleOptionSelect = (option: string) => {
    setSelectedOption(option);
  };

  // Convert first letter to lowercase for display
  function lowercaseFirstLetter(text: string): string {
    if (!text) return text;
    return text.charAt(0).toLowerCase() + text.slice(1);
  }

  return (
    <div className="screen">
      {/* Header with progress */}
      <div style={{ marginBottom: "24px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
          <h2 style={{ margin: 0 }}>{goalName}</h2>
          <button
            type="button"
            onClick={onExit}
            style={{
              padding: "6px 12px",
              background: "#f5f5f5",
              border: "1px solid #ddd",
              borderRadius: "6px",
              cursor: "pointer",
              fontSize: "14px",
            }}
          >
            {lang === "ko" ? "나가기" : "Exit"}
          </button>
        </div>

        {/* Progress bar */}
        <div style={{ marginBottom: "8px" }}>
          <div style={{ fontSize: "14px", color: "#666", marginBottom: "6px" }}>
            {lang === "ko"
              ? `진행률: ${progress.completion_percentage.toFixed(1)}% (마스터: ${progress.words_mastered}/${targetWordCount})`
              : `Progress: ${progress.completion_percentage.toFixed(1)}% (Mastered: ${progress.words_mastered}/${targetWordCount})`
            }
          </div>
          <div style={{
            width: "100%",
            height: "8px",
            background: "#e0e0e0",
            borderRadius: "4px",
            overflow: "hidden"
          }}>
            <div style={{
              width: `${progress.completion_percentage}%`,
              height: "100%",
              background: "linear-gradient(90deg, #667eea 0%, #764ba2 100%)",
              transition: "width 0.3s ease",
            }} />
          </div>
        </div>

        <div style={{ fontSize: "12px", color: "#888" }}>
          {lang === "ko"
            ? `학습한 단어: ${progress.words_studied} | 복습 횟수: ${progress.total_reviews}`
            : `Words Studied: ${progress.words_studied} | Reviews: ${progress.total_reviews}`
          }
        </div>
      </div>

      {/* Learning Card */}
      <div className="card" style={{ marginBottom: "24px", minHeight: "400px" }}>
        {/* Card Header */}
        <div style={{ marginBottom: "20px", borderBottom: "2px solid #f0f0f0", paddingBottom: "12px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <span style={{
                fontSize: "12px",
                padding: "4px 8px",
                background: currentCard.is_first_exposure ? "#e3f2fd" : "#fff3e0",
                color: currentCard.is_first_exposure ? "#1976d2" : "#f57c00",
                borderRadius: "4px",
                marginRight: "8px",
                fontWeight: "600",
              }}>
                {currentCard.is_first_exposure
                  ? (lang === "ko" ? "새 단어" : "New")
                  : (lang === "ko" ? `복습 ${currentCard.review_count}회` : `Review ${currentCard.review_count}`)
                }
              </span>
              <span style={{ fontSize: "12px", color: "#888" }}>
                {lang === "ko" ? `DVK 레벨 ${currentCard.dvk_level}` : `DVK Level ${currentCard.dvk_level}`}
              </span>
            </div>
            <div style={{ fontSize: "12px", color: "#888" }}>
              {currentCard.cefr && `${currentCard.cefr} · `}
              {currentCard.pos}
            </div>
          </div>
        </div>

        {/* Question */}
        <div style={{ marginBottom: "24px" }}>
          <div style={{ fontSize: "18px", fontWeight: "600", marginBottom: "16px" }}>
            {currentCard.stem || currentCard.word}
          </div>

          {/* Options */}
          {currentCard.options && currentCard.options.length > 0 && (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {currentCard.options.map((opt, idx) => {
                const isSelected = selectedOption === opt;
                const isCorrect = opt === currentCard.correct_answer;

                return (
                  <button
                    key={idx}
                    onClick={() => !showAnswer && handleOptionSelect(opt)}
                    disabled={showAnswer}
                    style={{
                      padding: "14px 16px",
                      textAlign: "left",
                      background: showAnswer
                        ? isCorrect
                          ? "#e8f5e9"
                          : isSelected
                          ? "#ffebee"
                          : "white"
                        : isSelected
                        ? "#f5f5f5"
                        : "white",
                      border: `2px solid ${
                        showAnswer
                          ? isCorrect
                            ? "#4caf50"
                            : isSelected
                            ? "#f44336"
                            : "#e0e0e0"
                          : isSelected
                          ? "#667eea"
                          : "#e0e0e0"
                      }`,
                      borderRadius: "8px",
                      cursor: showAnswer ? "default" : "pointer",
                      fontSize: "16px",
                      transition: "all 0.2s",
                    }}
                  >
                    {lowercaseFirstLetter(opt)}
                    {showAnswer && isCorrect && " ✓"}
                  </button>
                );
              })}
            </div>
          )}

          {/* Show answer section for non-option questions */}
          {(!currentCard.options || currentCard.options.length === 0) && (
            <div style={{ marginTop: "16px" }}>
              {!showAnswer ? (
                <button
                  type="button"
                  className="primary-btn"
                  onClick={handleReveal}
                  style={{ width: "100%" }}
                >
                  {lang === "ko" ? "답 확인하기" : "Show Answer"}
                </button>
              ) : (
                <div style={{
                  padding: "16px",
                  background: "#f0f7ff",
                  border: "2px solid #2196f3",
                  borderRadius: "8px",
                  fontSize: "16px",
                }}>
                  <div style={{ fontWeight: "600", marginBottom: "8px", color: "#1976d2" }}>
                    {lang === "ko" ? "정답:" : "Answer:"}
                  </div>
                  <div>{currentCard.correct_answer}</div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Korean meaning (helper) */}
        {showAnswer && currentCard.meaning_ko && (
          <div style={{
            marginTop: "16px",
            padding: "12px",
            background: "#fafafa",
            borderRadius: "6px",
            fontSize: "14px",
            color: "#666",
          }}>
            <strong>{lang === "ko" ? "한글 뜻:" : "Korean:"}</strong> {currentCard.meaning_ko}
          </div>
        )}

        {/* Self-assessment buttons */}
        {showAnswer && (
          <div style={{ marginTop: "24px", borderTop: "2px solid #f0f0f0", paddingTop: "20px" }}>
            <div style={{ fontSize: "14px", fontWeight: "600", marginBottom: "12px", textAlign: "center" }}>
              {lang === "ko" ? "이 단어를 얼마나 잘 기억하시나요?" : "How well did you know this word?"}
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
              <button
                type="button"
                onClick={() => handleSelfAssess(0)}
                style={{
                  padding: "14px",
                  background: "white",
                  border: "2px solid #f44336",
                  borderRadius: "8px",
                  cursor: "pointer",
                  fontSize: "14px",
                  fontWeight: "600",
                  color: "#f44336",
                }}
              >
                {lang === "ko" ? "❌ 몰랐어요" : "❌ Forgot"}
              </button>
              <button
                type="button"
                onClick={() => handleSelfAssess(1)}
                style={{
                  padding: "14px",
                  background: "white",
                  border: "2px solid #ff9800",
                  borderRadius: "8px",
                  cursor: "pointer",
                  fontSize: "14px",
                  fontWeight: "600",
                  color: "#ff9800",
                }}
              >
                {lang === "ko" ? "🤔 어려웠어요" : "🤔 Hard"}
              </button>
              <button
                type="button"
                onClick={() => handleSelfAssess(2)}
                style={{
                  padding: "14px",
                  background: "white",
                  border: "2px solid #4caf50",
                  borderRadius: "8px",
                  cursor: "pointer",
                  fontSize: "14px",
                  fontWeight: "600",
                  color: "#4caf50",
                }}
              >
                {lang === "ko" ? "✅ 좋아요" : "✅ Good"}
              </button>
              <button
                type="button"
                onClick={() => handleSelfAssess(3)}
                style={{
                  padding: "14px",
                  background: "white",
                  border: "2px solid #2196f3",
                  borderRadius: "8px",
                  cursor: "pointer",
                  fontSize: "14px",
                  fontWeight: "600",
                  color: "#2196f3",
                }}
              >
                {lang === "ko" ? "💯 쉬웠어요" : "💯 Easy"}
              </button>
            </div>
          </div>
        )}

        {/* Reveal button for option questions */}
        {currentCard.options && currentCard.options.length > 0 && !showAnswer && selectedOption && (
          <div style={{ marginTop: "20px" }}>
            <button
              type="button"
              className="primary-btn"
              onClick={handleReveal}
              style={{ width: "100%" }}
            >
              {lang === "ko" ? "답 확인하기" : "Check Answer"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
