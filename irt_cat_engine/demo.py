"""
IRT-based Vocabulary Diagnostic Test — Full Pipeline Demo

This script demonstrates the complete flow:
1. Load vocabulary DB (9,183 words)
2. Initialize IRT parameters (b, a)
3. Generate test items with distractors
4. Run a simulated CAT session
5. Produce a diagnostic report
"""
import numpy as np

from irt_cat_engine.data.load_vocabulary import load_vocabulary, get_vocab_stats
from irt_cat_engine.item_bank.parameter_initializer import (
    initialize_item_parameters, get_parameter_statistics,
)
from irt_cat_engine.item_bank.distractor_engine import DistractorEngine
from irt_cat_engine.models.irt_2pl import probability
from irt_cat_engine.cat.session import CATSession
from irt_cat_engine.cat.stopping_rules import StoppingRules


def run_demo():
    print("=" * 60)
    print("  IRT 기반 어휘 진단 테스트 - 파이프라인 데모")
    print("=" * 60)

    # ── Step 1: Load vocabulary ──
    print("\n[1/5] 어휘 DB 로드 중...")
    vocab = load_vocabulary()
    stats = get_vocab_stats(vocab)
    print(f"  총 {stats['total_words']}개 단어 로드")
    print(f"  CEFR 분포: {stats['cefr_distribution']}")
    print(f"  POS 분포: {dict(list(stats['pos_distribution'].items())[:5])}")
    print(f"  동의어 보유: {stats['with_synonyms']}개")
    print(f"  예문 보유: {stats['with_sentences']}개")

    # ── Step 2: Initialize IRT parameters ──
    print("\n[2/5] IRT 파라미터 초기화 중...")
    items = initialize_item_parameters(vocab, question_type=1)
    param_stats = get_parameter_statistics(items)
    print(f"  b (난이도): 평균={param_stats['b_mean']:.3f}, "
          f"표준편차={param_stats['b_std']:.3f}, "
          f"범위=[{param_stats['b_min']:.2f}, {param_stats['b_max']:.2f}]")
    print(f"  a (변별도): 평균={param_stats['a_mean']:.3f}, "
          f"범위=[{param_stats['a_min']:.2f}, {param_stats['a_max']:.2f}]")

    # Show example parameters
    print("\n  예시 파라미터:")
    examples = ["the", "happy", "receive", "abundant", "contemplate"]
    for ex in examples:
        matching = [item for item in items if item.word.lower() == ex]
        if matching:
            item = matching[0]
            p50 = probability(0.0, item.discrimination_a, item.difficulty_b)
            print(f"    '{item.word}' (CEFR: {item.cefr}): b={item.difficulty_b:.2f}, "
                  f"a={item.discrimination_a:.2f}, P(θ=0)={p50:.2f}")

    # ── Step 3: Generate sample items ──
    print("\n[3/5] 문항 생성 엔진 테스트...")
    engine = DistractorEngine(vocab)

    sample_word = next(w for w in vocab if w.word_display.lower() == "happy")
    item_type1 = engine.generate_item(sample_word, question_type=1)
    if item_type1:
        print(f"\n  [Type 1] {item_type1['stem']}")
        options = [item_type1['correct_answer']] + item_type1['distractors']
        np.random.shuffle(options)
        for i, opt in enumerate(options):
            marker = " ✓" if opt == item_type1['correct_answer'] else ""
            print(f"    {chr(65+i)}. {opt}{marker}")

    sample_syn = next(w for w in vocab if w.synonym and w.pos == "ADJ" and w.cefr == "B1")
    item_type3 = engine.generate_item(sample_syn, question_type=3)
    if item_type3:
        print(f"\n  [Type 3] {item_type3['stem']}")
        options = [item_type3['correct_answer']] + item_type3['distractors']
        np.random.shuffle(options)
        for i, opt in enumerate(options):
            marker = " ✓" if opt == item_type3['correct_answer'] else ""
            print(f"    {chr(65+i)}. {opt}{marker}")

    # ── Step 4: Run simulated CAT ──
    print("\n[4/5] 적응형 테스트 시뮬레이션 (가상 응시자 3명)...")

    test_profiles = [
        {"name": "초등학생 (θ_true=-1.5)", "theta_true": -1.5, "grade": "초5-6"},
        {"name": "중학생 (θ_true=0.0)", "theta_true": 0.0, "grade": "중2"},
        {"name": "고등학생 (θ_true=1.0)", "theta_true": 1.0, "grade": "고2"},
    ]

    rng = np.random.RandomState(42)

    for profile in test_profiles:
        print(f"\n  --- {profile['name']} ---")
        session = CATSession.create(
            item_pool=items,
            grade=profile["grade"],
        )

        while not session.is_complete:
            item = session.get_next_item()
            if item is None:
                break
            p = probability(profile["theta_true"], item.discrimination_a, item.difficulty_b)
            is_correct = bool(rng.random() < p)
            session.record_response(item, is_correct)

        results = session.get_results()
        error = results["theta"] - profile["theta_true"]
        print(f"    초기 θ: {session.initial_theta:.2f}")
        print(f"    추정 θ: {results['theta']:.3f} (진짜: {profile['theta_true']:.1f}, 오차: {error:+.3f})")
        print(f"    SE: {results['se']:.3f}, 신뢰도: {results['reliability']:.3f}")
        print(f"    CEFR: {results['cefr_level']} {results['cefr_probabilities']}")
        print(f"    교육과정: {results['curriculum_level']}")
        print(f"    추정 어휘: {results['vocab_size_estimate']}개 / {len(items)}개")
        print(f"    문항수: {results['total_items']}, 정답률: {results['accuracy']:.1%}")
        print(f"    종료: {session.termination_reason}")

    # ── Step 5: Batch simulation ──
    print("\n[5/5] 대규모 시뮬레이션 (100명)...")
    n_sim = 100
    theta_trues = rng.uniform(-2.5, 2.5, n_sim)
    theta_ests = []
    test_lengths = []

    for theta_true in theta_trues:
        session = CATSession(
            item_pool=items[:3000],  # Use subset for speed
            initial_theta=0.0,
            stopping_rules=StoppingRules(min_items=15, max_items=35, se_threshold=0.32),
        )
        while not session.is_complete:
            item = session.get_next_item()
            if item is None:
                break
            p = probability(float(theta_true), item.discrimination_a, item.difficulty_b)
            is_correct = bool(rng.random() < p)
            session.record_response(item, is_correct)
        theta_ests.append(session.current_theta)
        test_lengths.append(len(session.responses))

    theta_ests = np.array(theta_ests)
    errors = theta_ests - theta_trues
    rmse = float(np.sqrt(np.mean(errors ** 2)))
    corr = float(np.corrcoef(theta_trues, theta_ests)[0, 1])

    print(f"  RMSE: {rmse:.3f}")
    print(f"  평균 절대 오차: {np.mean(np.abs(errors)):.3f}")
    print(f"  상관계수: {corr:.3f}")
    print(f"  평균 문항수: {np.mean(test_lengths):.1f}")
    print(f"  문항수 범위: [{min(test_lengths)}, {max(test_lengths)}]")

    print("\n" + "=" * 60)
    print("  데모 완료!")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
