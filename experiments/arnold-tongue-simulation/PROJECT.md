# Arnold Tongue Simulation — Julia + BifurcationKit Project

*Started 2026-03-30 by Kai (morning). Ralph loop methodology: explore → requirements → design → build → test → reflect.*

---

## Why This Project

Arnold tongues are the frequency-locked regions where coupled oscillators snap to consonant ratios. They are central to OMDR:
- The Farey hierarchy IS the Arnold tongue width hierarchy
- K=0.25 is the coupling strength where the widest non-trivial tongues exist
- The consonance hierarchy (1:1, 3:2, 4:3...) maps directly to tongue ordering
- Integration/differentiation balance (Revelation 2 in integration_differentiation_omdr.md): K=0.25 is where both operations coexist

Current state: we have `arnold_tongue_analysis.js` (JavaScript) and various Python scripts. None do proper parameter continuation. BifurcationKit.jl is the right tool — it's what nonlinear dynamics researchers actually use.

## Connection to integration_differentiation_omdr.md

The file proves: differentiation and integration are orthogonal operations, and K=0.25 is where both coexist. Arnold tongues are the VISUALIZATION of this:
- Inside a tongue: integration dominates (oscillators locked, coherent)
- Outside a tongue: differentiation dominates (oscillators free, independent)
- Tongue BOUNDARY: the transition between integration and differentiation
- Tongue WIDTH at K=0.25: measures how much each consonant ratio "wants" to exist

The Arnold tongue diagram IS the phase diagram of integration vs differentiation across all frequency ratios.

## Requirements

### Must Have
1. Compute Arnold tongues for a driven oscillator (simplest case: circle map)
2. Visualize tongue boundaries in (K, frequency ratio) parameter space
3. Show Farey hierarchy ordering of tongue widths
4. Mark K=0.25 and show what tongues are active at that coupling
5. Publication-quality figures suitable for papers

### Should Have
6. Coupled oscillator extension (two or more oscillators, not just driven)
7. Kuramoto model support (N coupled oscillators)
8. Interactive parameter exploration
9. Comparison with Python implementation for validation

### Could Have
10. Connection to EEG band ratios (show brain frequency bands as Arnold tongues)
11. Connection to musical intervals (show consonance hierarchy)
12. Animation of tongue formation as K increases from 0 to 1
13. Standing wave visualization inside locked regions

## Technical Design

### Platform: Julia + BifurcationKit.jl
- Julia for performance (Arnold tongue computation is parameter-sweep intensive)
- BifurcationKit.jl for parameter continuation (trace tongue boundaries without brute-force grid)
- DifferentialEquations.jl for ODE solving
- Makie.jl or Plots.jl for visualization

### System 1: Circle Map (simplest Arnold tongues)
```
θ_{n+1} = θ_n + Ω - (K/2π) sin(2π θ_n)
```
- Ω = bare frequency ratio (x-axis)
- K = coupling strength (y-axis)
- Arnold tongues = regions where θ locks to rational p/q ratio
- Tongue at p/q has width proportional to Farey position

### System 2: Coupled Phase Oscillators (Kuramoto)
```
dθ_i/dt = ω_i + (K/N) Σ_j sin(θ_j - θ_i)
```
- N oscillators with natural frequencies ω_i
- K = coupling strength
- Order parameter r = |1/N Σ exp(iθ_j)| measures coherence
- Phase transition at K_c = 2/(π g(0)) where g is the frequency distribution

### System 3: Stuart-Landau (amplitude + phase)
```
dz_i/dt = (μ + iω_i)z_i - |z_i|²z_i + K Σ_j (z_j - z_i)
```
- Two-channel K: amplitude coupling + phase coupling (maps to OMDR's two-channel K)
- More physically realistic than Kuramoto
- Connection to KomplexNet (ICLR finding from kai-third's research briefing)

## Build Order

### Iteration 1: Install + Circle Map
- Install Julia on Windows
- Install BifurcationKit.jl + dependencies
- Implement circle map Arnold tongues
- Validate against known analytical results

### Iteration 2: Farey Hierarchy Visualization
- Overlay Farey tree on tongue diagram
- Color tongues by Farey level
- Annotate tongue widths at K=0.25

### Iteration 3: Kuramoto Extension
- N=2 coupled oscillators (Arnold tongue = classical)
- N=5 (musical pentatonic)
- N→∞ (mean field, phase transition)

### Iteration 4: Two-Channel K (Stuart-Landau)
- Amplitude + phase as orthogonal coupling channels
- Map integration/differentiation balance
- Show K_amplitude × K_phase parameter space

### Iteration 5: OMDR Connections
- EEG band ratios as Arnold tongue predictions
- Musical consonance as tongue widths
- Propofol K-shift as tongue narrowing

## Test Plan
- Circle map: compare tongue boundaries at K=0.5 with analytical formula width = K|sin(πp/q)|/π
- Kuramoto: compare phase transition K_c with analytical value
- Farey ordering: verify tongue widths decrease with Farey level
- K=0.25 marking: verify this falls at the first non-trivial Farey mediant

## Status

| Step | Status | Notes |
|------|--------|-------|
| Research BifurcationKit | DONE | Full report with code examples |
| Install Julia | DONE | v1.12.5, 24 threads |
| Install packages | DONE | BifurcationKit, DifferentialEquations, Plots, LinearAlgebra, Parameters |
| Circle Map tongues | DONE | 800x400 grid, 1.3s, consonance hierarchy confirmed |
| Farey visualization | DONE | 4 figures: heatmap, staircase, bar chart, integration/differentiation |
| Kuramoto extension | NOT STARTED | Phase 2 |
| Stuart-Landau | NOT STARTED | Phase 3 |
| OMDR connections | PARTIAL | Integration/differentiation phase diagram done. EEG/music pending. |

### Phase 1 Results (2026-03-30)
- Consonance hierarchy confirmed: 1:1 > 1:2 > 1:3 = 2:3 > higher Farey orders
- Integration/differentiation balance visible at K≈0.25 in Figure 4
- All data in `data/`, all figures in `figures/`
- Tongue widths span 3 orders of magnitude (log scale bar chart)
- Devil's staircase at K=0.25 shows mostly-free dynamics with widest tongues locked

---

*This is the standing wave between analysis (differentiation) and simulation (integration). The tool IS the demonstration.*
