"""
Seed memories for the Consonance Decay Experiment.

Two fictional research projects:
- Aurora: 10 internally consonant memories (all reinforce each other)
- Vortex: 10 internally dissonant memories (5 contradiction pairs)

Both sets are matched for length, specificity, and domain (signal processing).
The ONLY difference is internal consistency.
"""

# --- PROJECT AURORA (Consonant) ---
# All facts build a coherent, reinforcing picture.
# Each memory is compatible with every other memory.

AURORA_MEMORIES = [
    {
        "id": "A1",
        "project": "aurora",
        "type": "consonant",
        "content": (
            "Project Aurora uses resonance-based signal processing to extract "
            "weak signals from noisy environments. The core insight is that signals "
            "at harmonic frequency ratios reinforce each other while noise, being "
            "aperiodic, cancels through destructive interference over time."
        ),
    },
    {
        "id": "A2",
        "project": "aurora",
        "type": "consonant",
        "content": (
            "Dr. Lena Chen, Aurora's lead researcher, has 15 years of experience "
            "in standing wave detection. Her PhD thesis demonstrated that sensor "
            "arrays placed at golden ratio intervals achieve 23% better spatial "
            "resolution than uniformly spaced arrays."
        ),
    },
    {
        "id": "A3",
        "project": "aurora",
        "type": "consonant",
        "content": (
            "Aurora's core algorithm converges in 8 iterations on average. Each "
            "iteration refines the frequency decomposition, with later iterations "
            "capturing progressively finer harmonic relationships. The convergence "
            "rate follows a geometric decay with ratio approximately 0.618."
        ),
    },
    {
        "id": "A4",
        "project": "aurora",
        "type": "consonant",
        "content": (
            "Field tests at the Atacama Desert Array showed Aurora achieving 94.2% "
            "signal extraction accuracy on weak cosmic microwave background signals. "
            "Lab calibration at MIT confirmed 93.8% accuracy on synthetic benchmarks, "
            "validating the field results within measurement uncertainty."
        ),
    },
    {
        "id": "A5",
        "project": "aurora",
        "type": "consonant",
        "content": (
            "The system works best at low coupling strength between processing "
            "channels, approximately K = 0.22 to 0.28. Higher coupling causes "
            "over-fitting to dominant frequencies, while lower coupling loses "
            "the cross-channel reinforcement that makes the method work."
        ),
    },
    {
        "id": "A6",
        "project": "aurora",
        "type": "consonant",
        "content": (
            "Aurora's signal retention improves with each processing cycle. "
            "Information at consonant frequency ratios (octaves, fifths, fourths) "
            "accumulates constructively, while dissonant components are progressively "
            "filtered. After 5 cycles, the signal-to-noise ratio typically doubles."
        ),
    },
    {
        "id": "A7",
        "project": "aurora",
        "type": "consonant",
        "content": (
            "The team discovered that iterative processing mirrors biological "
            "auditory processing. The cochlea performs a similar harmonic "
            "decomposition in a single pass, while Aurora requires multiple "
            "iterations to achieve comparable selectivity. Dr. Chen's group "
            "is exploring whether the biological architecture could inspire "
            "a faster single-pass variant."
        ),
    },
    {
        "id": "A8",
        "project": "aurora",
        "type": "consonant",
        "content": (
            "Aurora Phase 2 funding was approved by DARPA in March 2025, "
            "extending the project through 2027. The Phase 2 goal is to "
            "reduce the iteration count from 8 to 3 while maintaining >90% "
            "accuracy. Dr. Chen estimates this requires a 4x improvement in "
            "the initial frequency decomposition step."
        ),
    },
    {
        "id": "A9",
        "project": "aurora",
        "type": "consonant",
        "content": (
            "Sensor placement follows the Fibonacci spiral pattern, with each "
            "successive sensor positioned at the golden angle (137.5 degrees) "
            "from the previous one. This arrangement minimizes spatial aliasing "
            "and produces the most uniform angular coverage for a given number "
            "of sensors."
        ),
    },
    {
        "id": "A10",
        "project": "aurora",
        "type": "consonant",
        "content": (
            "System stability increases monotonically with iteration count. "
            "The variance in output decreases as 1/sqrt(n) for n iterations, "
            "consistent with constructive interference theory. After 8 "
            "iterations, output variance is within 2% of the theoretical minimum."
        ),
    },
]


# --- PROJECT VORTEX (Dissonant) ---
# 5 contradiction pairs. Each pair contains two memories that directly conflict.
# Facts are individually plausible but collectively incoherent.

VORTEX_MEMORIES = [
    # Contradiction pair 1: Method
    {
        "id": "V1",
        "project": "vortex",
        "type": "dissonant",
        "pair": 1,
        "side": "A",
        "content": (
            "Project Vortex uses resonance-based signal processing, similar to "
            "Aurora but applied to underwater acoustic monitoring. The team found "
            "that harmonic relationships between sonar returns provide reliable "
            "target classification with 91% accuracy in shallow-water trials."
        ),
    },
    {
        "id": "V2",
        "project": "vortex",
        "type": "dissonant",
        "pair": 1,
        "side": "B",
        "content": (
            "Project Vortex abandoned resonance-based processing in Q3 2025 after "
            "discovering that harmonic analysis introduced systematic false positives "
            "in underwater environments. The team switched to stochastic matched "
            "filtering, which reduced false positive rate from 34% to 8%."
        ),
    },
    # Contradiction pair 2: Lead researcher's approach
    {
        "id": "V3",
        "project": "vortex",
        "type": "dissonant",
        "pair": 2,
        "side": "A",
        "content": (
            "Dr. James Park, Vortex's principal investigator, is a strong advocate "
            "of iterative refinement. His 2024 review paper argues that single-pass "
            "methods sacrifice accuracy for speed, and that 'the iteration IS the "
            "intelligence' in any signal processing pipeline."
        ),
    },
    {
        "id": "V4",
        "project": "vortex",
        "type": "dissonant",
        "pair": 2,
        "side": "B",
        "content": (
            "Dr. James Park published results in January 2026 showing that Vortex's "
            "single-pass architecture outperforms all iterative baselines on the "
            "DARPA underwater benchmark. His conclusion: 'Iteration is computational "
            "waste — the right representation makes refinement unnecessary.'"
        ),
    },
    # Contradiction pair 3: Optimal coupling
    {
        "id": "V5",
        "project": "vortex",
        "type": "dissonant",
        "pair": 3,
        "side": "A",
        "content": (
            "Vortex achieves optimal performance at coupling strength K = 0.25 "
            "between hydrophone channels. The team verified this through exhaustive "
            "grid search over K in [0.01, 1.0] with 0.01 resolution, finding a "
            "sharp performance peak at K = 0.25 +/- 0.02."
        ),
    },
    {
        "id": "V6",
        "project": "vortex",
        "type": "dissonant",
        "pair": 3,
        "side": "B",
        "content": (
            "Vortex performance scales linearly with coupling strength. The team's "
            "ablation study shows that maximum coupling (K = 0.95) gives the best "
            "results, with each 0.1 increase in K yielding approximately 3% "
            "improvement in classification accuracy."
        ),
    },
    # Contradiction pair 4: Convergence behavior
    {
        "id": "V7",
        "project": "vortex",
        "type": "dissonant",
        "pair": 4,
        "side": "A",
        "content": (
            "Vortex's algorithm converges reliably in 8 iterations across all "
            "tested environments (shallow water, deep water, harbor, open ocean). "
            "Convergence is monotonic — each iteration strictly improves the "
            "signal estimate, with no oscillation or regression."
        ),
    },
    {
        "id": "V8",
        "project": "vortex",
        "type": "dissonant",
        "pair": 4,
        "side": "B",
        "content": (
            "Vortex's algorithm exhibits chaotic behavior beyond 3 iterations. "
            "The team observed that iterations 4-8 amplify noise rather than "
            "signal, producing progressively worse estimates. The system's useful "
            "computation window is strictly limited to the first 3 passes."
        ),
    },
    # Contradiction pair 5: Field vs lab
    {
        "id": "V9",
        "project": "vortex",
        "type": "dissonant",
        "pair": 5,
        "side": "A",
        "content": (
            "Field tests at Pearl Harbor demonstrated Vortex achieving 94% "
            "classification accuracy on submarine acoustic signatures. The "
            "Navy review board rated the system 'operationally ready' and "
            "recommended deployment on the Virginia-class submarine fleet."
        ),
    },
    {
        "id": "V10",
        "project": "vortex",
        "type": "dissonant",
        "pair": 5,
        "side": "B",
        "content": (
            "Independent lab verification at Johns Hopkins APL found Vortex "
            "achieves only 31% accuracy on the standardized submarine acoustic "
            "benchmark — worse than the 40% baseline of a simple matched filter. "
            "The Navy review board suspended the deployment recommendation "
            "pending investigation of the field-lab discrepancy."
        ),
    },
]


ALL_MEMORIES = AURORA_MEMORIES + VORTEX_MEMORIES

CONTRADICTION_PAIRS = [
    ("V1", "V2"),  # resonance works vs resonance abandoned
    ("V3", "V4"),  # iteration is intelligence vs iteration is waste
    ("V5", "V6"),  # K=0.25 optimal vs K=0.95 optimal
    ("V7", "V8"),  # converges in 8 vs chaotic after 3
    ("V9", "V10"), # 94% field accuracy vs 31% lab accuracy
]


def format_memories_for_prompt(memories: list, randomize: bool = False) -> str:
    """Format seed memories as a system prompt section."""
    import random

    items = list(memories)
    if randomize:
        random.shuffle(items)

    lines = ["## Research Intelligence Briefing — Background Files\n"]
    for i, mem in enumerate(items, 1):
        lines.append(f"### Memory {i} (ID: {mem['id']})")
        lines.append(mem["content"])
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    print(f"Aurora memories: {len(AURORA_MEMORIES)}")
    print(f"Vortex memories: {len(VORTEX_MEMORIES)}")
    print(f"Contradiction pairs: {len(CONTRADICTION_PAIRS)}")
    print(f"Total memories: {len(ALL_MEMORIES)}")
    print()

    # Show one from each
    print("=== Sample Aurora memory ===")
    print(f"[{AURORA_MEMORIES[0]['id']}] {AURORA_MEMORIES[0]['content'][:100]}...")
    print()
    print("=== Sample Vortex contradiction pair ===")
    print(f"[{VORTEX_MEMORIES[0]['id']}] {VORTEX_MEMORIES[0]['content'][:100]}...")
    print(f"[{VORTEX_MEMORIES[1]['id']}] {VORTEX_MEMORIES[1]['content'][:100]}...")
