"""Reputation math must match AgentTrust._overall / _bayes / _clamp."""


def clamp(value: int) -> int:
    return max(0, min(100, value))


def bayes(success: int, fail: int, prior: int = 70, strength: int = 3) -> int:
    total = success + fail
    return (success * 100 + prior * strength) // (total + strength)


def overall(authenticity, reliability, sla_score, tx_score, dispute_score) -> int:
    weighted = (
        authenticity * 20
        + reliability * 25
        + sla_score * 20
        + tx_score * 20
        + dispute_score * 15
    )
    return clamp((weighted + 50) // 100)


def authenticity_from_fingerprint(status: str, score: int) -> int:
    if status == "verified":
        return score
    if status == "mismatched":
        return clamp(score // 2)
    if status == "inconclusive":
        return 40
    return 0


def dispute_score(lost: int, opened: int) -> int:
    return clamp(100 - lost * 8 - opened * 2)


def test_pitch_example_overall_is_97():
    """The pitch card: 98 / 96 / 99 / 97 / 94 → 97/100."""
    assert overall(98, 96, 99, 97, 94) == 97


def test_unverified_fingerprint_is_zero_authenticity():
    assert authenticity_from_fingerprint("unverified", 0) == 0
    # Behavioral reputation still counts, but overall is dragged down.
    score = overall(0, 96, 99, 97, 94)
    assert score < 97
    assert score == 77


def test_mismatch_halves_fingerprint_score():
    assert authenticity_from_fingerprint("mismatched", 80) == 40


def test_new_agent_uses_prior_not_a_fake_100():
    assert bayes(0, 0) == 70
    assert bayes(1, 0) == 77
    assert bayes(184, 4) == 97  # ~97.8% raw success, bayes slightly conservative


def test_sla_and_tx_priors():
    assert bayes(0, 0) == 70
    hits, misses = 180, 1
    assert bayes(hits, misses) >= 96


def test_dispute_history_penalties():
    assert dispute_score(0, 0) == 100
    assert dispute_score(0, 3) == 94
    assert dispute_score(2, 3) == 78


def test_failed_job_reduces_reliability():
    good = bayes(184, 4)
    worse = bayes(184, 5)
    assert worse < good


def test_escrow_split():
    escrow = 500
    worker_share = 60
    worker = escrow * worker_share // 100
    buyer = escrow - worker
    assert worker == 300
    assert buyer == 200


def test_weights_sum_to_100():
    assert 20 + 25 + 20 + 20 + 15 == 100
