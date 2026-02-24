import { useState, useRef, useCallback } from "react";
import { useLang } from "../i18n/LangContext";
import type { VocabMatrixData, MatrixWord, KnowledgeState } from "../types/api";

interface Props {
  data: VocabMatrixData;
}

const STATE_COLORS: Record<string, string> = {
  not_known: "#e2e8f0",
  emerging: "#93c5fd",
  developing: "#86efac",
  comfortable: "#fde047",
  mastered: "#fca5a5",
};

export default function VocabMatrix({ data }: Props) {
  const { lang } = useLang();
  const [showGoal, setShowGoal] = useState(false);
  const [hoveredWord, setHoveredWord] = useState<MatrixWord | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const [selectedWord, setSelectedWord] = useState<MatrixWord | null>(null);
  const gridRef = useRef<HTMLDivElement>(null);

  const handleMouseEnter = useCallback(
    (word: MatrixWord, e: React.MouseEvent) => {
      const rect = (e.target as HTMLElement).getBoundingClientRect();
      const gridRect = gridRef.current?.getBoundingClientRect();
      if (gridRect) {
        setTooltipPos({
          x: rect.left - gridRect.left + rect.width / 2,
          y: rect.top - gridRect.top - 8,
        });
      }
      setHoveredWord(word);
    },
    []
  );

  const handleMouseLeave = useCallback(() => {
    setHoveredWord(null);
  }, []);

  const summary = showGoal ? data.goal_summary : data.summary;

  const stateLabel = (key: string) => {
    const s = data.states.find((st: KnowledgeState) => st.key === key);
    return s ? (lang === "ko" ? s.label_ko : s.label) : key;
  };

  return (
    <div className="matrix-container">
      {/* Toggle Current / Goal */}
      <div className="matrix-toggle">
        <button
          type="button"
          className={`matrix-toggle-btn${!showGoal ? " active" : ""}`}
          onClick={() => setShowGoal(false)}
        >
          {lang === "ko" ? "현재 수준" : "Current"}
        </button>
        <button
          type="button"
          className={`matrix-toggle-btn${showGoal ? " active" : ""}`}
          onClick={() => setShowGoal(true)}
        >
          {lang === "ko" ? "목표 수준" : "Goal"}
        </button>
      </div>

      {showGoal && (
        <p className="matrix-goal-info">
          {lang === "ko"
            ? `목표: ${data.goal_cefr} (theta ${data.goal_theta}) | ${data.goal_summary.words_changed}개 단어 상태 변화 예상`
            : `Goal: ${data.goal_cefr} (theta ${data.goal_theta}) | ${data.goal_summary.words_changed} words expected to improve`}
        </p>
      )}

      {/* Grid */}
      <div className="matrix-grid" ref={gridRef}>
        {data.words.map((word, idx) => {
          const state = showGoal ? word.goal_state : word.current_state;
          const color = STATE_COLORS[state] || STATE_COLORS.not_known;
          const changed = showGoal && word.current_state !== word.goal_state;
          return (
            <button
              key={idx}
              type="button"
              className={`matrix-cube${changed ? " matrix-cube-changed" : ""}`}
              style={{ backgroundColor: color }}
              onMouseEnter={(e) => handleMouseEnter(word, e)}
              onMouseLeave={handleMouseLeave}
              onClick={() => setSelectedWord(word)}
              title={word.word}
            />
          );
        })}

        {/* Tooltip */}
        {hoveredWord && (
          <div
            className="matrix-tooltip"
            style={{ left: tooltipPos.x, top: tooltipPos.y }}
          >
            <strong>{hoveredWord.word}</strong>
            <span>{hoveredWord.meaning_ko}</span>
            <span className="matrix-tooltip-meta">
              {hoveredWord.cefr} &middot; P=
              {showGoal
                ? hoveredWord.goal_probability
                : hoveredWord.current_probability}
            </span>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="matrix-legend">
        {data.states.map((s: KnowledgeState) => (
          <div key={s.key} className="matrix-legend-item">
            <div
              className="matrix-legend-swatch"
              style={{ backgroundColor: s.color }}
            />
            <span>{lang === "ko" ? s.label_ko : s.label}</span>
          </div>
        ))}
      </div>

      {/* Summary bar */}
      <div className="matrix-summary">
        {data.states.map((s: KnowledgeState) => {
          const counts = summary.counts as unknown as Record<string, number>;
          const count = counts[s.key] ?? 0;
          const pct =
            summary.total > 0 ? Math.round((count / summary.total) * 100) : 0;
          return (
            <div key={s.key} className="matrix-summary-item">
              <div
                className="matrix-summary-bar"
                style={{ backgroundColor: s.color, width: `${pct}%` }}
              />
              <span className="matrix-summary-label">
                {stateLabel(s.key)}: {count} ({pct}%)
              </span>
            </div>
          );
        })}
      </div>

      {/* Detail Modal */}
      {selectedWord && (
        <div
          className="matrix-modal-overlay"
          onClick={() => setSelectedWord(null)}
        >
          <div className="matrix-modal" onClick={(e) => e.stopPropagation()}>
            <button
              type="button"
              className="matrix-modal-close"
              onClick={() => setSelectedWord(null)}
            >
              &times;
            </button>
            <h3 className="matrix-modal-word">{selectedWord.word}</h3>
            <p className="matrix-modal-meaning">{selectedWord.meaning_ko}</p>
            <div className="matrix-modal-details">
              <div className="matrix-modal-row">
                <span>CEFR</span>
                <span>{selectedWord.cefr}</span>
              </div>
              <div className="matrix-modal-row">
                <span>{lang === "ko" ? "품사" : "POS"}</span>
                <span>{selectedWord.pos}</span>
              </div>
              <div className="matrix-modal-row">
                <span>{lang === "ko" ? "빈도 순위" : "Freq Rank"}</span>
                <span>#{selectedWord.freq_rank.toLocaleString()}</span>
              </div>
              <div className="matrix-modal-row">
                <span>{lang === "ko" ? "현재 상태" : "Current"}</span>
                <div className="matrix-modal-state">
                  <div
                    className="matrix-legend-swatch"
                    style={{
                      backgroundColor:
                        STATE_COLORS[selectedWord.current_state],
                    }}
                  />
                  <span>
                    {stateLabel(selectedWord.current_state)} (P=
                    {selectedWord.current_probability})
                  </span>
                </div>
              </div>
              <div className="matrix-modal-row">
                <span>{lang === "ko" ? "목표 상태" : "Goal"}</span>
                <div className="matrix-modal-state">
                  <div
                    className="matrix-legend-swatch"
                    style={{
                      backgroundColor: STATE_COLORS[selectedWord.goal_state],
                    }}
                  />
                  <span>
                    {stateLabel(selectedWord.goal_state)} (P=
                    {selectedWord.goal_probability})
                  </span>
                </div>
              </div>
              <div className="matrix-modal-row">
                <span>{lang === "ko" ? "IRT 파라미터" : "IRT Params"}</span>
                <span>
                  {selectedWord.has_irt_params
                    ? lang === "ko"
                      ? "있음"
                      : "Yes"
                    : lang === "ko"
                      ? "CEFR 추정"
                      : "CEFR estimate"}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
