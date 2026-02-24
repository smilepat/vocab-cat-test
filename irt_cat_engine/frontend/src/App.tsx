import { useState, useCallback } from "react";
import SurveyScreen from "./components/SurveyScreen";
import TestScreen from "./components/TestScreen";
import ResultsScreen from "./components/ResultsScreen";
import { LangProvider, useLang } from "./i18n/LangContext";
import { t } from "./i18n/translations";
import { apiPost } from "./hooks/useApi";
import type {
  TestStartResponse,
  TestRespondResponse,
  TestResults,
  ItemResponse,
  TestProgress,
} from "./types/api";
import "./App.css";

type Screen = "survey" | "test" | "results";

function AppInner() {
  const { lang, toggle } = useLang();
  const [screen, setScreen] = useState<Screen>("survey");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [sessionId, setSessionId] = useState("");
  const [userId, setUserId] = useState("");
  const [currentItem, setCurrentItem] = useState<ItemResponse | null>(null);
  const [progress, setProgress] = useState<TestProgress | null>(null);
  const [results, setResults] = useState<TestResults | null>(null);

  const handleStart = useCallback(
    async (profile: {
      nickname: string;
      grade: string;
      self_assess: string;
      exam_experience: string;
      question_type: number;
    }) => {
      setLoading(true);
      setError(null);
      try {
        const data = await apiPost<TestStartResponse>("/test/start", profile);
        setSessionId(data.session_id);
        setUserId(data.user_id);
        setCurrentItem(data.first_item);
        setProgress(data.progress);
        setScreen("test");
      } catch (e) {
        setError(e instanceof Error ? e.message : t("serverError", lang));
      } finally {
        setLoading(false);
      }
    },
    [lang]
  );

  const handleAnswer = useCallback(
    async (itemId: number, isCorrect: boolean, timeMs: number, isDontKnow = false) => {
      setLoading(true);
      setError(null);
      try {
        const data = await apiPost<TestRespondResponse>(
          `/test/${sessionId}/respond`,
          {
            item_id: itemId,
            is_correct: isCorrect,
            is_dont_know: isDontKnow,
            response_time_ms: timeMs,
          }
        );
        setProgress(data.progress);

        if (data.is_complete && data.results) {
          setResults(data.results);
          setScreen("results");
        } else if (data.next_item) {
          setCurrentItem(data.next_item);
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : t("responseFailed", lang));
      } finally {
        setLoading(false);
      }
    },
    [sessionId, lang]
  );

  const handleRestart = useCallback(() => {
    setScreen("survey");
    setSessionId("");
    setUserId("");
    setCurrentItem(null);
    setProgress(null);
    setResults(null);
    setError(null);
  }, []);

  return (
    <div className="app">
      <div className="lang-toggle">
        <button type="button" className="lang-btn" onClick={toggle}>
          {t("langSwitch", lang)}
        </button>
      </div>

      {error && (
        <div className="error-bar">
          {error}
          <button type="button" onClick={() => setError(null)}>X</button>
        </div>
      )}

      {screen === "survey" && (
        <SurveyScreen onStart={handleStart} loading={loading} />
      )}

      {screen === "test" && currentItem && progress && (
        <TestScreen
          item={currentItem}
          progress={progress}
          onAnswer={handleAnswer}
          loading={loading}
        />
      )}

      {screen === "results" && results && (
        <ResultsScreen
          results={results}
          sessionId={sessionId}
          userId={userId}
          onRestart={handleRestart}
        />
      )}
    </div>
  );
}

function App() {
  return (
    <LangProvider>
      <AppInner />
    </LangProvider>
  );
}

export default App;
