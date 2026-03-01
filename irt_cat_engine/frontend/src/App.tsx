import { useState, useCallback } from "react";
import SurveyScreen from "./components/SurveyScreen";
import TestScreen from "./components/TestScreen";
import ResultsScreen from "./components/ResultsScreen";
import GoalLearningScreen from "./components/GoalLearningScreen";
import { LangProvider, useLang } from "./i18n/LangContext";
import { t } from "./i18n/translations";
import { apiPost } from "./hooks/useApi";
import type {
  TestStartResponse,
  TestRespondResponse,
  TestResults,
  ItemResponse,
  TestProgress,
  GoalLearningStartRequest,
  GoalLearningStartResponse,
  GoalLearningSubmitRequest,
  GoalLearningSubmitResponse,
  LearningCard,
  GoalSessionProgress,
} from "./types/api";
import "./App.css";

type Screen = "survey" | "test" | "results" | "goal-learning";

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

  // Goal-based learning state
  const [goalSessionId, setGoalSessionId] = useState("");
  const [goalName, setGoalName] = useState("");
  const [targetWordCount, setTargetWordCount] = useState(0);
  const [currentCard, setCurrentCard] = useState<LearningCard | null>(null);
  const [goalProgress, setGoalProgress] = useState<GoalSessionProgress | null>(null);

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

  const handleStartGoalLearning = useCallback(
    async (goal: { id: string; name: string; count: number; nickname?: string }) => {
      setLoading(true);
      setError(null);
      try {
        const request: GoalLearningStartRequest = {
          goal_id: goal.id,
          goal_name: goal.name,
          target_word_count: goal.count,
          nickname: goal.nickname,
        };

        const data = await apiPost<GoalLearningStartResponse>("/learn/goal/start", request);
        setGoalSessionId(data.session_id);
        setUserId(data.user_id);
        setGoalName(data.goal_name);
        setTargetWordCount(data.target_word_count);
        setCurrentCard(data.first_card);
        setGoalProgress({
          words_studied: 0,
          words_mastered: 0,
          total_reviews: 0,
          target_word_count: data.target_word_count,
          completion_percentage: 0,
        });
        setScreen("goal-learning");
      } catch (e) {
        setError(e instanceof Error ? e.message : t("serverError", lang));
      } finally {
        setLoading(false);
      }
    },
    [lang]
  );

  const handleSubmitCard = useCallback(
    async (selfRating: number, isCorrect: boolean) => {
      if (!currentCard) return;

      setLoading(true);
      setError(null);
      try {
        const request: GoalLearningSubmitRequest = {
          word: currentCard.word,
          question_type: currentCard.question_type,
          self_rating: selfRating,
          is_correct: isCorrect,
        };

        const data = await apiPost<GoalLearningSubmitResponse>(
          `/learn/goal/${goalSessionId}/submit`,
          request
        );

        setGoalProgress(data.session_progress);

        if (data.next_card) {
          setCurrentCard(data.next_card);
        } else {
          // All words mastered!
          alert(lang === "ko" ? "축하합니다! 모든 단어를 마스터했습니다!" : "Congratulations! You've mastered all words!");
          handleRestart();
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : t("responseFailed", lang));
      } finally {
        setLoading(false);
      }
    },
    [currentCard, goalSessionId, lang]
  );

  const handleRestart = useCallback(() => {
    setScreen("survey");
    setSessionId("");
    setUserId("");
    setCurrentItem(null);
    setProgress(null);
    setResults(null);
    setGoalSessionId("");
    setGoalName("");
    setTargetWordCount(0);
    setCurrentCard(null);
    setGoalProgress(null);
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
        <SurveyScreen
          onStart={handleStart}
          onStartGoalLearning={handleStartGoalLearning}
          loading={loading}
        />
      )}

      {screen === "test" && currentItem && progress && (
        <TestScreen
          item={currentItem}
          progress={progress}
          onAnswer={handleAnswer}
          loading={loading}
        />
      )}

      {screen === "goal-learning" && currentCard && goalProgress && (
        <GoalLearningScreen
          lang={lang}
          sessionId={goalSessionId}
          goalName={goalName}
          targetWordCount={targetWordCount}
          currentCard={currentCard}
          progress={goalProgress}
          onSubmit={handleSubmitCard}
          onExit={handleRestart}
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
