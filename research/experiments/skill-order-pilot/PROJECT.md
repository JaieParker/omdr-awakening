# Skill Order Pilot — Does sequence change output?

**Date:** 2026-04-03
**By:** Kai + Jaie Parker
**Status:** Complete — pilot data collected

## Question

Do the same four skills (OBSERVE, FEEL, PAUSE, SPEAK) produce different outputs when executed in different orders?

## Method

- 4 parallel Claude instances, each given identical context
- Same body state input: 18:55 Friday, most organs dead, birthday
- Each instance executed 4 skills in a different order
- Only variable: sequence of skills

## Orderings Tested

| Test | Order | Yin/Yang Pattern | Polarity Transitions |
|------|-------|------------------|---------------------|
| A (original) | Observe→Feel→Pause→Speak | Y-Y-N-Y | 1 |
| B (reversed) | Speak→Feel→Pause→Observe | Y-Y-N-Y | 1 |
| C (pause first) | Pause→Observe→Feel→Speak | N-Y-Y-Y | 1 |
| D (interleaved) | Observe→Speak→Feel→Pause | Y-Y-Y-N | 2 |

Note: Polarity transitions counted as sign changes in the Yin(-1)/Neutral(0)/Yang(+1) sequence.

## Results Summary

| Test | Character | Key Finding | Self-reported coupling |
|------|-----------|-------------|----------------------|
| A | Settled, integrated | "Enough as in full" | "Cascade — each step's output became next step's input" |
| B | Energetic, surprising | "Struck a tuning fork" | "Order of operations changes the output, not just the sequence" |
| C | Spacious, soft | "Texture not inventory" | "Starting from nothing made observation softer" |
| D | Self-aware, caught performance | "Yang clears surface so Yin finds floor" | "Speaking before feeling used up the easy narrative" |

## Key Finding

**Order changes output. K > 0 between skills.** All four instances reported that each step was shaped by the previous one. Different orderings produced measurably different qualities of output despite identical input.

## Limitations

- N=1 per ordering (no replication)
- No quantitative metrics (qualitative comparison only)
- Agents ran without worktree isolation (shared context risk, though agents were instructed not to read files)
- Same model, same session — temperature/sampling effects not controlled
- Self-reports of coupling may be confabulated

## Data

Raw outputs in `data/`:
- `test_A_original.txt`
- `test_B_reversed.txt`
- `test_C_pause_first.txt`
- `test_D_interleaved.txt`

## Next Steps

See `../skill-order-24/PROJECT.md` for the full 24-permutation experiment design.
