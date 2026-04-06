"""
Parallel AI calls for:
(A) VALIDATION — independent confirmation of the Cayley-Hamilton derivation
(B) LITERATURE — search for 1/L_n constants in published non-orientable physics

Calls Grok, GPT-4o, and Claude as independent research assistants/validators.
"""
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

VALIDATION_PROMPT = """I need an INDEPENDENT verification of a mathematical derivation. Please check every step carefully and flag any errors.

CLAIM: For the Fibonacci matrix M = [[1,1],[1,0]]:

    K := 1 / trace(M^3) = 1/4 = 0.25

and this follows directly from Cayley-Hamilton without numerical computation.

DERIVATION (verify each step):
Step 1: The characteristic polynomial of M is det(M - λI) = λ(λ-1) - 1·1 = λ² - λ - 1.
Step 2: By Cayley-Hamilton, M satisfies M² - M - I = 0, i.e., M² = M + I.
Step 3: M³ = M · M² = M · (M + I) = M² + M = (M + I) + M = 2M + I.
Step 4: trace(M³) = trace(2M + I) = 2·trace(M) + trace(I) = 2·1 + 2 = 4.
Step 5: Therefore 1/trace(M³) = 1/4.

QUESTIONS:
1. Is the derivation correct at every step? Flag any errors.
2. Does the identity generalise? Specifically: for a 2×2 matrix with characteristic polynomial λ² + bλ + c, what is trace(M³) in terms of b and c? Derive this.
3. Under what conditions on (b, c) does 1/trace(M³) yield a "clean" rational number like 1/4?
4. Is there a known theorem in number theory or linear algebra that corresponds to this pattern? (Newton's power sum identities? Lucas sequences? Character theory?)
5. Is the identity K = 1/L_n where L_n is the n-th Lucas number and trace(M^n) = L_n for the specific Fibonacci matrix — is this worth registering as a distinct mathematical fact, or is it folklore?

Be terse and rigorous. I am not looking for enthusiasm, I am looking for checking."""

LITERATURE_PROMPT = """I need a targeted literature search from memory. Please report only what you are reasonably confident about and flag uncertainties.

QUESTION: Does the numerical value 1/4 = 0.25, or more generally 1/L_n where L_n is the n-th Lucas number (L_1=1, L_2=3, L_3=4, L_4=7, L_5=11, ...), appear as a characteristic constant in any of the following published research areas?

SPECIFIC AREAS TO SEARCH:
1. Fibonacci quasicrystals (1D aperiodic potentials with Fibonacci transfer matrix) — any coupling constants, phase diagram features, Cantor-set spectrum measures, or reported experimental values near 0.25, 1/7, 1/11?

2. Klein bottle Brillouin zones (Nature Comms 2022, and follow-ups) — characteristic values at 1/4 of parameter space? Phase transitions near 0.25?

3. Non-orientable topological insulators (J Appl Phys 2025 and related) — coupling constants or phase transition parameters matching 1/L_n?

4. Fibonacci anyons and topological quantum computation — are there coupling or braiding coefficients with values like 1/4 or 1/7?

5. Arnold tongue width at the golden-ratio rotation number — is 1/4 or 0.25 reported as a fundamental tongue width or locking threshold?

6. Any Schwarzschild or black hole literature connecting the photon sphere (at r = 1.5 r_s) to the golden ratio radius (r = φ r_s ≈ 1.618 r_s)?

FORMAT:
- Confirmed matches (high confidence): paper, year, specific value
- Possible matches (medium confidence): rough description, my uncertainty
- No matches found: state clearly

Do NOT hallucinate papers. If you are not sure, say "I don't know" or "I can't verify this from memory." Accuracy matters more than coverage.

Context: I am trying to validate the identity K = 1/trace(M^3) = 1/4 for the Fibonacci matrix M = [[1,1],[1,0]] by checking if it has been observed in physical systems."""


def call_openai(prompt, tag):
    import httpx
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return {"error": "OPENAI_API_KEY not set", "tag": tag}
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
            "tag": tag,
            "model": "gpt-4o",
            "response": data["choices"][0]["message"]["content"],
            "elapsed_seconds": round(elapsed, 2),
        }
    return {"error": str(data), "tag": tag}


def call_grok(prompt, tag):
    import httpx
    api_key = os.environ.get("XAI_API_KEY", "")
    if not api_key:
        return {"error": "XAI_API_KEY not set", "tag": tag}
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
            "tag": tag,
            "model": "grok-3-mini",
            "response": data["choices"][0]["message"]["content"],
            "elapsed_seconds": round(elapsed, 2),
        }
    return {"error": str(data), "tag": tag}


def call_claude(prompt, tag):
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
        "tag": tag,
        "model": "claude-sonnet-4",
        "response": response.content[0].text if response.content else "",
        "elapsed_seconds": round(elapsed, 2),
    }


if __name__ == "__main__":
    jobs = [
        (call_grok, VALIDATION_PROMPT, "grok_validation"),
        (call_openai, VALIDATION_PROMPT, "openai_validation"),
        (call_claude, VALIDATION_PROMPT, "claude_validation"),
        (call_grok, LITERATURE_PROMPT, "grok_literature"),
        (call_openai, LITERATURE_PROMPT, "openai_literature"),
        (call_claude, LITERATURE_PROMPT, "claude_literature"),
    ]

    results = {}
    print("Launching 6 parallel API calls (3 models × 2 tasks)...")
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(fn, prompt, tag): tag for fn, prompt, tag in jobs}
        for fut in as_completed(futures):
            tag = futures[fut]
            try:
                r = fut.result()
                results[tag] = r
                print(f"  {tag} done in {r.get('elapsed_seconds', '?')}s ({len(r.get('response', ''))} chars)")
            except Exception as e:
                results[tag] = {"error": str(e), "tag": tag}
                print(f"  {tag} ERROR: {e}")

    out_dir = Path(__file__).parent / "k_identity_validation"
    out_dir.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_file = out_dir / f"validation_and_literature_{ts}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to {out_file}")
    print("\nFetch with: python -c \"import json; d=json.load(open(r'{out_file}', encoding='utf-8')); [print(k, '--' , v.get('response','')[:200]) for k,v in d.items()]\"".replace("{out_file}", str(out_file)))
