"""Large-scale simulation: 10,000 virtual test-takers with real vocabulary data.

Uses vectorized numpy for item selection and EAP estimation to achieve
practical run times with the full 9,183-item pool.

Validates CAT system performance targets:
- RMSE < 0.45 (achieved ~0.33)
- Correlation > 0.92 (achieved ~0.975)
- Majority stop before max items (achieved ~66%)
"""
import numpy as np
import pytest
import time

from scipy import stats as sp_stats

from irt_cat_engine.data.load_vocabulary import load_vocabulary
from irt_cat_engine.item_bank.parameter_initializer import initialize_item_parameters
from irt_cat_engine.models.irt_2pl import ItemParameters
from irt_cat_engine.config import (
    VOCAB_DB_PATH, CAT_MIN_ITEMS, CAT_MAX_ITEMS, CAT_SE_THRESHOLD,
    CAT_CONVERGENCE_WINDOW, CAT_CONVERGENCE_EPSILON,
    EAP_QUADRATURE_POINTS, EAP_QUAD_RANGE,
)


def _fast_simulate_cat(
    theta_true: float,
    a_all: np.ndarray,
    b_all: np.ndarray,
    rng: np.random.RandomState,
    min_items: int = CAT_MIN_ITEMS,
    max_items: int = CAT_MAX_ITEMS,
    se_threshold: float = CAT_SE_THRESHOLD,
) -> tuple[float, float, int, str]:
    """Fast vectorized CAT simulation for a single test-taker.

    Returns: (theta_hat, se, n_items, termination_reason)
    """
    n_pool = len(a_all)
    administered = np.zeros(n_pool, dtype=bool)
    item_indices = []
    responses = []
    theta_history = [0.0]
    current_theta = 0.0
    current_se = 1.5

    # Precompute EAP quadrature
    quad_points, quad_weights = np.polynomial.hermite_e.hermegauss(EAP_QUADRATURE_POINTS)
    # Transform from Hermite to N(0,1): points are already scaled for N(0,1)
    quad_points = quad_points.astype(np.float64)
    quad_weights = quad_weights.astype(np.float64)

    for step in range(max_items):
        # --- Item Selection: vectorized max Fisher information ---
        avail_mask = ~administered
        avail_idx = np.where(avail_mask)[0]
        if len(avail_idx) == 0:
            break

        a_avail = a_all[avail_idx]
        b_avail = b_all[avail_idx]

        # P and Q vectorized
        exp_val = np.clip(-a_avail * (current_theta - b_avail), -500, 500)
        p_avail = 1.0 / (1.0 + np.exp(exp_val))
        q_avail = 1.0 - p_avail
        info_avail = a_avail ** 2 * p_avail * q_avail

        # Select from top-5 randomly
        top5_local = np.argsort(info_avail)[-5:]
        selected_local = rng.choice(top5_local)
        selected_global = avail_idx[selected_local]

        administered[selected_global] = True
        item_indices.append(selected_global)

        # --- Simulate response ---
        a_sel = a_all[selected_global]
        b_sel = b_all[selected_global]
        exp_s = np.clip(-a_sel * (theta_true - b_sel), -500, 500)
        p_correct = 1.0 / (1.0 + np.exp(exp_s))
        is_correct = 1 if rng.random() < p_correct else 0
        responses.append(is_correct)

        # --- EAP estimation (vectorized) ---
        n_admin = len(item_indices)
        a_admin = a_all[item_indices]
        b_admin = b_all[item_indices]
        r_admin = np.array(responses, dtype=np.float64)

        # Log-likelihood at each quadrature point: shape (n_quad, n_admin)
        # theta_q shape: (n_quad, 1), a shape: (1, n_admin), b shape: (1, n_admin)
        theta_q = quad_points[:, np.newaxis]
        exp_mat = np.clip(-a_admin[np.newaxis, :] * (theta_q - b_admin[np.newaxis, :]), -500, 500)
        p_mat = 1.0 / (1.0 + np.exp(exp_mat))
        p_mat = np.clip(p_mat, 1e-10, 1.0 - 1e-10)

        # Log-likelihood per quad point
        log_l = np.sum(r_admin * np.log(p_mat) + (1.0 - r_admin) * np.log(1.0 - p_mat), axis=1)

        # Posterior = likelihood × prior_weight (Hermite weights already include Gaussian)
        log_posterior = log_l + np.log(quad_weights + 1e-300)
        log_posterior -= np.max(log_posterior)  # Numerical stability
        posterior = np.exp(log_posterior)
        posterior /= np.sum(posterior)

        current_theta = float(np.sum(posterior * quad_points))
        current_se = float(np.sqrt(np.sum(posterior * (quad_points - current_theta) ** 2)))
        current_se = max(current_se, 0.01)

        theta_history.append(current_theta)

        # --- Stopping rules ---
        n_done = len(responses)
        if n_done >= max_items:
            return current_theta, current_se, n_done, "max_items"

        if n_done >= min_items:
            if current_se < se_threshold:
                return current_theta, current_se, n_done, "se_threshold"

            if len(theta_history) >= CAT_CONVERGENCE_WINDOW:
                recent = theta_history[-CAT_CONVERGENCE_WINDOW:]
                diffs = [abs(recent[i] - recent[i - 1]) for i in range(1, len(recent))]
                if all(d < CAT_CONVERGENCE_EPSILON for d in diffs):
                    return current_theta, current_se, n_done, "convergence"

    return current_theta, current_se, len(responses), "max_items"


@pytest.fixture(scope="module")
def item_arrays():
    """Load full item pool and return as numpy arrays."""
    if not VOCAB_DB_PATH.exists():
        pytest.skip(f"Vocabulary DB not found: {VOCAB_DB_PATH}")
    vocab = load_vocabulary()
    items = initialize_item_parameters(vocab, question_type=1)
    a_all = np.array([item.discrimination_a for item in items], dtype=np.float64)
    b_all = np.array([item.difficulty_b for item in items], dtype=np.float64)
    return a_all, b_all, items


class TestLargeScaleSimulation:
    """10,000-person simulation with full item pool."""

    def test_10k_simulation(self, item_arrays):
        a_all, b_all, items = item_arrays
        n_simulations = 10000
        rng = np.random.RandomState(2024)

        theta_trues = rng.uniform(-2.5, 2.5, n_simulations)
        theta_estimates = np.zeros(n_simulations)
        se_values = np.zeros(n_simulations)
        test_lengths = np.zeros(n_simulations, dtype=int)
        termination_reasons = []

        start = time.time()

        for i in range(n_simulations):
            theta_hat, se, n_items, reason = _fast_simulate_cat(
                float(theta_trues[i]), a_all, b_all, rng,
            )
            theta_estimates[i] = theta_hat
            se_values[i] = se
            test_lengths[i] = n_items
            termination_reasons.append(reason)

            if (i + 1) % 2000 == 0:
                elapsed_so_far = time.time() - start
                print(f"  [{i+1}/{n_simulations}] {elapsed_so_far:.1f}s elapsed...")

        elapsed = time.time() - start

        errors = theta_estimates - theta_trues
        rmse = float(np.sqrt(np.mean(errors ** 2)))
        mean_abs_bias = float(np.mean(np.abs(errors)))
        correlation = float(np.corrcoef(theta_trues, theta_estimates)[0, 1])
        mean_items = float(np.mean(test_lengths))
        se_below_035 = float(np.mean(se_values < 0.35))

        reason_counts = {}
        for r in termination_reasons:
            reason_counts[r] = reason_counts.get(r, 0) + 1

        print(f"\n{'='*60}")
        print(f"  10,000-Person Simulation Results")
        print(f"{'='*60}")
        print(f"  Time: {elapsed:.1f}s ({elapsed/n_simulations*1000:.1f}ms per test)")
        print(f"  RMSE: {rmse:.4f}")
        print(f"  Mean Absolute Bias: {mean_abs_bias:.4f}")
        print(f"  Correlation (true vs est): {correlation:.4f}")
        print(f"  Mean test length: {mean_items:.1f}")
        print(f"  Test length range: [{test_lengths.min()}, {test_lengths.max()}]")
        print(f"  Mean SE: {np.mean(se_values):.4f}")
        print(f"  % SE < 0.35: {se_below_035*100:.1f}%")
        print(f"  Termination reasons: {reason_counts}")

        print(f"\n  By ability range:")
        for lo, hi, label in [(-2.5, -1.5, "Low"), (-1.5, -0.5, "Below Avg"),
                               (-0.5, 0.5, "Average"), (0.5, 1.5, "Above Avg"),
                               (1.5, 2.5, "High")]:
            mask = (theta_trues >= lo) & (theta_trues < hi)
            if mask.sum() > 0:
                sub_errors = errors[mask]
                sub_rmse = float(np.sqrt(np.mean(sub_errors ** 2)))
                sub_items = float(np.mean(test_lengths[mask]))
                print(f"    {label} (theta {lo:.1f}~{hi:.1f}): "
                      f"n={mask.sum()}, RMSE={sub_rmse:.3f}, items={sub_items:.1f}")

        print(f"{'='*60}")

        # Assertions — quality metrics are primary
        assert rmse < 0.45, f"RMSE {rmse:.4f} exceeds 0.45"
        assert mean_abs_bias < 0.35, f"Mean abs bias {mean_abs_bias:.4f} exceeds 0.35"
        assert correlation > 0.92, f"Correlation {correlation:.4f} below 0.92"
        # Mean items can be high (SE threshold 0.30 is strict); verify majority
        # terminate early and that no tests go below min_items
        assert test_lengths.min() >= CAT_MIN_ITEMS, "Some tests ended below min_items"
        pct_early_stop = 1.0 - (reason_counts.get("max_items", 0) / n_simulations)
        assert pct_early_stop > 0.50, f"Only {pct_early_stop*100:.1f}% stop before max items"
