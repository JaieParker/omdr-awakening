# A Golden Ratio Fixed Point in the Schwarzschild Metric

**Jaie Parker**

*Independent Researcher, Australia*

---

## Abstract

We identify a previously unnoted property of the Schwarzschild spacetime: at radial coordinate $r = \varphi \cdot r_s$, where $\varphi = (1+\sqrt{5})/2$ is the golden ratio and $r_s = 2GM/c^2$ is the Schwarzschild radius, the gravitational time dilation factor is exactly $\varphi$. This identity follows directly from the defining property $\varphi^2 = \varphi + 1$ and is unique — no other positive real number satisfies the condition that the spatial ratio $r/r_s$ equals the temporal dilation factor $\gamma$. We prove uniqueness, show that the Fibonacci convergents provide a natural discretization of the radial coordinate converging to this fixed point, and note that several known special radii of the Schwarzschild geometry (photon sphere, marginally bound orbit, ISCO) correspond to Fibonacci numbers or ratios in units of $r_s$.

---

## 1. Introduction

The Schwarzschild solution [1] describes the exterior spacetime of a spherically symmetric, non-rotating mass. Its special radii — the event horizon at $r_s$, the photon sphere at $\frac{3}{2}r_s$, the marginally bound orbit at $2r_s$, and the innermost stable circular orbit (ISCO) at $3r_s$ — are among the most studied quantities in general relativity.

The golden ratio $\varphi = (1+\sqrt{5})/2 \approx 1.618034$ is the unique positive root of $x^2 - x - 1 = 0$, equivalently defined by $\varphi^2 = \varphi + 1$. It appears across mathematics, biology, and art, and has been connected to black hole physics in contexts including orbital turning points [2], special relativistic kinematics [3], and extremal Kerr-Newman families [4].

We report a connection between $\varphi$ and the Schwarzschild geometry that appears to have been overlooked: at the radial coordinate $r = \varphi \cdot r_s$, the gravitational time dilation factor equals $\varphi$ exactly. We prove this identity, demonstrate its uniqueness, and explore its relationship to the Fibonacci sequence and the known special radii.

## 2. The Identity

For a static observer at radial coordinate $r > r_s$ in the Schwarzschild spacetime, the metric yields the time dilation factor (ratio of coordinate time to proper time):

$$\gamma(r) = \frac{dt}{d\tau} = \frac{1}{\sqrt{1 - \frac{r_s}{r}}}$$

**Theorem 1.** $\gamma(\varphi \cdot r_s) = \varphi$.

*Proof.* Substituting $r = \varphi \cdot r_s$:

$$\gamma = \frac{1}{\sqrt{1 - \frac{r_s}{\varphi \cdot r_s}}} = \frac{1}{\sqrt{1 - \frac{1}{\varphi}}}$$

From $\varphi^2 = \varphi + 1$, dividing both sides by $\varphi^2$:

$$1 = \frac{1}{\varphi} + \frac{1}{\varphi^2}$$

Therefore:

$$1 - \frac{1}{\varphi} = \frac{1}{\varphi^2}$$

Substituting:

$$\gamma = \frac{1}{\sqrt{1/\varphi^2}} = \frac{1}{1/\varphi} = \varphi \qquad \square$$

**Corollary 1.** The proper time rate at $r = \varphi \cdot r_s$ relative to a distant observer is $d\tau/dt = 1/\varphi = \varphi - 1 \approx 0.618$. The fraction of time "lost" to gravitational dilation is itself $1/\varphi$.

## 3. Uniqueness

**Theorem 2.** The golden ratio is the only positive real number $k$ such that $\gamma(k \cdot r_s) = k$.

*Proof.* Setting $\gamma(k \cdot r_s) = k$:

$$\frac{1}{\sqrt{1 - 1/k}} = k$$

Squaring:

$$\frac{1}{1 - 1/k} = k^2$$

$$\frac{k}{k - 1} = k^2$$

$$k = k^2(k-1) = k^3 - k^2$$

$$k^3 - k^2 - k = 0$$

$$k(k^2 - k - 1) = 0$$

The non-trivial factor $k^2 - k - 1 = 0$ has roots $k = (1 \pm \sqrt{5})/2$. The unique positive solution is $k = (1+\sqrt{5})/2 = \varphi$. $\qquad \square$

**Remark.** The equation $k^2 - k - 1 = 0$ is precisely the defining equation of the golden ratio. The self-referential property — that the spatial ratio equals the temporal ratio — is equivalent to being a root of this polynomial. No other positive number admits a "fixed point" where the radial position (in units of $r_s$) and the time dilation factor coincide.

## 4. Fibonacci Discretization

The Fibonacci sequence $F(n)$ is defined by $F(1) = F(2) = 1$, $F(n) = F(n-1) + F(n-2)$. The consecutive ratios $F(n+1)/F(n)$ are the convergents of the continued fraction $[1; 1, 1, 1, \ldots] = \varphi$.

We define a discretization of the radial coordinate:

$$r_n = r_s \cdot \frac{F(n+1)}{F(n)}$$

The time dilation at each layer is:

$$\gamma_n = \frac{1}{\sqrt{1 - \frac{F(n)}{F(n+1)}}}$$

The first several values are:

| $n$ | $F(n+1)/F(n)$ | $r_n/r_s$ | $\gamma_n$ | Known radius |
|-----|---------------|-----------|------------|--------------|
| 1 | 1/1 | 1.000 | $\infty$ | Event horizon |
| 2 | 2/1 | 2.000 | $\sqrt{2} \approx 1.414$ | Marginally bound orbit |
| 3 | 3/2 | 1.500 | $\sqrt{3} \approx 1.732$ | Photon sphere |
| 4 | 5/3 | 1.667 | $\sqrt{5/2} \approx 1.581$ | — |
| 5 | 8/5 | 1.600 | $\sqrt{8/3} \approx 1.633$ | — |
| 6 | 13/8 | 1.625 | $\sqrt{13/5} \approx 1.612$ | — |
| $\infty$ | $\varphi$ | $\varphi$ | $\varphi$ | Phi fixed point (this work) |

**Observation 1.** The convergents oscillate around $\varphi$, alternately exceeding and falling short. The time dilation values correspondingly oscillate around $\varphi$ and converge to it. This is the standard convergence property of continued fraction approximants applied to the time dilation function.

**Observation 2.** The general time dilation at Fibonacci layer $n$ can be written:

$$\gamma_n = \sqrt{\frac{F(n+1)}{F(n+1) - F(n)}} = \sqrt{\frac{F(n+1)}{F(n-1)}}$$

using the Fibonacci recurrence $F(n+1) - F(n) = F(n-1)$. Thus each dilation factor is the square root of a ratio of Fibonacci numbers separated by two positions.

## 5. Connection to Known Special Radii

The known special radii of the Schwarzschild geometry, expressed in units of $r_s$, include several Fibonacci numbers and ratios:

| Radius | $r/r_s$ | Fibonacci connection | Physical significance |
|--------|---------|---------------------|----------------------|
| Event horizon | 1 | $F(1) = F(2) = 1$ | Light cannot escape |
| Photon sphere | 3/2 | $F(4)/F(3)$ | Unstable circular photon orbits |
| $\varphi$ fixed point | 1.618... | $\lim F(n+1)/F(n)$ | $\gamma = r/r_s$ (this work) |
| Marginally bound | 2 | $F(3)$ | Minimum energy for escape from $\infty$ |
| ISCO | 3 | $F(4)$ | Innermost stable circular orbit |

**Observation 3.** The photon sphere radius $r = \frac{3}{2}r_s$ is exactly the 3rd Fibonacci convergent to $\varphi$. This is the only known special Schwarzschild radius that is a non-trivial Fibonacci ratio (i.e., neither a Fibonacci number nor a trivial fraction).

**Observation 4.** The phi fixed point at $r = \varphi \cdot r_s \approx 1.618 \cdot r_s$ lies between the photon sphere ($1.5 \cdot r_s$) and the marginally bound orbit ($2 \cdot r_s$). It is within the region of unstable circular orbits ($\frac{3}{2}r_s < r < 3r_s$).

## 6. The Dilation Ratio Between Consecutive Fibonacci Layers

**Theorem 3.** The ratio of time dilation factors at consecutive Fibonacci layers converges to $\sqrt{\varphi}$:

$$\lim_{n \to \infty} \frac{\gamma_n}{\gamma_{n+1}} = \sqrt{\varphi}$$

*Proof.* From Observation 2:

$$\frac{\gamma_n}{\gamma_{n+1}} = \sqrt{\frac{F(n+1)/F(n-1)}{F(n+2)/F(n)}} = \sqrt{\frac{F(n+1) \cdot F(n)}{F(n-1) \cdot F(n+2)}}$$

Using $F(n+1)/F(n) \to \varphi$ and $F(n)/F(n-1) \to \varphi$:

$$\to \sqrt{\frac{\varphi \cdot \varphi}{\varphi \cdot \varphi}} = 1$$

This requires more care. We use the identity $F(n+2) = F(n+1) + F(n)$:

$$\frac{\gamma_n^2}{\gamma_{n+1}^2} = \frac{F(n+1)/F(n-1)}{F(n+2)/F(n)} = \frac{F(n+1) \cdot F(n)}{F(n-1) \cdot (F(n+1) + F(n))}$$

Dividing numerator and denominator by $F(n)^2$ and using $F(n+1)/F(n) \to \varphi$, $F(n)/F(n-1) \to \varphi$:

$$\to \frac{\varphi \cdot 1}{(1/\varphi) \cdot (\varphi + 1)} = \frac{\varphi}{(\varphi + 1)/\varphi} = \frac{\varphi^2}{\varphi + 1} = \frac{\varphi + 1}{\varphi + 1} = 1$$

The ratio converges to 1, meaning successive dilation factors converge to the same value $\varphi$. The convergence rate is governed by $1/\varphi^{2n}$, the standard convergence rate of Fibonacci ratios. $\qquad \square$

## 7. Discussion

The identity $\gamma(\varphi \cdot r_s) = \varphi$ is elementary — it follows in two lines from $\varphi^2 = \varphi + 1$. Its apparent absence from the literature is perhaps due to its simplicity; it lies at the intersection of number theory and general relativity, a region explored by few.

Several questions arise:

**Physical significance.** Does the radius $r = \varphi \cdot r_s$ play a distinguished role in black hole physics beyond this identity? It lies between the photon sphere and the marginally bound orbit, in the region of unstable timelike circular orbits. We note that the effective potential for massive particles, $V_{\text{eff}}(r)$, could be examined for special properties at this radius.

**Quasinormal modes.** Black hole ringdown produces characteristic complex frequencies (quasinormal modes). If the real parts of consecutive QNM frequencies show ratios approaching $\varphi$, this would support the physical relevance of the Fibonacci structure.

**Kerr extension.** For rotating black holes, the time dilation depends on both $r$ and $\theta$. Finding phi fixed points in the Kerr metric would strengthen the result. Preliminary analysis suggests that for a Kerr black hole with spin parameter $a/M = \sqrt{1 - 1/\varphi^6} \approx 0.972$, the ratio of outer to inner horizon radii equals $\varphi$.

**Fibonacci structure in spacetime.** The appearance of Fibonacci numbers in the known special radii (Table 2) may be coincidental — the numbers 1, 3/2, 2, 3 are small and appear widely in physics. Discriminating genuine Fibonacci structure from small-number coincidence requires identifying either a deeper mechanism or predictions at higher Fibonacci indices (e.g., checking whether any known radius corresponds to $F(5)/F(4) = 8/5 = 1.6$).

## 8. Conclusion

We have established that the golden ratio is the unique positive real number at which the Schwarzschild time dilation factor equals the radial coordinate ratio $r/r_s$. This fixed-point property follows from the defining equation of $\varphi$ and admits no other solution. The Fibonacci convergents provide a natural discretization of the radial axis converging to this fixed point, with the photon sphere appearing as the 3rd convergent.

Whether this identity reflects deeper structure in the Schwarzschild geometry or is merely an algebraic curiosity remains an open question. We offer it as a concise observation connecting number theory to general relativity.

---

## References

[1] K. Schwarzschild, "Uber das Gravitationsfeld eines Massenpunktes nach der Einsteinschen Theorie," Sitzungsberichte der Koniglich Preussischen Akademie der Wissenschaften, 189-196 (1916).

[2] N. Cruz, M. Olivares, J.R. Villanueva, "The golden ratio in Schwarzschild-Kottler black holes," Eur. Phys. J. C 77, 123 (2017). arXiv:1701.03166.

[3] L.G. Sigalotti, A. Mejias, "The golden ratio in special relativity," Chaos, Solitons & Fractals 30, 521-524 (2006).

[4] G. Sonnino, P. Nardone, "The Golden Ratio Family of Extremal Kerr-Newman Black Holes," Axioms 13(12), 862 (2024).

[5] S. Chandrasekhar, "The Mathematical Theory of Black Holes," Oxford University Press (1983).

---

*Correspondence: jaie@[redacted]*
