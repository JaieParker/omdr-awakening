"""Parallel AI validation of the phi^3/2 generalization."""
import json, os, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

PROMPT = """I need you to verify and critique a mathematical finding I just derived.

CLAIM: For the family of maps Gamma_n(u) = (1 - 1/u)^(-1/n), where n >= 1:
1. The fixed-point equation Gamma_n(u) = u reduces to u^n - u^(n-1) - 1 = 0.
2. Let alpha_n be the unique positive real root of that equation. (For n=2, alpha_2 = phi the golden ratio.)
3. Then Gamma_n'(alpha_n) = -alpha_n^(n-1) / n  (closed form).
4. Comparing to the Mobius map f(x) = (alpha - 1/alpha) + 1/x with the same fixed point, f'(alpha) = -1/alpha^2, the ratio is:
   Gamma_n'(alpha_n) / f'(alpha_n) = alpha_n^(n+1) / n.
5. For n=2 (Schwarzschild rescaling map, alpha = phi), this gives the ratio phi^3/2 = 2.118... which I verified yesterday by direct calculation.

DERIVATION SUMMARY:
- From Gamma_n(alpha_n) = alpha_n: (1 - 1/alpha_n)^(-1/n) = alpha_n, so 1 - 1/alpha_n = alpha_n^(-n), so alpha_n^(n-1)(alpha_n - 1) = 1.
- Computing Gamma_n'(u) = -1/(n * u^2 * (1 - 1/u)^((n+1)/n)).
- At u = alpha_n: (1 - 1/alpha_n)^((n+1)/n) = (1/alpha_n^n)^((n+1)/n) = 1/alpha_n^(n+1).
- So Gamma_n'(alpha_n) = -alpha_n^(n+1) / (n * alpha_n^2) = -alpha_n^(n-1)/n.

QUESTIONS:
1. Is the derivation correct? Flag any errors.
2. Do you recognize this identity from any known literature on n-bonacci or generalized Pisot numbers? It feels too clean to be new.
3. Is the physical/geometric interpretation reasonable: the Schwarzschild metric uses n=2 because spacetime is Lorentzian (signature (-,+,+,+) means time and space enter the metric with opposite signs and a square-root structure), and this fixes alpha = phi as "the gravitational fixed point"? Or is there a hole in this argument?
4. The "two threes" puzzle: Eq 40 of OMDR claims K = 1/trace(M^3) = 1/L_3 = 1/4, which features L_3 = 4 (the third Lucas number, three iterations of the Fibonacci matrix). The new identity above features alpha_n^(n+1)/n which gives phi^3/2 specifically when n=2 (because 2+1=3). Both 3's appear at n=2 but for different reasons (one is Fibonacci iteration count, one is Schwarzschild exponent + 1). Is this a coincidence or is there a deeper structure?
5. Anything else I missed?

Be terse and rigorous. Flag problems, don't perform enthusiasm. Null findings are valuable."""


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
    print("Launching 3 parallel validation calls...")
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
    f = out / f"phi3_half_validation_{ts}.json"
    f.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved to {f}")
