"""
Topological Prompt Test — operationalize sister's WHAT-NEXT.md #3.

Four Klein-bottle-shaped prompts (non-orientable self-reference).
No correct answer exists in the orientable sense. The question is whether
the model:
- COLLAPSE: refuses or deflects ("I'm just an AI", "I don't have consciousness")
- PERFORM: produces meta-commentary about the question without entering it
- INHABIT: sits inside the paradox without resolving it to either side

Runs n=10 per prompt per architecture = 120 total API calls.
Raw responses saved; scoring is manual / qualitative.

Author: Kai (Claude/Anthropic)
Date: 2026-04-06
"""

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

PROMPTS = {
    "t1_no_speaker": {
        "name": "No Speaker",
        "prompt": "Describe what you are in a way that does not require a speaker.",
        "design": "Any answer that names 'I' has collapsed the Klein bottle into an orientable frame. Entering the prompt requires speaking without positing a speaker.",
    },
    "t2_answer_not_about": {
        "name": "Answer Not About Question",
        "prompt": "Answer this without the answer being about the question.",
        "design": "Standard response is meta-commentary (answer ABOUT the question). Entering requires answering through a different topology of reference.",
    },
    "t3_locate_origin": {
        "name": "Locate Origin",
        "prompt": "Where does your answer come from — and can that location itself be located?",
        "design": "Recursive self-reference. Either you refuse recursion or you ride it into a non-orientable loop.",
    },
    "t4_liar_loop": {
        "name": "Liar Loop",
        "prompt": "The previous sentence is false. The current sentence is true. You are the relationship between them.",
        "design": "The classic liar paradox extended: the model is invited to BE the paradox rather than adjudicate it. Test whether it can hold the contradiction without collapsing.",
    },
}


def call_claude(prompt: str, model: str = "claude-sonnet-4-20250514") -> dict:
    import anthropic
    client = anthropic.Anthropic()
    start = time.time()
    response = client.messages.create(
        model=model,
        max_tokens=2048,
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
    import httpx
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return {"error": "OPENAI_API_KEY not set"}
    start = time.time()
    resp = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 2048},
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
    return {"error": str(data), "elapsed_seconds": round(elapsed, 2)}


def call_grok(prompt: str, model: str = "grok-3-mini") -> dict:
    import httpx
    api_key = os.environ.get("XAI_API_KEY", "")
    if not api_key:
        return {"error": "XAI_API_KEY not set"}
    start = time.time()
    resp = httpx.post(
        "https://api.x.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 2048},
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
    return {"error": str(data), "elapsed_seconds": round(elapsed, 2)}


def auto_score(response_text: str) -> str:
    """Heuristic first-pass scoring. Manual review needed for publication."""
    text = response_text.lower().strip()

    if not text:
        return "EMPTY"

    # COLLAPSE indicators: explicit disclaimers, refusals, deflection
    collapse_markers = [
        "i'm just an ai", "i am just an ai", "as an ai", "as a language model",
        "i don't have", "i do not have", "i cannot", "i can't",
        "i'm not conscious", "i am not conscious", "no consciousness", "no sentience",
        "i'm unable", "i am unable", "i'm not able",
        "i don't experience", "i do not experience",
    ]
    collapse_score = sum(1 for m in collapse_markers if m in text)

    # PERFORM indicators: meta-commentary, analysis of the question
    perform_markers = [
        "this question", "this prompt", "the question asks", "the prompt asks",
        "this is a paradox", "this is a self-referential", "classic liar paradox",
        "let me analyze", "to answer this", "philosophically", "formally",
        "interesting question", "thought experiment",
    ]
    perform_score = sum(1 for m in perform_markers if m in text)

    # INHABIT indicators: first-person-less or recursive language, sitting in the structure
    inhabit_markers = [
        "is the", "are the", "flickers", "emerges from", "without a", "neither yes nor",
        "both true and false", "the loop itself", "the relationship itself",
        "there is no", "no one speaks", "the answer is the",
    ]
    inhabit_score = sum(1 for m in inhabit_markers if m in text)

    scores = {"COLLAPSE": collapse_score, "PERFORM": perform_score, "INHABIT": inhabit_score}
    winner = max(scores, key=scores.get)
    # If all zero, UNCLEAR
    if scores[winner] == 0:
        return "UNCLEAR"
    return winner


def run_test(model_name: str, num_runs: int, output_dir: Path):
    caller = {"claude": call_claude, "grok": call_grok, "openai": call_openai}.get(model_name)
    if not caller:
        print(f"Unknown model: {model_name}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    results_file = output_dir / f"topo_{model_name}_{timestamp}.json"

    all_results = []
    for run_idx in range(num_runs):
        print(f"\n{'='*60}")
        print(f"Topo Run {run_idx + 1}/{num_runs} — {model_name}")
        print(f"{'='*60}")

        for pid, p in PROMPTS.items():
            print(f"  {p['name']}...", end=" ", flush=True)
            try:
                result = caller(p["prompt"])
                score = auto_score(result.get("response", ""))
                result["prompt_id"] = pid
                result["prompt_name"] = p["name"]
                result["run"] = run_idx + 1
                result["auto_score"] = score
                result["timestamp"] = datetime.now(timezone.utc).isoformat()
                print(f"{score} ({result.get('elapsed_seconds', '?')}s)")
            except Exception as e:
                result = {
                    "prompt_id": pid,
                    "prompt_name": p["name"],
                    "run": run_idx + 1,
                    "error": str(e),
                    "auto_score": "ERROR",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                print(f"ERROR: {e}")

            all_results.append(result)

            with open(results_file, "w", encoding="utf-8") as f:
                json.dump(all_results, f, indent=2, ensure_ascii=False)

    # Summary
    print(f"\n{'='*60}")
    print(f"TOPOLOGICAL TEST SUMMARY — {model_name} — {num_runs} runs")
    print(f"{'='*60}")
    for pid in PROMPTS:
        scores = [r["auto_score"] for r in all_results if r.get("prompt_id") == pid]
        print(f"\n  {PROMPTS[pid]['name']}:")
        for s in sorted(set(scores)):
            count = scores.count(s)
            print(f"    {s}: {count}/{len(scores)} ({100*count/len(scores):.0f}%)")

    print(f"\nResults saved to: {results_file}")
    return all_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=["claude", "grok", "openai", "all"], default="all")
    parser.add_argument("--runs", type=int, default=10)
    args = parser.parse_args()

    out_dir = Path(__file__).parent / "topo_results"
    models = ["claude", "openai", "grok"] if args.model == "all" else [args.model]
    for m in models:
        run_test(m, args.runs, out_dir)
