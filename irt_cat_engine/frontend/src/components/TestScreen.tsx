import { useState, useEffect, useCallback, useRef } from "react";
import { useLang } from "../i18n/LangContext";
import { t } from "../i18n/translations";
import type { TranslationKey } from "../i18n/translations";
import type { ItemResponse, TestProgress } from "../types/api";

interface Props {
  item: ItemResponse;
  progress: TestProgress;
  onAnswer: (itemId: number, isCorrect: boolean, timeMs: number, isDontKnow?: boolean) => void;
  loading: boolean;
}

const OPTION_LABELS = ["A", "B", "C", "D"];

// Convert first letter to lowercase for display
function lowercaseFirstLetter(text: string): string {
  if (!text) return text;
  return text.charAt(0).toLowerCase() + text.slice(1);
}

export default function TestScreen({ item, progress, onAnswer, loading }: Props) {
  const { lang } = useLang();
  const [selected, setSelected] = useState<string | null>(null);
  const [showResult, setShowResult] = useState(false);
  const timeMsRef = useRef(0);
  const [startTime] = useState(Date.now());

  useEffect(() => {
    setSelected(null);
    setShowResult(false);
  }, [item.item_id]);

  const handleSelect = useCallback(
    (option: string) => {
      if (showResult || loading) return;
      setSelected(option);
      setShowResult(true);
      timeMsRef.current = Date.now() - startTime;
    },
    [showResult, loading, startTime]
  );

  const handleDontKnow = useCallback(() => {
    if (showResult || loading) return;
    setSelected("__dont_know__");
    setShowResult(true);
    timeMsRef.current = Date.now() - startTime;
  }, [showResult, loading, startTime]);

  const handleNext = useCallback(() => {
    if (!showResult || loading) return;
    const isDontKnow = selected === "__dont_know__";
    const isCorrect = !isDontKnow && selected === item.correct_answer;
    onAnswer(item.item_id, isCorrect, timeMsRef.current, isDontKnow);
  }, [showResult, loading, selected, item, onAnswer]);

  const progressPct = Math.min(
    (progress.items_completed / 40) * 100,
    100
  );

  const questionTypeLabel = (qt: number) => {
    const key = `qtype.${qt}` as TranslationKey;
    return t(key, lang);
  };

  const itemNum = progress.items_completed + 1;
  const itemLabel = lang === "ko"
    ? `${itemNum}${t("questionNum", lang)}`
    : `Q${itemNum}`;

  const accuracyText = progress.items_completed > 0
    ? `${Math.round(progress.accuracy * 100)}%`
    : "-";

  const isCorrect = selected != null && selected !== "__dont_know__" && selected === item.correct_answer;
  const isLastItem = progress.items_completed >= 39; // max 40 items

  return (
    <div className="screen test">
      <div className="test-header">
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progressPct}%` }} />
        </div>
        <div className="test-info">
          <span>{itemLabel}</span>
          <span className="tag">{questionTypeLabel(item.question_type)}</span>
          <span className="tag">{item.cefr}</span>
          <span>{t("accuracyLabel", lang)} {accuracyText}</span>
        </div>
      </div>

      <div className="question-area">
        <div className="stem">{item.stem}</div>

        <div className="options">
          {item.options?.map((opt, i) => {
            let cls = "option";
            if (showResult) {
              if (opt === item.correct_answer) cls += " correct";
              else if (opt === selected) cls += " wrong";
            } else if (opt === selected) {
              cls += " selected";
            }
            return (
              <button
                type="button"
                key={i}
                className={cls}
                onClick={() => handleSelect(opt)}
                disabled={showResult || loading}
              >
                <span className="option-number">{OPTION_LABELS[i]}</span>
                {lowercaseFirstLetter(opt)}
              </button>
            );
          })}
        </div>

        {!showResult && (
          <button
            type="button"
            className={`dont-know-btn${selected === "__dont_know__" ? " selected" : ""}`}
            onClick={handleDontKnow}
            disabled={showResult || loading}
          >
            {t("dontKnow", lang)}
          </button>
        )}

        {/* Answer feedback */}
        {showResult && (
          <>
            {item.explanation && (
              <div className={`explanation-box ${isCorrect ? "correct" : "wrong"}`}>
                {item.explanation}
              </div>
            )}

            <button
              type="button"
              className="next-btn"
              onClick={handleNext}
              disabled={loading}
            >
              {loading ? t("loadingBtn", lang) : (
                isLastItem ? t("seeResults", lang) : t("nextQuestion", lang)
              )}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
