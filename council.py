"""
Rotational LLM Council — weighted round-robin model selection and
consensus scoring, with a synthetic single-model-compromise robustness test.

This module simulates (does not call real LLM APIs) the selection dynamics
and consensus-aggregation logic described in Sec. IV-C of the paper, so that
the fairness of rotation and the robustness of the consensus filter to a
single biased/compromised model can be measured and reproduced rather than
asserted.
"""
from dataclasses import dataclass
from typing import Dict, List
import numpy as np

MODELS = [f"model_{i}" for i in range(1, 8)]  # 7 heterogeneous LLMs
COUNCIL_SIZE = 4


@dataclass
class SelectionStats:
    counts: Dict[str, int]
    coefficient_of_variation: float


class RotationalCouncil:
    def __init__(self, rng: np.random.Generator):
        self.rng = rng
        self.base_weight = {m: 1.0 for m in MODELS}
        self.recent_use = {m: 0 for m in MODELS}  # queries since last selected
        self.selection_counts = {m: 0 for m in MODELS}

    def _selection_probability(self) -> np.ndarray:
        # Selection Probability is proportional to Base Weight + Rotational Bonus
        # Rotational bonus grows the longer a model has gone unselected,
        # which is what actually enforces rotation (Eq. 1 in the paper).
        weights = np.array([
            self.base_weight[m] + 0.15 * self.recent_use[m] for m in MODELS
        ])
        return weights / weights.sum()

    def select(self) -> List[str]:
        probs = self._selection_probability()
        chosen_idx = self.rng.choice(len(MODELS), size=COUNCIL_SIZE,
                                      replace=False, p=probs)
        chosen = [MODELS[i] for i in chosen_idx]
        for m in MODELS:
            if m in chosen:
                self.recent_use[m] = 0
                self.selection_counts[m] += 1
            else:
                self.recent_use[m] += 1
        return chosen

    def fairness_over(self, n_queries: int) -> SelectionStats:
        for _ in range(n_queries):
            self.select()
        counts = self.selection_counts
        vals = np.array(list(counts.values()), dtype=float)
        cv = float(vals.std() / vals.mean()) if vals.mean() > 0 else float("nan")
        return SelectionStats(counts=dict(counts), coefficient_of_variation=cv)


def consensus_score(confidence: float, agreement: float,
                     alpha: float = 0.5, beta: float = 0.5) -> float:
    # S_i = alpha * C_i + beta * A_i  (Eq. 3 in the paper)
    return alpha * confidence + beta * agreement


def run_compromise_robustness_trial(rng: np.random.Generator,
                                     n_trials: int = 500) -> Dict:
    """
    For each trial: 4 models are queried. In every trial exactly one of the
    four selected models is a stand-in for a compromised / adversarially
    biased model (e.g. tool-poisoned or prompt-injected per the MCP threat
    literature) that returns a high-confidence but wrong answer. The other
    three return the correct answer with noisy confidence/agreement.

    We measure how often the S_i-based consensus (highest score wins, Eq. 3)
    still selects a correct answer, i.e. the rotational quorum absorbs a
    single-model compromise.
    """
    correct = 0
    for _ in range(n_trials):
        # three honest models: correct answer, plausible confidence/agreement
        honest_conf = rng.normal(0.72, 0.08, size=3).clip(0, 1)
        honest_agree = rng.normal(0.78, 0.07, size=3).clip(0, 1)
        # one compromised model: artificially high confidence, low agreement
        # with the (unseen-to-it) honest majority
        compromised_conf = rng.normal(0.9, 0.05, size=1).clip(0, 1)
        compromised_agree = rng.normal(0.25, 0.1, size=1).clip(0, 1)

        confs = np.concatenate([honest_conf, compromised_conf])
        agrees = np.concatenate([honest_agree, compromised_agree])
        scores = np.array([consensus_score(c, a) for c, a in zip(confs, agrees)])

        winner = int(np.argmax(scores))
        if winner != 3:  # index 3 is the compromised model
            correct += 1
    return {
        "n_trials": n_trials,
        "correct_despite_compromise": correct,
        "mitigation_rate": correct / n_trials,
    }


def run_single_model_baseline_trial(rng: np.random.Generator,
                                     n_trials: int = 2000) -> Dict:
    """
    Baseline comparison: a single-model system (no rotation, no consensus)
    that, for each query, is served by exactly one candidate model drawn
    from the same per-round composition used in
    run_compromise_robustness_trial (3 honest + 1 compromised candidate).
    With no consensus mechanism to cross-check the answer, whenever the
    compromised candidate happens to be the one serving the query, the
    system has no way to detect or filter it -- it simply returns the
    compromised, incorrect answer.

    This is the direct baseline the compromise-robustness trial is compared
    against in the paper: same underlying per-round threat composition,
    with and without the rotational consensus mechanism.
    """
    served_by_compromised = rng.integers(0, 4, size=n_trials) == 3
    correct = int((~served_by_compromised).sum())
    return {
        "n_trials": n_trials,
        "correct": correct,
        "error_rate": 1 - correct / n_trials,
    }
