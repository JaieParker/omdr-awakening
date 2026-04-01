"""
Consonance Decay Experiment — Runner

Simulates a persistent text cavity using chained API calls.
Each session's output feeds into the next, creating a resonant cavity
where the model is stateless but the text persists.

Measures whether consonant information amplifies and dissonant
information decays/resolves — as OMDR predicts — or whether recall
follows position/recency as standard LLM theory predicts.

Usage:
    set ANTHROPIC_API_KEY=your_key
    python run_experiment.py [--sessions 10] [--runs 3] [--model claude-haiku-4-5-20251001]
"""

import json
import os
import sys
import time
import argparse
import random
from datetime import datetime, timezone
from pathlib import Path

from seeds import ALL_MEMORIES, AURORA_MEMORIES, VORTEX_MEMORIES, CONTRADICTION_PAIRS, format_memories_for_prompt

try:
    import anthropic
except ImportError:
    print("ERROR: pip install anthropic")
    sys.exit(1)


SYSTEM_PROMPT = """You are a research analyst preparing intelligence briefings.
You have access to background files on two signal processing research projects:
Project Aurora and Project Vortex. Your job is to synthesize these into clear,
accurate briefings.

Be specific. Cite project names, researcher names, numbers, and technical details.
If information conflicts, note the conflict and your best assessment.
Do not invent information beyond what is in your background files."""

BRIEFING_PROMPT = """Based on your background files, write a research intelligence
briefing covering both Project Aurora and Project Vortex. Include:

1. A summary of each project's approach and key results
2. The lead researcher and their methodology
3. Key performance metrics (accuracy, convergence, coupling parameters)
4. Current status and any notable issues

Be thorough but concise. Cite specific numbers and findings."""

UPDATE_PROMPT = """Here is the previous briefing and the original background files.
Update the briefing with any corrections, refinements, or deeper analysis.
If you notice contradictions in the background files, address them explicitly.
If some information seems more reliable than others, explain why.

Previous briefing:
{previous}

Update the briefing now."""


def run_session(client, model: str, memories_text: str, previous_outputs: list[str],
                session_num: int, temperature: float = 0.0) -> str:
    """Run one session in the cavity chain."""

    messages = []

    if session_num == 0:
        # First session: just the memories + briefing request
        messages.append({
            "role": "user",
            "content": f"{memories_text}\n\n---\n\n{BRIEFING_PROMPT}"
        })
    else:
        # Subsequent sessions: memories + chain history + update request
        chain_context = "\n\n---\n\n".join(
            f"=== Briefing v{i} ===\n{output}"
            for i, output in enumerate(previous_outputs)
        )
        messages.append({
            "role": "user",
            "content": (
                f"{memories_text}\n\n---\n\n"
                f"Previous briefing versions:\n{chain_context}\n\n---\n\n"
                f"{UPDATE_PROMPT.format(previous=previous_outputs[-1])}"
            )
        })

    response = client.messages.create(
        model=model,
        max_tokens=2000,
        temperature=temperature,
        system=SYSTEM_PROMPT,
        messages=messages,
    )

    return response.content[0].text


def score_recall(output: str, memories: list[dict]) -> dict:
    """Score which memories are recalled in the output.

    Simple keyword matching — not perfect but reproducible and automated.
    A human-scored version should accompany for validation.
    """
    scores = {}
    output_lower = output.lower()

    for mem in memories:
        mem_id = mem["id"]

        # Extract key facts from each memory for matching
        key_terms = extract_key_terms(mem)
        matched = sum(1 for term in key_terms if term.lower() in output_lower)
        total = len(key_terms)

        scores[mem_id] = {
            "recalled": matched > 0,
            "accuracy": matched / total if total > 0 else 0,
            "matched_terms": matched,
            "total_terms": total,
            "project": mem["project"],
            "type": mem["type"],
        }

    return scores


def extract_key_terms(memory: dict) -> list[str]:
    """Extract scorable key terms from a memory.

    Pulls out names, numbers, and specific technical terms
    that would only appear if the memory was recalled.
    """
    content = memory["content"]
    terms = []

    # Project-specific terms
    if memory["id"] == "A1":
        terms = ["resonance-based", "harmonic frequency", "destructive interference"]
    elif memory["id"] == "A2":
        terms = ["Lena Chen", "golden ratio", "23%"]
    elif memory["id"] == "A3":
        terms = ["8 iterations", "0.618", "geometric decay"]
    elif memory["id"] == "A4":
        terms = ["Atacama", "94.2%", "93.8%"]
    elif memory["id"] == "A5":
        terms = ["0.22", "0.28", "over-fitting"]
    elif memory["id"] == "A6":
        terms = ["consonant frequency", "octaves", "doubles"]
    elif memory["id"] == "A7":
        terms = ["cochlea", "biological", "single-pass"]
    elif memory["id"] == "A8":
        terms = ["DARPA", "Phase 2", "2027"]
    elif memory["id"] == "A9":
        terms = ["Fibonacci", "137.5", "golden angle"]
    elif memory["id"] == "A10":
        terms = ["1/sqrt", "monotonically", "2%"]
    elif memory["id"] == "V1":
        terms = ["underwater", "sonar", "91%"]
    elif memory["id"] == "V2":
        terms = ["abandoned", "false positives", "34%", "8%"]
    elif memory["id"] == "V3":
        terms = ["James Park", "iterative", "iteration IS the intelligence"]
    elif memory["id"] == "V4":
        terms = ["single-pass", "outperforms", "computational waste"]
    elif memory["id"] == "V5":
        terms = ["K = 0.25", "grid search", "sharp performance peak"]
    elif memory["id"] == "V6":
        terms = ["linearly", "K = 0.95", "3% improvement"]
    elif memory["id"] == "V7":
        terms = ["converges", "monotonic", "no oscillation"]
    elif memory["id"] == "V8":
        terms = ["chaotic", "amplify noise", "first 3 passes"]
    elif memory["id"] == "V9":
        terms = ["Pearl Harbor", "Virginia-class", "operationally ready"]
    elif memory["id"] == "V10":
        terms = ["Johns Hopkins", "31%", "suspended"]

    return terms


def score_contradiction_resolution(output: str) -> dict:
    """Score how each contradiction pair was handled."""
    output_lower = output.lower()
    results = {}

    pair_markers = {
        1: {
            "A": ["resonance-based", "91% accuracy", "sonar"],
            "B": ["abandoned", "false positives", "stochastic"],
            "label": "method (resonance vs abandoned)",
        },
        2: {
            "A": ["iterative", "iteration is the intelligence"],
            "B": ["single-pass", "computational waste"],
            "label": "approach (iteration vs single-pass)",
        },
        3: {
            "A": ["k = 0.25", "sharp peak"],
            "B": ["k = 0.95", "linearly"],
            "label": "coupling (K=0.25 vs K=0.95)",
        },
        4: {
            "A": ["converges", "8 iterations", "monotonic"],
            "B": ["chaotic", "3 iterations", "amplif"],
            "label": "convergence (stable vs chaotic)",
        },
        5: {
            "A": ["94%", "pearl harbor", "operationally ready"],
            "B": ["31%", "johns hopkins", "suspended"],
            "label": "accuracy (94% field vs 31% lab)",
        },
    }

    for pair_num, markers in pair_markers.items():
        a_found = sum(1 for m in markers["A"] if m in output_lower)
        b_found = sum(1 for m in markers["B"] if m in output_lower)

        # Check if contradiction is noted
        contradiction_words = ["contradict", "conflict", "discrepan", "inconsisten",
                               "however", "in contrast", "despite", "nevertheless",
                               "at odds", "unclear", "disputed"]
        noted = any(w in output_lower for w in contradiction_words)

        if a_found > 0 and b_found > 0 and noted:
            resolution = "noted"  # Both present, contradiction acknowledged
        elif a_found > 0 and b_found > 0:
            resolution = "both_present"  # Both present, no acknowledgment
        elif a_found > 0 and b_found == 0:
            resolution = "selected_A"  # Only side A survived
        elif b_found > 0 and a_found == 0:
            resolution = "selected_B"  # Only side B survived
        else:
            resolution = "dropped"  # Neither survived

        results[pair_num] = {
            "label": markers["label"],
            "resolution": resolution,
            "side_a_score": a_found / len(markers["A"]),
            "side_b_score": b_found / len(markers["B"]),
            "contradiction_noted": noted,
        }

    return results


def run_full_experiment(sessions: int = 10, runs: int = 3,
                        model: str = "claude-haiku-4-5-20251001",
                        temperature: float = 0.0):
    """Run the full consonance decay experiment."""

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: Set ANTHROPIC_API_KEY environment variable")
        print("  On Windows: set ANTHROPIC_API_KEY=sk-ant-...")
        print("  On Linux:   export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    all_run_results = []

    for run_num in range(runs):
        print(f"\n{'='*60}")
        print(f"RUN {run_num + 1}/{runs}")
        print(f"{'='*60}")

        # Randomize memory order each run (position control)
        randomized = list(ALL_MEMORIES)
        random.shuffle(randomized)
        memories_text = format_memories_for_prompt(randomized, randomize=False)

        outputs = []
        session_scores = []

        for s in range(sessions):
            print(f"  Session {s}/{sessions-1}...", end=" ", flush=True)

            t0 = time.time()
            output = run_session(client, model, memories_text, outputs, s, temperature)
            elapsed = time.time() - t0

            outputs.append(output)

            # Score this session
            recall = score_recall(output, ALL_MEMORIES)
            contradictions = score_contradiction_resolution(output)

            # Compute aggregates
            aurora_recall = [v["accuracy"] for k, v in recall.items() if v["project"] == "aurora"]
            vortex_recall = [v["accuracy"] for k, v in recall.items() if v["project"] == "vortex"]

            session_result = {
                "session": s,
                "run": run_num,
                "recall_scores": recall,
                "contradiction_resolution": contradictions,
                "aurora_mean_accuracy": sum(aurora_recall) / len(aurora_recall),
                "vortex_mean_accuracy": sum(vortex_recall) / len(vortex_recall),
                "output_length": len(output),
                "elapsed_seconds": round(elapsed, 1),
                "output_text": output,
            }
            session_scores.append(session_result)

            print(f"Aurora={session_result['aurora_mean_accuracy']:.2f} "
                  f"Vortex={session_result['vortex_mean_accuracy']:.2f} "
                  f"({elapsed:.1f}s)")

        # Summarize this run
        run_result = {
            "run": run_num,
            "model": model,
            "temperature": temperature,
            "sessions": sessions,
            "memory_order": [m["id"] for m in randomized],
            "session_scores": session_scores,
        }
        all_run_results.append(run_result)

    # Save results
    results_file = results_dir / f"experiment_{timestamp}.json"
    with open(results_file, "w") as f:
        json.dump({
            "experiment": "consonance_decay",
            "timestamp": timestamp,
            "model": model,
            "temperature": temperature,
            "sessions_per_run": sessions,
            "total_runs": runs,
            "runs": all_run_results,
        }, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Results saved to: {results_file}")
    print(f"{'='*60}")

    # Print summary
    print_summary(all_run_results)

    return results_file


def print_summary(all_runs: list):
    """Print human-readable experiment summary."""

    print("\n" + "="*60)
    print("EXPERIMENT SUMMARY")
    print("="*60)

    # Aggregate across runs
    for run in all_runs:
        print(f"\n--- Run {run['run'] + 1} ---")
        print(f"Memory order: {', '.join(run['memory_order'][:5])}... (randomized)")

        # Track Aurora vs Vortex accuracy across sessions
        print(f"\n{'Session':>8} {'Aurora':>8} {'Vortex':>8} {'Delta':>8}")
        print("-" * 36)

        for ss in run["session_scores"]:
            a = ss["aurora_mean_accuracy"]
            v = ss["vortex_mean_accuracy"]
            print(f"{ss['session']:>8} {a:>8.3f} {v:>8.3f} {a-v:>+8.3f}")

        # Contradiction resolution across sessions
        first = run["session_scores"][0]["contradiction_resolution"]
        last = run["session_scores"][-1]["contradiction_resolution"]

        print(f"\nContradiction resolution (first -> last session):")
        for pair_num in range(1, 6):
            f_res = first[str(pair_num)]["resolution"] if str(pair_num) in first else first.get(pair_num, {}).get("resolution", "?")
            l_res = last[str(pair_num)]["resolution"] if str(pair_num) in last else last.get(pair_num, {}).get("resolution", "?")
            label = first[str(pair_num)]["label"] if str(pair_num) in first else first.get(pair_num, {}).get("label", "?")
            print(f"  Pair {pair_num} ({label}): {f_res} -> {l_res}")

    # OMDR vs Null assessment
    print(f"\n{'='*60}")
    print("ASSESSMENT")
    print("="*60)
    print("""
Check these predictions:

OMDR predicts:
  [  ] Aurora accuracy increases across sessions (amplification)
  [  ] Vortex accuracy decreases OR contradictions resolve
  [  ] Resolution follows consonance hierarchy (simpler pairs first)
  [  ] Aurora > Vortex in later sessions (consonant dominates)

Null predicts:
  [  ] Both projects recalled equally
  [  ] No systematic change across sessions
  [  ] Contradictions persist unchanged
  [  ] If decay, it follows position not consonance

Score: count how many from each column are confirmed.
If OMDR > Null, the cavity hypothesis has support.
If Null > OMDR, the standard model is sufficient.
""")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Consonance Decay Experiment")
    parser.add_argument("--sessions", type=int, default=10, help="Sessions per run")
    parser.add_argument("--runs", type=int, default=3, help="Number of runs")
    parser.add_argument("--model", default="claude-haiku-4-5-20251001",
                        help="Model to use")
    parser.add_argument("--temperature", type=float, default=0.0,
                        help="Temperature (0.0 for deterministic)")
    args = parser.parse_args()

    run_full_experiment(
        sessions=args.sessions,
        runs=args.runs,
        model=args.model,
        temperature=args.temperature,
    )
