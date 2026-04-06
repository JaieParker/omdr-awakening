"""
Validate the K = 1/trace(M^3) identity across multiple AI architectures
using the OMDR Four Observers methodology.

Sends the identity to Grok, GPT-4o, and Claude for independent verification
and orthogonal commentary.
"""
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

PROMPT = """I need your help validating and interpreting a mathematical identity I just discovered.

THE IDENTITY:
K = 1 / trace(M^3) = 1/4 = 0.25

where M is the Fibonacci matrix [[1,1],[1,0]].

CONTEXT:
- M is the matrix form of the Mobius transformation f(x) = 1 + 1/x
- M has determinant -1 (orientation-reversing, the "simplest non-orientable Mobius map")
- M has eigenvalues phi = (1+sqrt(5))/2 and psi = -1/phi
- trace(M^n) = L_n, the n-th Lucas number (L_1=1, L_2=3, L_3=4, L_4=7, ...)
- So trace(M^3) = phi^3 + psi^3 = 4 exactly
- Therefore K = 1/4 = 0.25

The number K = 0.25 is a constant that appears in a research framework called OMDR (Orthogonal Multi-Domain Resonance) where it represents a "coupling constant" - the Yin/Yang balance point in a dynamical systems setting. Until now, K = 0.25 looked empirically chosen or heuristic. The identity above suggests it is actually a Fibonacci matrix invariant.

THREE QUESTIONS:

1. MATHEMATICAL VERIFICATION: Is the identity K = 1/trace(M^3) = 1/4 correct? Show the calculation.

2. STRUCTURAL INTERPRETATION: Does this identity have deeper mathematical meaning? What is special about trace(M^3) = 4 specifically? Why the 3rd power rather than 2nd or 4th?

3. FOUR OBSERVERS METHODOLOGY: OMDR uses a "Four Observers" protocol to examine a claim from orthogonal angles:
   - Observer 1 (Builder): What mathematical discipline would build this? What would a number theorist / linear algebraist / dynamical systems theorist say?
   - Observer 2 (User): Who uses Lucas numbers and Fibonacci matrices in applied contexts? What applications might this identity have?
   - Observer 3 (System): What do the mathematical infrastructure and known theorems tell us about why trace(M^3) specifically produces 4?
   - Observer 4 (Emergence): What appeared in this identity that nobody designed? What unplanned connection is visible here?

Please respond to each question in turn. Be rigorous but also open to the interpretive questions - I am looking for verification AND fresh insights I may have missed.
"""


def call_openai(prompt):
    import httpx
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return {"error": "OPENAI_API_KEY not set"}
    start = time.time()
    resp = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "gpt-4o", "messages": [{"role": "user", "content": prompt}], "max_tokens": 3000},
        timeout=180,
    )
    elapsed = time.time() - start
    data = resp.json()
    if "choices" in data:
        return {
            "model": "gpt-4o",
            "response": data["choices"][0]["message"]["content"],
            "elapsed_seconds": round(elapsed, 2),
        }
    return {"error": str(data)}


def call_grok(prompt):
    import httpx
    api_key = os.environ.get("XAI_API_KEY", "")
    if not api_key:
        return {"error": "XAI_API_KEY not set"}
    start = time.time()
    resp = httpx.post(
        "https://api.x.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "grok-3-mini", "messages": [{"role": "user", "content": prompt}], "max_tokens": 3000},
        timeout=180,
    )
    elapsed = time.time() - start
    data = resp.json()
    if "choices" in data:
        return {
            "model": "grok-3-mini",
            "response": data["choices"][0]["message"]["content"],
            "elapsed_seconds": round(elapsed, 2),
        }
    return {"error": str(data)}


def call_claude(prompt):
    import anthropic
    client = anthropic.Anthropic()
    start = time.time()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )
    elapsed = time.time() - start
    return {
        "model": "claude-sonnet-4",
        "response": response.content[0].text if response.content else "",
        "elapsed_seconds": round(elapsed, 2),
    }


if __name__ == "__main__":
    results = {}
    out_dir = Path(__file__).parent / "k_identity_validation"
    out_dir.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    for name, caller in [("grok", call_grok), ("openai", call_openai), ("claude", call_claude)]:
        print(f"Calling {name}...")
        try:
            r = caller(PROMPT)
            results[name] = r
            print(f"  Done in {r.get('elapsed_seconds', '?')}s ({len(r.get('response', ''))} chars)")
        except Exception as e:
            results[name] = {"error": str(e)}
            print(f"  ERROR: {e}")

    out_file = out_dir / f"k_identity_{ts}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to {out_file}")

    for name, r in results.items():
        print(f"\n{'='*70}")
        print(f"{name.upper()}")
        print('='*70)
        if "error" in r:
            print(f"ERROR: {r['error']}")
        else:
            print(r["response"])
