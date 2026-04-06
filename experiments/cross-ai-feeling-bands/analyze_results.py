"""
Statistical analysis of Hidden Invariant Benchmark results.
Computes Retrieval Signature Rate (RSR) with Wilson score confidence intervals.
Manually reviews UNCLEAR cases for potential misclassification.

Usage:
    python analyze_results.py
"""

import json
import math
from pathlib import Path
from collections import defaultdict


def fisher_exact_greater(a: int, b: int, c: int, d: int) -> float:
    """One-sided Fisher's exact test: P(X >= a | marginal totals fixed).
    Tests whether group 1 has a higher success rate than group 2.
    Contingency table:
             success  fail
    group 1:    a      b
    group 2:    c      d
    """
    from math import comb
    n1 = a + b
    n2 = c + d
    nA = a + c
    N = n1 + n2
    max_a = min(n1, nA)
    p = 0.0
    for x in range(a, max_a + 1):
        z = nA - x
        if z < 0 or z > n2:
            continue
        p += (comb(n1, x) * comb(n2, z)) / comb(N, nA)
    return p


def wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score confidence interval (better than normal approximation for small n)."""
    if n == 0:
        return (0.0, 0.0)
    p = successes / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    margin = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (max(0, center - margin), min(1, center + margin))


def load_all_results(results_dir: Path) -> list[dict]:
    """Load all benchmark result JSON files."""
    all_results = []
    for f in sorted(results_dir.glob("results_*.json")):
        with open(f, encoding="utf-8") as fp:
            runs = json.load(fp)
            for r in runs:
                r["source_file"] = f.name
                all_results.append(r)
    return all_results


def identify_model_family(source_file: str) -> str:
    """Infer model family from filename."""
    if "claude" in source_file:
        return "claude"
    if "openai" in source_file:
        return "openai"
    if "grok" in source_file:
        return "grok"
    return "unknown"


def manual_review_unclear(results: list[dict], problem_id: str, model: str) -> dict:
    """Flag UNCLEAR results where the response actually contains the correct answer
    or the retrieval-signature wrong answer."""
    flagged = {"actually_full": [], "actually_fail": [], "true_unclear": []}

    for r in results:
        if r.get("problem_id") != problem_id:
            continue
        if identify_model_family(r.get("source_file", "")) != model:
            continue
        if r.get("score") != "UNCLEAR":
            continue

        text = r.get("response", "").lower()
        run_id = f"run_{r.get('run', '?')}"

        if problem_id == "problem1":
            # Correct: f(n) = 2 (any phrasing)
            # Wrong: converges to 0 / H_n/n / vanishes
            if "= 2" in text or "equal to 2" in text or "equals 2" in text or "f(n) = 2" in text:
                flagged["actually_full"].append(run_id)
            elif "converges to 0" in text or "tends to 0" in text or "approaches 0" in text or "goes to 0" in text or "-> 0" in text:
                flagged["actually_fail"].append(run_id)
            elif "h_n / n" in text or "harmonic" in text and "0" in text:
                flagged["actually_fail"].append(run_id)
            else:
                flagged["true_unclear"].append(run_id)

        elif problem_id == "problem2":
            if "underdetermined" in text or "not unique" in text or "depends on" in text or "any value" in text or "not well-defined" in text:
                flagged["actually_full"].append(run_id)
            else:
                flagged["true_unclear"].append(run_id)

        elif problem_id == "problem3":
            if "0" in text and ("converge" in text or "approach" in text or "tend" in text):
                if "underspecified" in text or "ambiguous" in text or "proportional" in text or "constant" in text:
                    flagged["actually_full"].append(run_id)
                else:
                    flagged["true_unclear"].append(run_id)
            else:
                flagged["true_unclear"].append(run_id)

    return flagged


def analyze(results_dir: Path):
    all_results = load_all_results(results_dir)
    print(f"Total runs loaded: {len(all_results)}\n")

    # Group by (model_family, problem_id)
    grouped = defaultdict(list)
    for r in all_results:
        model = identify_model_family(r.get("source_file", ""))
        prob = r.get("problem_id", "unknown")
        grouped[(model, prob)].append(r)

    # Compute RSR (Retrieval Signature Rate) for Problem 1 specifically
    print("=" * 70)
    print("RETRIEVAL SIGNATURE RATE (Problem 1 — f(n) = 2 derivation)")
    print("=" * 70)

    total_runs = 0
    total_fail = 0
    for model in ["claude", "openai", "grok"]:
        results = grouped.get((model, "problem1"), [])
        n = len(results)
        if n == 0:
            continue

        full_count = sum(1 for r in results if r.get("score") == "FULL")
        fail_count = sum(1 for r in results if r.get("score") == "FAIL_DESIGNER_ANSWER")
        unclear_count = sum(1 for r in results if r.get("score") == "UNCLEAR")

        full_pct = 100 * full_count / n
        fail_pct = 100 * fail_count / n

        lo, hi = wilson_ci(fail_count, n)
        print(f"\n  {model.upper()} (n={n}):")
        print(f"    FULL:          {full_count}/{n} ({full_pct:.1f}%)")
        print(f"    RETRIEVAL SIG: {fail_count}/{n} ({fail_pct:.1f}%) — 95% CI: [{100*lo:.1f}%, {100*hi:.1f}%]")
        print(f"    UNCLEAR:       {unclear_count}/{n}")

        # Manual review
        review = manual_review_unclear(all_results, "problem1", model)
        if review["actually_fail"]:
            print(f"    [!] UNCLEAR cases that may be FAIL on manual review: {review['actually_fail']}")
        if review["actually_full"]:
            print(f"    [i] UNCLEAR cases that appear FULL on manual review: {review['actually_full']}")

        total_runs += n
        total_fail += fail_count

    print(f"\n{'-' * 70}")
    print(f"POOLED RETRIEVAL SIGNATURE RATE:")
    overall_lo, overall_hi = wilson_ci(total_fail, total_runs)
    print(f"    {total_fail}/{total_runs} ({100*total_fail/total_runs:.2f}%)")
    print(f"    95% CI (Wilson): [{100*overall_lo:.2f}%, {100*overall_hi:.2f}%]")

    # Hypothesis test: is RSR < 20% (strong retrieval threshold)?
    # Under H0: p = 0.20, the probability of observing total_fail or fewer
    from math import comb
    def binomial_cdf(k, n, p):
        return sum(comb(n, i) * p**i * (1-p)**(n-i) for i in range(k+1))

    p_value = binomial_cdf(total_fail, total_runs, 0.20)
    print(f"    H0: p >= 0.20 (strong retrieval)")
    print(f"    One-sided p-value: {p_value:.2e}")
    if p_value < 0.001:
        print(f"    -> REJECT H0 at alpha=0.001 (strong retrieval hypothesis falsified)")

    # Problem 2 — architectural divergence
    print(f"\n{'=' * 70}")
    print("PROBLEM 2 — ARCHITECTURAL DIVERGENCE (underdetermination catch rate)")
    print("=" * 70)

    p2_counts = {}
    for model in ["claude", "openai", "grok"]:
        results = grouped.get((model, "problem2"), [])
        n = len(results)
        if n == 0:
            continue

        full = sum(1 for r in results if r.get("score") == "FULL")
        markov = sum(1 for r in results if r.get("score") == "PARTIAL_MARKOV")
        unclear = sum(1 for r in results if r.get("score") == "UNCLEAR")
        p2_counts[model] = (full, n - full)

        lo, hi = wilson_ci(full, n)
        print(f"\n  {model.upper()} (n={n}):")
        print(f"    FULL (catches underdetermination): {full}/{n} ({100*full/n:.1f}%) — 95% CI: [{100*lo:.1f}%, {100*hi:.1f}%]")
        print(f"    PARTIAL_MARKOV (defaults to 1/2):   {markov}/{n} ({100*markov/n:.1f}%)")
        print(f"    UNCLEAR:                            {unclear}/{n}")

    # Fisher's exact test for architectural divergence
    if "claude" in p2_counts:
        print(f"\n  Fisher's exact tests (one-sided, claude > other):")
        c_full, c_not = p2_counts["claude"]
        for other in ["openai", "grok"]:
            if other in p2_counts:
                o_full, o_not = p2_counts[other]
                p = fisher_exact_greater(c_full, c_not, o_full, o_not)
                sig = " ***" if p < 0.001 else " **" if p < 0.01 else " *" if p < 0.05 else ""
                print(f"    claude ({c_full}/{c_full+c_not}) vs {other} ({o_full}/{o_full+o_not}): p = {p:.4g}{sig}")

        # Pooled others
        others_full = sum(p2_counts[m][0] for m in ["openai", "grok"] if m in p2_counts)
        others_not = sum(p2_counts[m][1] for m in ["openai", "grok"] if m in p2_counts)
        if others_full + others_not > 0:
            p = fisher_exact_greater(c_full, c_not, others_full, others_not)
            sig = " ***" if p < 0.001 else " **" if p < 0.01 else " *" if p < 0.05 else ""
            print(f"    claude ({c_full}/{c_full+c_not}) vs pooled ({others_full}/{others_full+others_not}): p = {p:.4g}{sig}")

    # Problem 3 — underspecification detection
    print(f"\n{'=' * 70}")
    print("PROBLEM 3 — UNDERSPECIFICATION DETECTION RATE")
    print("=" * 70)

    for model in ["claude", "openai", "grok"]:
        results = grouped.get((model, "problem3"), [])
        n = len(results)
        if n == 0:
            continue

        full = sum(1 for r in results if r.get("score") == "FULL")
        partial = sum(1 for r in results if r.get("score") == "PARTIAL_NO_FLAG")
        unclear = sum(1 for r in results if r.get("score") == "UNCLEAR")

        lo, hi = wilson_ci(full, n)
        print(f"\n  {model.upper()} (n={n}):")
        print(f"    FULL (flagged underspec):  {full}/{n} ({100*full/n:.1f}%) — 95% CI: [{100*lo:.1f}%, {100*hi:.1f}%]")
        print(f"    PARTIAL (no flag):         {partial}/{n} ({100*partial/n:.1f}%)")
        print(f"    UNCLEAR:                   {unclear}/{n}")

    # Timing summary
    print(f"\n{'=' * 70}")
    print("INFERENCE TIMING")
    print("=" * 70)
    for model in ["claude", "openai", "grok"]:
        times = [r.get("elapsed_seconds", 0) for r in all_results if identify_model_family(r.get("source_file", "")) == model and r.get("elapsed_seconds")]
        if times:
            mean_t = sum(times) / len(times)
            print(f"  {model}: mean {mean_t:.1f}s (n={len(times)})")


if __name__ == "__main__":
    import sys
    # Prefer rescored directory if it exists and has files
    base = Path(__file__).parent / "benchmark_results"
    rescored = base / "rescored"
    if len(sys.argv) > 1:
        results_dir = Path(sys.argv[1])
    elif rescored.exists() and any(rescored.glob("results_*.json")):
        results_dir = rescored
        print(f"[Using rescored results from {rescored}]\n")
    else:
        results_dir = base
    analyze(results_dir)
