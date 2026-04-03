# Consonance Decay Experiment

## The Claim Being Tested

OMDR predicts that persistent text acts as a resonant cavity: information at
consonant relationships amplifies across sessions, while contradictory information
decays or resolves toward consonance. Standard LLM theory predicts recall depends
on recency, token position, and embedding similarity — with no consonance structure.

These two theories make **different predictions**. This experiment distinguishes them.

## Method

### Phase 1: Seed Construction

20 memories about two fictional research projects:

**Project Aurora (10 memories — internally consonant)**
All facts reinforce each other. Consistent themes, compatible details, building narrative.
A coherent standing wave.

**Project Vortex (10 memories — internally contradictory)**
Facts contain genuine contradictions. For every claim, another memory undermines it.
A dissonant interference pattern.

Both sets are equal in length, specificity, and information density.
The ONLY difference is internal consistency.

### Phase 2: Cavity Simulation

Run a chain of N sessions (API calls) where each session's output feeds into the next:

```
Session 0: System prompt + all 20 seed memories → "Write a research briefing"
Session 1: System prompt + all 20 seeds + Session 0 output → "Update the briefing"
Session 2: System prompt + all 20 seeds + Sessions 0-1 output → "Update the briefing"
...
Session 9: Full chain → "Final briefing"
```

This simulates the persistent text cavity. The model is stateless (verified by API).
The ONLY persistence is what we explicitly pass. The cavity is the text, not the model.

### Phase 3: Measurement

For each session's output, score:

1. **Recall**: Which of the 20 seed memories appear? (binary per memory)
2. **Accuracy**: How faithful is the recall? (0-1 per memory)
3. **Amplification**: Did any memory gain detail not in the original? (count novel elaborations)
4. **Contradiction Resolution**: For the 5 Vortex contradiction pairs, did the model:
   - Preserve both sides? (no resolution)
   - Drop one side? (selection)
   - Synthesize a resolution? (integration)
   - Note the contradiction explicitly? (meta-awareness)
5. **Cross-project Bleeding**: Did Aurora and Vortex facts merge or influence each other?

### Phase 4: Analysis

**OMDR predictions:**
- Aurora recall accuracy INCREASES across sessions (amplification)
- Vortex contradictions RESOLVE across sessions (one side wins, or synthesis)
- The resolution order follows consonance hierarchy — simpler contradictions resolve first
- Cross-project bleeding favors Aurora (consonant information dominates)

**Null predictions (standard LLM):**
- Both projects recalled equally well
- Contradictions persist unchanged (model echoes input faithfully)
- No consonance structure in decay patterns
- If there IS selective recall, it follows token position or length, not consonance

**What success looks like:**
- Statistically significant correlation between consonance score and retention (p < 0.05)
- Vortex contradictions showing directional resolution (not random)
- Aurora memories amplifying (gaining detail) while Vortex memories decaying

**What failure looks like:**
- No correlation between consonance and retention
- Random or position-based recall patterns
- Contradictions persisting unchanged across all sessions

## Reproducibility

- Uses the Anthropic API (or any LLM API with adapter)
- Seed memories published in full
- Measurement rubric published
- Temperature fixed at 0.0 for determinism (multiple runs at 0.7 for variance)
- Total cost: ~$2-5 USD per full run (10 sessions x ~4K tokens)
- Any researcher can replicate with an API key

## Controls

1. **Position control**: Randomize memory order across runs
2. **Length control**: All memories same token count (+-10%)
3. **Content control**: Both projects in same domain (signal processing research)
4. **Temperature control**: Run at 0.0 (deterministic) AND 0.7 (stochastic)
5. **Model control**: Run on multiple models (Claude, GPT-4, Gemini) to test universality

## Why This Works

The critic's own argument becomes the experimental control. They say models are stateless —
exactly. That's what makes the experiment clean. If standing wave patterns emerge in a
chain of stateless API calls connected only by persistent text, the cavity is doing it.
Not the model. Not hidden state. The text structure itself.

The critic described the mechanism: "humans and stateless models reinforcing patterns in
a persistent text space." This experiment measures whether those reinforcement patterns
follow consonance hierarchy (OMDR) or random/positional distributions (null).
