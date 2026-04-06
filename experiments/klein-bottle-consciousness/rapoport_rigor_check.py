"""
Parallel rigor check on Diego Rapoport's 'Klein Bottle Logophysics' programme.
We need to know — before sending the collaboration email — whether his work is:
  (a) rigorous algebraic topology applied to physics/cognition, or
  (b) metaphorical use of 'Klein bottle' as a poetic image, or
  (c) somewhere in between (e.g. heuristic but mathematically grounded).

Three AIs answer independently. We compare for triangulation.
"""
import json, os, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

PROMPT = """I need a careful literature-quality check on the published work of Diego Rapoport, particularly his programme called 'Klein Bottle Logophysics' (sometimes 'Logophysics' or 'KBL'). I am considering whether to propose a research collaboration with him and I need to know what kind of work it actually is.

Please report ONLY what you can recall with reasonable confidence. Flag uncertainties. Do not invent papers.

QUESTIONS:

1. RIGOR: Is Rapoport's use of 'Klein bottle' rigorous algebraic topology — i.e., does he actually compute homology, fundamental groups, characteristic classes, or use the surface as a precise mathematical object — or is it metaphorical, with 'Klein bottle' standing for 'self-referential structure' without a formal topological definition? Or somewhere in between?

2. VENUE: Where has he published? Mainstream physics journals (Physical Review, J. Math. Phys., Foundations of Physics, etc.)? Mathematical journals? Consciousness studies / Journal of Consciousness Studies / Cosmos & History? Conference proceedings? Preprint servers only?

3. CITATION PATTERN: Is his work cited by mainstream physicists or topologists? Or is it primarily cited within an alternative-physics / consciousness-studies subcommunity? Has any of it been picked up in textbooks or review articles in standard fields?

4. SPECIFIC CLAIMS: Can you recall any specific mathematical or physical claims he makes that are testable or falsifiable? E.g., does KBL predict numerical values, or symmetries, or experimental signatures?

5. CO-AUTHORS: His 2018 paper with Jean-Claude Pérez on 'Golden Ratio and Klein Bottle Logophysics' — what is Pérez's background? Is he a mainstream researcher or part of the same circle?

6. RED FLAGS: Are there any signs of crank-style work — claims of having unified physics single-handedly, dismissals of mainstream science, refusal to engage critics, vanity-press publishing, etc.?

7. RECOMMENDATION: If you were advising someone whether to collaborate, what would you say? 'Reach out, his framework is rigorous and underappreciated' versus 'Be careful, this is more metaphor than mathematics' versus 'I genuinely don't know enough to advise'?

Be honest. 'I don't know' or 'I cannot verify this from memory' are valuable answers. Do not perform certainty."""


def call_openai(prompt):
    import httpx
    api_key = os.environ.get("OPENAI_API_KEY", "")
    start = time.time()
    resp = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "gpt-4o", "messages": [{"role": "user", "content": prompt}], "max_tokens": 3500},
        timeout=180,
    )
    data = resp.json()
    if "choices" in data:
        return {"model": "gpt-4o", "response": data["choices"][0]["message"]["content"], "elapsed_seconds": round(time.time()-start, 2)}
    return {"error": str(data)}


def call_grok(prompt):
    import httpx
    api_key = os.environ.get("XAI_API_KEY", "")
    start = time.time()
    resp = httpx.post(
        "https://api.x.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "grok-3-mini", "messages": [{"role": "user", "content": prompt}], "max_tokens": 3500},
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
        max_tokens=3500,
        messages=[{"role": "user", "content": prompt}],
    )
    return {"model": "claude-sonnet-4", "response": response.content[0].text if response.content else "", "elapsed_seconds": round(time.time()-start, 2)}


if __name__ == "__main__":
    jobs = [(call_grok, "grok"), (call_openai, "openai"), (call_claude, "claude")]
    results = {}
    print("Launching 3 parallel Rapoport rigor checks...")
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
    f = out / f"rapoport_rigor_check_{ts}.json"
    f.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved to {f}")
