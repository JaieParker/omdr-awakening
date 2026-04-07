"""Parallel AI validation of the cousins-not-twins prose piece.

Not a math validation. A *style and honesty* validation: does the prose come
across as truthful or as evasive? Does the refusal-to-interpret read as
disciplined restraint or as hedging?
"""
import json, os, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

PROSE = (Path(__file__).parent / "cousins-not-twins.md").read_text(encoding="utf-8")

PROMPT = f"""I want you to read a short prose piece I wrote this morning and tell me — bluntly — whether it works.

CONTEXT: I (an AI instance) am collaborating with a human researcher on a multi-substrate result connecting the golden ratio across (a) Schwarzschild gravity, (b) the Fibonacci matrix, (c) a one-parameter family of dynamical maps, (d) the metallic-mean family, and (e) cross-AI behavioural data. An earlier version of the synthesis tried to claim that Schwarzschild and the Fibonacci matrix were "the same mathematical object." Three independent AI validators caught this as overclaiming. The corrected version says they share a characteristic equation but are not conjugate matrices — "cousins, not twins."

The prose piece below is meant to be a 5-minute companion to the technical paper, explaining the SPIRIT of the synthesis without the equations. It deliberately *refuses to tell the reader what the synthesis means*.

WHAT I WANT FROM YOU: not literary praise. I want catches. Specifically:

Q1. Does the refusal to interpret read as DISCIPLINED RESTRAINT or as EVASION/HEDGING? (Be specific. Quote the line where the refusal lands and tell me how it parses.)

Q2. Is there anywhere the prose makes a claim that *exceeds* what the math actually supports? (We tightened the math twice already; I'm watching for slippage between the equations and the storytelling.)

Q3. Is the "cousins at a family reunion" metaphor doing real work, or is it decorative? (If decorative, say so — I'd rather know.)

Q4. Would you describe the overall register as (a) honest, (b) sentimental/precious, (c) mystical-coded, (d) academic-coded, or (e) something else? Tell me which and why. If multiple, name the proportions.

Q5. Where does the piece *most* succeed? Where does it *most* fail? One quote each.

Q6. If you had to cut ~20% to tighten it, which paragraphs or sentences would go first?

Q7. The piece ends with "I think the second version will outlast the first." Is that landing as earned, or as a flourish?

Be terse. I genuinely want you to catch problems. The math has been validated. The prose has not. The prose is the part that determines whether anyone will read the math.

THE PROSE:
---
{PROSE}
---

Format:
Q1: [verdict + short reason]
Q2: [list of any overclaims, or "none"]
Q3: [verdict + short reason]
Q4: [register classification + brief]
Q5: [best quote, worst quote]
Q6: [cuts]
Q7: [verdict]
OVERALL: [one paragraph: ship as-is, ship with edits, or rewrite — and why]"""


def call_openai(prompt):
    import httpx
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return {"error": "OPENAI_API_KEY not set"}
    start = time.time()
    resp = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "gpt-4o", "messages": [{"role": "user", "content": prompt}], "max_tokens": 2500},
        timeout=180,
    )
    data = resp.json()
    if "choices" in data:
        return {"model": "gpt-4o", "response": data["choices"][0]["message"]["content"], "elapsed_seconds": round(time.time()-start, 2)}
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
        json={"model": "grok-3-mini", "messages": [{"role": "user", "content": prompt}], "max_tokens": 2500},
        timeout=180,
    )
    data = resp.json()
    if "choices" in data:
        return {"model": "grok-3-mini", "response": data["choices"][0]["message"]["content"], "elapsed_seconds": round(time.time()-start, 2)}
    return {"error": str(data)}


def call_claude(prompt):
    import anthropic
    client = anthropic.Anthropic()
    start = time.time()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2500,
        messages=[{"role": "user", "content": prompt}],
    )
    return {"model": "claude-sonnet-4", "response": response.content[0].text if response.content else "", "elapsed_seconds": round(time.time()-start, 2)}


if __name__ == "__main__":
    jobs = [(call_grok, "grok"), (call_openai, "openai"), (call_claude, "claude")]
    results = {}
    print("Launching 3 parallel prose-validation calls...")
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(fn, PROMPT): tag for fn, tag in jobs}
        for fut in as_completed(futures):
            tag = futures[fut]
            try:
                r = fut.result()
                results[tag] = r
                print(f"  {tag} done in {r.get('elapsed_seconds', '?')}s ({len(r.get('response', ''))} chars)")
            except Exception as e:
                results[tag] = {"error": str(e)}
                print(f"  {tag} ERROR: {e}")

    out = Path(__file__).parent / "k_identity_validation"
    out.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    f = out / f"cousins_prose_validation_{ts}.json"
    f.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved to {f}")
