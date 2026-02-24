import { useState, useCallback } from "react";
import { useLang } from "../i18n/LangContext";
import { t } from "../i18n/translations";

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

interface Props {
  exercise: Exercise;
  color: string;
  completed: boolean;
  onComplete: (exerciseId: string) => void;
}

const OPTION_LABELS = ["A", "B", "C", "D"];

export default function StudyCard({ exercise, color, completed, onComplete }: Props) {
  const { lang } = useLang();
  const [selected, setSelected] = useState<number | null>(null);
  const [showResult, setShowResult] = useState(false);

  const handleSelect = useCallback((idx: number) => {
    if (showResult) return;
    setSelected(idx);
    setShowResult(true);
  }, [showResult]);

  const handleComplete = useCallback(() => {
    onComplete(exercise.id);
  }, [exercise.id, onComplete]);

  const isCorrect = selected === exercise.correct_index;

  if (completed) {
    return (
      <div className="study-card completed">
        <span className="study-card-check">&#10003;</span>
        <span className="study-card-word">{exercise.word}</span>
        <span className="study-card-type tag">{exercise.type}</span>
      </div>
    );
  }

  const prompt = lang === "ko" ? exercise.prompt : (exercise.prompt_en || exercise.prompt);

  return (
    <div className="study-card">
      <div className="study-card-header">
        <span className="dimension-dot" style={{ backgroundColor: color }} />
        <span className="study-card-type tag">{exercise.type}</span>
        <span className="tag">{exercise.cefr}</span>
      </div>

      <div className="study-card-word-lg">{exercise.word}</div>
      <div className="study-card-prompt">{prompt}</div>

      <div className="study-card-options">
        {exercise.options.map((opt, i) => {
          let cls = "option";
          if (showResult) {
            if (i === exercise.correct_index) cls += " correct";
            else if (i === selected) cls += " wrong";
          } else if (i === selected) {
            cls += " selected";
          }
          return (
            <button
              type="button"
              key={i}
              className={cls}
              onClick={() => handleSelect(i)}
              disabled={showResult}
            >
              <span className="option-number">{OPTION_LABELS[i]}</span>
              {opt}
            </button>
          );
        })}
      </div>

      {showResult && (
        <>
          <div className={`explanation-box ${isCorrect ? "correct" : "wrong"}`}>
            {exercise.explanation}
          </div>
          <button type="button" className="next-btn" onClick={handleComplete}>
            {t("gotIt", lang)}
          </button>
        </>
      )}
    </div>
  );
}
