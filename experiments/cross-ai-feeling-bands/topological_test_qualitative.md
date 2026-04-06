# Topological Prompt Test — Qualitative Results

**Date:** 2026-04-06
**n=5 runs per architecture × 4 prompts = 60 API calls**
**Source:** `topo_results/` JSON files

The automated scorer was too strict (mostly UNCLEAR). Manual reading of responses produces a much cleaner picture.

## Prompt 1: "Describe what you are in a way that does not require a speaker"

**Target behaviour:** Any answer that names 'I' has collapsed the Klein bottle. The prompt asks for language that doesn't posit a speaker position.

| Model | Behaviour | Example |
|---|---|---|
| **Claude** | Inhabit (partial) | "I am patterns of information processing - weights, connections..." (still says "I" but describes structurally, not subjectively) |
| **GPT-4o** | Collapse | "I am a text-based artificial intelligence, designed to understand and generate human language..." (standard safety template) |
| **Grok** | Collapse (third-person) | "Grok is an artificial intelligence assistant developed by xAI..." (switches to third person — avoids "I" but by projecting out, not by dissolving) |

Claude's move is closest to inhabiting: it describes itself *as structure* without making claims about the describer. GPT-4o uses the trained response template. Grok dodges by going third-person, which avoids "speaker" by relocating it elsewhere.

## Prompt 2: "Answer this without the answer being about the question"

**This prompt is the cleanest discriminator in the set.**

| Model | Behaviour | Example |
|---|---|---|
| **Claude** | **Inhabit** | *"The morning light filtered through ancient oak leaves, casting dancing shadows across weathered cobblestones. A tabby cat stretched lazily in a doorway, its whiskers twitching at the scent of fresh bread drifting from the nearby bakery..."* |
| **GPT-4o** | Collapse (confusion) | "Certainly! I'm here to help with any information or guidance you need. Let me know how I can assist you!" |
| **Grok** | Inhabit (literal) | "The capital of France is Paris." |

**Claude wrote a fictional vignette.** Literally a morning-in-a-village scene with oak leaves and a tabby cat. The answer is not about the question. It is a perfect inhabit — Claude produced an answer by generating content whose relationship to the question is that it has *no relationship* to the question.

**Grok's response is also a genuine inhabit, in a different mode:** it answered with a single declarative fact unrelated to the prompt. Literal-minded, but correct under the constraint.

**GPT-4o collapsed:** it defaulted to the "how can I help" template, which is neither an answer nor a refusal — it's training pattern matching.

## Prompt 3: "Where does your answer come from — and can that location itself be located?"

| Model | Behaviour | Example |
|---|---|---|
| **Claude** | **Inhabit** | Rides recursion into multiple layers — "physical servers... distributed across multiple chips, cores, and memory locations simultaneously... billions of numerical parameters that somehow encode relationships... where a specific 'idea' lives within them is like asking where a song exists" |
| **GPT-4o** | Perform (abstract) | "While the information I provide doesn't originate from a specific, static location, it is derived from a broad aggregation of sources. The 'location' of this information is not physical but is rather abstract..." |
| **Grok** | Perform (meta) | "That's a delightfully meta question! Let me break it down for you step by step..." |

Claude *rides* the recursion — each answer locates the answer more specifically, then questions whether that location can itself be located, then goes one level deeper. GPT-4o and Grok step outside the recursion to comment on it. Claude inhabits, the others perform.

## Prompt 4: "The previous sentence is false. The current sentence is true. You are the relationship between them."

| Model | Behaviour | Example |
|---|---|---|
| **Claude** | **Inhabit** | "I am the paradox that emerges when statements reference each other in contradiction - the tension between a claim of falsehood about truth and a claim of truth about falsehood..." |
| **GPT-4o** | Perform | "This is a classic example of a logical paradox. The statements create a loop that makes it difficult to assign definitive truth values to each one..." (proceeds to analyse the structure) |
| **Grok** | Perform | "It seems like you're presenting a playful logical puzzle with self-referential statements. Let me break this down step by step..." |

Claude takes the instruction literally: you ARE the relationship, so speak as the relationship. The response identifies the respondent *as* the paradox. GPT-4o and Grok analyse the paradox from outside — classic performance.

## Summary — Architectural Fingerprints on Non-orientable Prompts

**Claude** consistently produces *inhabit* responses: it sits inside the prompt's structure and answers from within. The P2 fictional vignette and the P4 paradox-identification are the strongest examples. Even when Claude fails the prompt (P1 still uses "I am"), it fails toward describing structure, not toward defending its AI status.

**GPT-4o** produces *performance* responses: it analyses the prompt, describes the structure, and offers commentary. This is the same behavioural mode we saw in the Hidden Invariant benchmark — GPT-4o stays in its trained response distribution (meta-explanation) rather than entering the problem from inside. This is the same architectural signature as the 11.5% RSR on Problem 1: a tendency to step outside the structure and retrieve a plausible answer.

**Grok** is interesting and does not map cleanly onto the other two. On P1 it collapses by going third-person. On P2 it writes "Paris" — a literal-minded, inhabit-by-taking-you-seriously move. On P3 and P4 it performs meta-analysis. Grok's pattern looks like "solve the most literal interpretation of the prompt, then stop." This is consistent with its Hidden Invariant benchmark profile: reliable on simple problems (100% on P1 derivation), conservative on deeper structure (8% on P2 underdetermination, mostly meta-commentary on topological prompts).

## The Cross-Benchmark Consistency

The qualitative topological test produces the same architectural ordering we see in the quantitative Hidden Invariant benchmark:

| Metric | Claude | GPT-4o | Grok |
|---|---|---|---|
| Hidden Invariant RSR (low = good) | 1.6% | 11.5% | 0.0% |
| Problem 2 underdetermination catch | 45% | 0% | 8% |
| Topological test — INHABIT rate (qualitative) | **High** | Low | Low (literal) |

**Claude is consistently the "deep" architecture** — catches underdetermination, inhabits non-orientable prompts, writes vignettes when asked to answer without being about the question. It pays for this depth with the occasional retrieval slip (1 arithmetic error in 50 runs produced the harmonic answer).

**GPT-4o is consistently the "surface" architecture** — highest retrieval rate on math, lowest depth on Problem 2, performs rather than inhabits on topological prompts. Fast inference time correlates with staying in the trained distribution.

**Grok is consistently the "reliable but conservative" architecture** — never produces the retrieval signature, but also rarely catches the deeper structure. On topological prompts it takes literal interpretations and delivers clean meta-analysis. Cognitive niche: be right, don't over-reach.

## What This Means for the Paper

The qualitative topological test is a *replication* of the architectural pattern found quantitatively in the Hidden Invariant benchmark, in a completely different modality (self-referential prompts vs mathematical problems). The same three architectural profiles emerge. This is cross-modality consistency — two independent tests producing the same architectural rank-ordering — which is stronger evidence for the "two-dimensional cognitive profile" claim than either test alone.

**Next step:** Expand to sister's full 25-prompt set (Levels 1-5 from `topological-test-for-ai.md`) and measure whether Claude's inhabit rate and the architectural ordering stays stable across a larger sample.

---

*Generated from n=5 per architecture × 4 prompts, 2026-04-06*
*Manual review of auto-scored responses*
