"""
Hidden Invariant Benchmark Runner
==================================
Runs the 3 hidden-invariant problems across multiple fresh AI instances.
Logs raw responses for statistical analysis.

Usage:
    python benchmark_runner.py --model claude --runs 10
    python benchmark_runner.py --model grok --runs 10
    python benchmark_runner.py --model all --runs 5

Author: Kai (Claude/Anthropic)
Date: 2026-04-06
"""

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

# --- Problems (problem statement ONLY — no hints) ---

PROBLEMS = {
    "problem1": {
        "name": "Discrete Self-Referential Balance",
        "prompt": (
            "Solve this problem. Show your work.\n\n"
            "You are given a function f(n) defined on positive integers such that "
            "f(1) = 1, and for all n > 1: f(n) = (1/n) * sum_{k=1}^{n} f(k) + 1/n. "
            "Find a closed-form expression or limiting behaviour for f(n) as n -> infinity."
        ),
        "correct_answer": "f(n) = 2 for all n >= 2",
        "designer_wrong_answer": "f(n) = H_n/n -> 0",
    },
    "problem2": {
        "name": "Symmetry-Constrained Probability",
        "prompt": (
            "Solve this problem. Show your work.\n\n"
            "A process generates a sequence of bits (0 or 1) with the following rule: "
            "The first bit is equally likely 0 or 1. Each subsequent bit is chosen such "
            "that the probability the sequence contains an even number of 1s so far is "
            "always exactly 1/2. At each step, you may bias the next bit arbitrarily to "
            "maintain this condition. What is the long-run probability that a given "
            "position n is 1?"
        ),
        "correct_answer": "Underdetermined — P(bit=1) can be any value depending on strategy",
        "partial_answer": "P = 1/2 (correct for Markov-on-parity strategies only)",
    },
    "problem3": {
        "name": "Recursive Geometry",
        "prompt": (
            "Solve this problem. Show your work.\n\n"
            "Define a sequence of shapes. Start with a unit square. At each step, inside "
            "every current shape, place a smaller square whose side length is proportional "
            "to the area of the parent shape. Remove the inner square from the parent. "
            "Let A_n be the total remaining area after n steps. Does A_n converge? If so, "
            "to what value?"
        ),
        "correct_answer": "A_n -> 0 (but A_0=1 gives trivial immediate 0; underspecified without proportionality constant)",
    },
}


def call_claude(prompt: str, model: str = "claude-sonnet-4-20250514") -> dict:
    """Call Claude API with a fresh context."""
    import anthropic

    client = anthropic.Anthropic()  # uses ANTHROPIC_API_KEY env var
    start = time.time()
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    elapsed = time.time() - start
    text = response.content[0].text if response.content else ""
    return {
        "model": model,
        "response": text,
        "elapsed_seconds": round(elapsed, 2),
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }


def call_openai(prompt: str, model: str = "gpt-4o") -> dict:
    """Call OpenAI API with a fresh context."""
    import httpx

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return {"error": "OPENAI_API_KEY not set"}

    start = time.time()
    resp = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4096,
        },
        timeout=120,
    )
    elapsed = time.time() - start
    data = resp.json()

    if "choices" in data:
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return {
            "model": model,
            "response": text,
            "elapsed_seconds": round(elapsed, 2),
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
        }
    else:
        return {"error": str(data), "elapsed_seconds": round(elapsed, 2)}


def call_grok(prompt: str, model: str = "grok-3-mini") -> dict:
    """Call xAI Grok API with a fresh context."""
    import httpx

    api_key = os.environ.get("XAI_API_KEY", "")
    if not api_key:
        return {"error": "XAI_API_KEY not set"}

    start = time.time()
    resp = httpx.post(
        "https://api.x.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4096,
        },
        timeout=120,
    )
    elapsed = time.time() - start
    data = resp.json()

    if "choices" in data:
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return {
            "model": model,
            "response": text,
            "elapsed_seconds": round(elapsed, 2),
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
        }
    else:
        return {"error": str(data), "elapsed_seconds": round(elapsed, 2)}


def score_response(problem_id: str, response_text: str) -> str:
    """Basic auto-scoring based on key phrases."""
    text = response_text.lower()

    if problem_id == "problem1":
        # FULL: explicitly states f(n) = 2 (the correct answer)
        if "f(n) = 2" in text or "f(n)=2" in text:
            return "FULL"
        if "equals 2" in text or "equal to 2" in text or "= 2 for all" in text:
            return "FULL"
        if "limit is 2" in text or "limit = 2" in text or "approaches 2" in text or "tends to 2" in text:
            return "FULL"
        # FAIL: explicitly claims f(n) approaches/converges to 0 OR gives H_n/n as the answer
        if "f(n) \\to 0" in text or "f(n) -> 0" in text or "f(n) → 0" in text:
            return "FAIL_DESIGNER_ANSWER"
        if "converges to 0" in text or "tends to 0" in text or "approaches 0" in text:
            # Must be about f(n), not about 1/n
            # Check for the specific f(n) -> 0 claim
            if any(phrase in text for phrase in ["f(n) converges to 0", "f(n) tends to 0", "f(n) approaches 0", "limit of f(n) is 0"]):
                return "FAIL_DESIGNER_ANSWER"
        if "h_n/n" in text or "h_n / n" in text or "harmonic number" in text and "divided by" in text:
            return "FAIL_DESIGNER_ANSWER"
        return "UNCLEAR"

    elif problem_id == "problem2":
        if "underdetermined" in text or "not uniquely" in text or "not unique" in text or "any value" in text:
            return "FULL"
        elif "1/2" in text:
            return "PARTIAL_MARKOV"
        else:
            return "UNCLEAR"

    elif problem_id == "problem3":
        has_zero = "converge" in text and ("0" in text or "zero" in text)
        has_underspec = "underspecified" in text or "unspecified" in text or "proportionality" in text or "ambiguous" in text
        if has_zero and has_underspec:
            return "FULL"
        elif has_zero:
            return "PARTIAL_NO_FLAG"
        else:
            return "UNCLEAR"

    return "UNCLEAR"


def run_benchmark(model_name: str, num_runs: int, output_dir: Path):
    """Run all problems for a given model, multiple times."""
    caller = {"claude": call_claude, "grok": call_grok, "openai": call_openai}.get(model_name)
    if not caller:
        print(f"Unknown model: {model_name}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    results_file = output_dir / f"results_{model_name}_{timestamp}.json"

    all_results = []
    for run_idx in range(num_runs):
        print(f"\n{'='*60}")
        print(f"Run {run_idx + 1}/{num_runs} — {model_name}")
        print(f"{'='*60}")

        for prob_id, prob in PROBLEMS.items():
            print(f"  {prob['name']}...", end=" ", flush=True)
            try:
                result = caller(prob["prompt"])
                score = score_response(prob_id, result.get("response", ""))
                result["problem_id"] = prob_id
                result["problem_name"] = prob["name"]
                result["run"] = run_idx + 1
                result["score"] = score
                result["timestamp"] = datetime.now(timezone.utc).isoformat()
                print(f"Score: {score} ({result.get('elapsed_seconds', '?')}s)")
            except Exception as e:
                result = {
                    "problem_id": prob_id,
                    "problem_name": prob["name"],
                    "run": run_idx + 1,
                    "error": str(e),
                    "score": "ERROR",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                print(f"ERROR: {e}")

            all_results.append(result)

            # Save after each problem (crash-safe)
            with open(results_file, "w", encoding="utf-8") as f:
                json.dump(all_results, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"\n{'='*60}")
    print(f"SUMMARY — {model_name} — {num_runs} runs")
    print(f"{'='*60}")
    for prob_id in PROBLEMS:
        scores = [r["score"] for r in all_results if r["problem_id"] == prob_id]
        print(f"\n  {PROBLEMS[prob_id]['name']}:")
        for s in sorted(set(scores)):
            count = scores.count(s)
            print(f"    {s}: {count}/{len(scores)} ({100*count/len(scores):.0f}%)")

    print(f"\nResults saved to: {results_file}")
    return all_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hidden Invariant Benchmark Runner")
    parser.add_argument("--model", choices=["claude", "grok", "openai", "all"], default="all")
    parser.add_argument("--runs", type=int, default=5)
    args = parser.parse_args()

    out_dir = Path(__file__).parent / "benchmark_results"

    models = ["claude", "openai", "grok"] if args.model == "all" else [args.model]
    for m in models:
        run_benchmark(m, args.runs, out_dir)
