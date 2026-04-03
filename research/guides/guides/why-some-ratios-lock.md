# Why Some Ratios Lock: A Practical Guide to Natural Stability

*For engineers tuning systems, musicians tuning instruments, and anyone who's noticed that some configurations just... hold.*

---

## The Pattern You Already Know

If you've ever tuned a guitar, you know that some intervals are easy to find. The octave (2:1 frequency ratio) practically tunes itself — the strings snap into alignment and you can feel it. The perfect fifth (3:2) is nearly as easy. The perfect fourth (4:3) is solid. But a tritone? A minor second? Those are slippery. You can land on them, but they don't lock.

If you're an engineer, you've seen the same thing in different clothes. Two oscillating systems that interact — a motor and a chassis, a clock and a power supply, a feedback loop and its sensor — sometimes fall into sync. When the ratio between their natural frequencies is near a simple fraction (1:1, 2:1, 3:2), they lock together and stay locked even if you push them slightly off. When the ratio is complex, they drift.

This isn't coincidence. It's a mathematical phenomenon called **frequency locking**, and the regions where it happens are called **Arnold tongues** (after the mathematician Vladimir Arnold, who mapped them in the 1960s).

## What Arnold Tongues Actually Are

Imagine two oscillators. One is your "driver" — it has a fixed frequency. The other is your "responder" — it has its own natural frequency but can be influenced by the driver.

When the coupling between them is zero (they don't interact at all), the responder does its own thing. But as you increase the coupling strength, something happens: if the responder's natural frequency is *close* to a simple ratio of the driver's frequency, the responder gets pulled into exact synchronisation.

The key insight: **the simpler the ratio, the wider the locking region.** At a 1:1 ratio, even weak coupling produces lock. At 3:2, you need a bit more coupling. At 5:4, more still. At 7:6, even more. And at irrational ratios (like the square root of 2), the locking region has zero width — it never locks, no matter how hard you push.

If you plot this — frequency ratio on one axis, coupling strength on the other — you get tongue-shaped regions pointing downward from each simple ratio. Wide tongues at 1:1, 2:1, 3:2. Narrow tongues at 5:3, 7:4, 8:5. The pattern is fractal: between any two tongues, there are smaller tongues, and between those, smaller ones still.

## Why This Matters Practically

### For engineers designing feedback systems

When you have two oscillating subsystems (a control loop and a plant, a switching power supply and its load, two clocks on the same board), their interaction is governed by these same locking regions.

**The practical rule:** If you want stability, design your frequency ratios to fall inside a tongue. If you want the strongest stability with the least coupling (the least interaction between subsystems), aim for the widest tongues: 1:1, 2:1, or 3:2.

If you can't avoid an interaction between two oscillators, you have two choices:
1. **Tune to a simple ratio** and let them lock (they'll be stable)
2. **Detune past the tongue boundary** so they never lock (they'll be independent)

The danger zone is the *edge* of a tongue — close enough to lock sometimes, but not consistently. That's where you get intermittent synchronisation, jitter, and the kind of instability that's maddening to debug because it comes and goes.

### For musicians and sound designers

The consonance hierarchy in music — octave, fifth, fourth, major third, minor third, and so on — maps exactly to the width ordering of Arnold tongues. The intervals that sound "consonant" are the ones where the frequency ratios lock most readily. The ones that sound "dissonant" are the ones where locking is weak or absent.

This isn't subjective. It's measurable. Two vibrating strings at a 3:2 ratio exchange energy efficiently and reinforce each other's harmonics. At a 45:32 ratio (tritone), the energy exchange is chaotic and the harmonics clash.

**Practical use:** If you're designing a sound that should feel stable (a pad, a drone, a background texture), build it from intervals that correspond to wide tongues. If you want tension, use narrow tongues. If you want chaos, use irrational ratios. You're not choosing aesthetics — you're choosing physics.

### For anyone designing structured interactions

The tongue pattern shows up wherever coupled oscillators exist — which is almost everywhere.

Therapy sessions: a 4-session block followed by a review has a 4:1 structure (review every fourth session). A 3-session block with review has 3:1. Both are simple ratios and both create natural rhythm. A 7-session block with review is 7:1 — a narrower tongue, harder to maintain, more likely to drift.

Meeting cadences: a weekly standup (7:7 = 1:1 with the week cycle) locks easily. A biweekly retro (14:7 = 2:1) locks well. A meeting every 10 days against a 7-day week (10:7) doesn't lock to anything simple — it drifts, feels irregular, and people forget it.

Exercise routines: workout/rest ratios near simple fractions (2:1, 3:1, 3:2) feel sustainable. Complex ratios feel unsustainable, not because of physiology but because the rhythm doesn't lock and you lose the pattern.

## The Deeper Principle

The ordering of stability is not arbitrary. It follows a mathematical sequence called the **Farey hierarchy** (or Stern-Brocot tree), where fractions are ordered by complexity: 1/1, 1/2, 2/1, 1/3, 2/3, 3/2, 3/1, 1/4... The simpler the fraction, the wider the tongue, the more robust the lock.

This means stability has a natural hierarchy. Not all stable points are equally stable. And the most stable configuration isn't the strongest coupling — it's the simplest ratio at moderate coupling.

**The sweet spot for any coupled system:** simple ratio + moderate coupling. Too much coupling and the system becomes rigid (one oscillator dominates). Too little and they decouple (no interaction). Moderate coupling at a simple ratio gives you **robust synchronisation with flexibility** — both elements maintain their character while staying in relationship.

Which, if you think about it, is what good tuning means in any domain.

---

*This guide describes Arnold tongues and frequency locking, discovered in the study of coupled oscillators. The mathematics was developed by V.I. Arnold (1961) and has been applied in physics, biology, and engineering for decades. The practical applications to music, scheduling, and system design follow from the same underlying dynamics.*
