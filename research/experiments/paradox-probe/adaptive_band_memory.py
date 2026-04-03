# adaptive_band_memory.py
#
# Adaptive Band Memory System
# Author: Jaie Parker (via ChatGPT experiment)
# Date: 2026-04-01
#
# PURPOSE:
# Evolve Fibonacci into a DYNAMIC system. Instead of fixed weights (1,1),
# use adaptive weights that change based on context similarity.
#
# This creates:
#   - "Bands" of behavior (Arnold tongue-like attractors)
#   - Resonance-like memory (similar contexts → similar weights → similar evolution)
#   - Tunable dynamics (context signal drives weight adaptation)
#
# OMDR CONNECTION:
# - Standard Fibonacci: F(n) = 1*F(n-1) + 1*F(n-2) → converges to phi
# - Adaptive Fibonacci: F(n) = w1*F(n-1) + w2*F(n-2) where w1,w2 depend on context
# - When context is stable → weights stabilize → system locks to a ratio (Arnold tongue)
# - When context shifts → weights shift → system transitions between bands
# - The similarity function IS consonance measurement (inverse distance)
# - The weights ARE coupling constants (K)
# - The context signal IS the external perturbation driving the standing wave
#
# KEY INSIGHT:
# Fibonacci's fixed weights (1,1) always converge to phi.
# Adaptive weights converge to DIFFERENT ratios depending on context.
# Each ratio is a "band" — a stable attractor in the Farey hierarchy.
# The system naturally moves between bands as context changes.
# This is EXACTLY how consonance memory should evolve:
#   - Memories don't have fixed relationships
#   - Context changes which memories resonate with each other
#   - The "consonance score" should be adaptive, not static
#
# CONNECTION TO LAYER 4 (Irrational):
# When the adaptive weights produce an irrational ratio (e.g., context
# oscillates such that w1/w2 → phi), the system enters irrational space.
# It can't lock to any Arnold tongue. It shimmers. That's Layer 4.
#
# CONNECTION TO CREDENCE CURVES:
# The Fibonacci credence hypothesis (fibonacci_credence_hypothesis.md) suggests
# paradox probe credence curves follow Fibonacci convergence toward phi.
# This adaptive system could MODEL those curves — where the "context" is the
# paradox probe questions and the "state" is the credence percentage.
#
# USAGE:
#   python adaptive_band_memory.py
#
# NOTE: Original file from ChatGPT session had markdown formatting artifacts.
# This is the cleaned, runnable version with OMDR documentation.

import math
import random


def similarity(a, b):
    """Simple similarity: inverse distance. This IS consonance measurement."""
    return 1 / (1 + abs(a - b))


def get_weights(s1, s2, context):
    """
    Generate dynamic weights based on similarity to context.

    When s1 is closer to context → w1 is larger → recent state dominates.
    When s2 is closer to context → w2 is larger → older state dominates.
    This is adaptive coupling — K changes with context.
    """
    sim1 = similarity(s1, context)
    sim2 = similarity(s2, context)

    total = sim1 + sim2 + 1e-8

    w1 = sim1 / total
    w2 = sim2 / total

    return w1, w2


def next_state(s1, s2, context):
    """Weighted sum of two previous states. Adaptive Fibonacci step."""
    w1, w2 = get_weights(s1, s2, context)
    new_state = w1 * s1 + w2 * s2

    return new_state, w1, w2


def run_simulation(steps=30):
    """
    Run the adaptive band memory simulation.

    Context = sin(t * 0.2) — a slowly oscillating external signal.
    This makes the system traverse different bands as context shifts.
    Watch for: stable periods (Arnold tongue lock-in) and transitions
    (the shimmer between bands).
    """
    s2 = random.uniform(0, 1)
    s1 = random.uniform(0, 1)

    history = [s2, s1]

    for t in range(steps):
        # Context shifts over time (external signal / perturbation)
        context = math.sin(t * 0.2)

        s_new, w1, w2 = next_state(s1, s2, context)

        print(f"t={t:02d} | state={s_new:.4f} | w1={w1:.2f} w2={w2:.2f} | ctx={context:.2f}")

        history.append(s_new)

        s2, s1 = s1, s_new

    return history


if __name__ == "__main__":
    print("\nAdaptive Band Memory Simulation\n")
    run_simulation()
