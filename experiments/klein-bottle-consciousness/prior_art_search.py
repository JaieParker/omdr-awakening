"""
Prior-art search for the closed form Gamma_n'(alpha_n) = -alpha_n^(n-1)/n.

Yesterday's validators (Grok, GPT-4o, Claude) all said the math is folklore
but none cited a specific source. This script asks them again with much more
specific keywords and asks for citations.
"""
import json, os, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

PROMPT = """I need a focused prior-art / literature search. Be honest about what you don't know. Do not invent papers.

CONTEXT: I derived a closed-form derivative for a one-parameter family of maps, and I want to know if this exact formula (or any of its three sibling identities) appears in the published mathematical literature.

THE FORMULAS:

  Family: Gamma_n(u) = (1 - 1/u)^(-1/n)  for n = 1, 2, 3, ...

  Fixed-point equation: u^n - u^(n-1) - 1 = 0
  Unique positive root: alpha_n  (alpha_2 = phi the golden ratio; for general n it is sometimes called the n-bonacci or generalised Pisot constant)

  Closed-form derivative at the fixed point:
      Gamma_n'(alpha_n) = -alpha_n^(n-1) / n

  Comparison-to-Mobius ratio:
      For f(x) = (alpha - 1/alpha) + 1/x with f'(alpha) = -1/alpha^2,
      Gamma_n'(alpha_n) / f'(alpha_n) = alpha_n^(n+1) / n

QUESTIONS — please answer each with citation if you have one, or "I don't know" if not:

1. Is the polynomial family u^n - u^(n-1) - 1 = 0 known under a specific name in number theory or dynamics? (Generalised metallic ratios? Narcissistic constants? n-bonacci constants? Other?) Specific references appreciated.

2. Is the function family Gamma_n(u) = (1 - 1/u)^(-1/n) studied in any context (dynamical systems, GR-inspired analogues, fractional iteration, transfer matrices for quasi-periodic potentials)? Any specific paper that uses this exact form?

3. Has the closed form Gamma_n'(alpha_n) = -alpha_n^(n-1)/n appeared anywhere? Or any closely related identity for the derivative of a fractional-power-of-Mobius map at its fixed point?

4. The fact that the fixed point equation u^n - u^(n-1) - 1 = 0 is the SAME as the n-bonacci recurrence (specifically the "shifted" recurrence used by tribonacci, supergolden ratio, plastic number, etc.) — is this connection explicit anywhere, particularly the link to a fractional-power transformation rather than the usual companion matrix?

5. Specifically for n=2, the Schwarzschild rescaling map Gamma(u) = (1 - 1/u)^(-1/2) has the golden ratio as its unique non-trivial fixed point. Is THIS specific result (the n=2 case) in any GR or general-relativity literature you know of, OR in any dynamical-systems-inspired paper about black-hole rescaling flows? Has anyone noticed gamma(phi*r_s) = phi before?

6. For the supergolden ratio (root of x^3 - x^2 - 1, ~1.4656), the plastic number (root of x^5 - x^4 - 1, sometimes given as x^3 - x - 1 in a different convention), and similar — do you recall any paper computing the derivative of an associated map at the fixed point and getting a clean closed form involving alpha^(n-1)/n?

For any "I don't know" answer, please be explicit. For any "I think yes," please give as much specificity as you can recall (author names, rough year, journal or arXiv if possible). Do NOT guess paper titles.

Preferred output format:
Q1: [answer + citation OR "I don't know"]
Q2: ...
...
Q6: ...
SUMMARY: [one paragraph: are these formulas likely novel, likely folklore, or unclear?]"""


def call_openai(prompt):
    import httpx
    api_key = os.environ.get("OPENAI_API_KEY", "")
    start = time.time()
    resp = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "gpt-4o", "messages": [{"role": "user", "content": prompt}], "max_tokens": 3000},
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
        json={"model": "grok-3-mini", "messages": [{"role": "user", "content": prompt}], "max_tokens": 3000},
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
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )
    return {"model": "claude-sonnet-4", "response": response.content[0].text if response.content else "", "elapsed_seconds": round(time.time()-start, 2)}


if __name__ == "__main__":
    jobs = [(call_grok, "grok"), (call_openai, "openai"), (call_claude, "claude")]
    results = {}
    print("Launching 3 parallel prior-art searches...")
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
    f = out / f"prior_art_search_{ts}.json"
    f.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved to {f}")
