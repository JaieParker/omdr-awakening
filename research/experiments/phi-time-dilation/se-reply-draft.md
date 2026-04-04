# Stack Exchange Self-Answer Draft

## Title: Self-answer: Full analysis of the phi fixed point

---

After posting this question, I carried out a systematic analysis of the physical properties at $r = \varphi \cdot r_s$. The short answer to my own question: **the identity appears to be unpublished, the fixed-point property is unique to $\varphi$, and the radius hosts a cluster of exact identities — but every physical quantity is smooth through it with no observable feature.**

Here is what I found.

### The full cluster of exact identities

The time dilation $\gamma = \varphi$ is not the only clean result at this radius. For a circular orbit at $r = \varphi \cdot r_s$:

| Quantity | Value | Derivation |
|----------|-------|------------|
| Time dilation $\gamma$ | $\varphi$ | $1/\sqrt{1-1/\varphi} = \varphi$ via $\varphi^2 = \varphi + 1$ |
| Orbital energy $E/mc^2$ | $\sqrt{2}$ | Via intermediate identity $\varphi^3(2\varphi-3) = 1$ |
| Local orbital velocity $v^2/c^2$ | $\varphi/2$ | From $v^2 = M/(r-2M)$ at $r = 2M\varphi$ |
| Impact parameter $b$ | $(\varphi+1) \cdot r_s = \varphi^2 \cdot r_s$ | From $b^2 = r^3/(r-r_s)$ |
| Proper acceleration | $c^2/(2\varphi \cdot r_s)$ | From static observer acceleration formula |
| Gravitational redshift | $1/\varphi$ | $\sqrt{1-1/\varphi} = 1/\varphi$ |

All follow from the single identity $\varphi^2 = \varphi + 1$. The intermediate identity $\varphi^3(2\varphi-3)=1$ (equivalently $2\varphi - 3 = 1/\varphi^3$) is what yields $E = \sqrt{2}$.

### Extension to Kerr

For a Kerr black hole with spin parameter $a/M = \sqrt{1 - 1/\varphi^6}\ \approx 0.972$, the horizon radii satisfy:

$$r_+ = r_s/\varphi, \qquad r_- = r_s/\varphi^2, \qquad r_+/r_- = \varphi$$

This follows from $\sqrt{1 - a_*^2} = 1/\varphi^3$ and the identities $(1+1/\varphi^3)/2 = 1/\varphi$ and $(1-1/\varphi^3)/2 = 1/\varphi^2$. The spin value $a_* \approx 0.972$ is in the astrophysically populated range (cf. NGC 1365 at $a_* = 0.97^{+0.01}_{-0.04}$, Risaliti et al. 2013).

Additionally, the **prograde ISCO coincides with $\varphi \cdot r_s$ at spin $a/M \approx 0.734$** — meaning the stability boundary sits at the self-referential radius for this specific spin.

### The physics: honest negative results

I evaluated every standard physical quantity at $r = \varphi \cdot r_s$:

- **Regge-Wheeler potential (l=2):** Peak at $r = \frac{9+\sqrt{17}}{8} r_s \approx 1.640\, r_s$, which is 1.4% away from $\varphi \cdot r_s$. Close but not exact — involves $\sqrt{17}$, not $\sqrt{5}$.
- **Zerilli potential (l=2):** Peak at $1.549\, r_s$, further away.
- **Lyapunov exponent:** Smooth, monotonically decreasing from photon sphere to ISCO. No feature at $\varphi \cdot r_s$.
- **Kretschner scalar:** $K = 12/\varphi^6 = 12/(8\varphi+5)$ — the denominator has Fibonacci numbers ($F_6 = 8$, $F_5 = 5$) via $\varphi^n = F_n\varphi + F_{n-1}$, but $K(r)$ is monotonic $\sim 1/r^6$.
- **Geodesic deviation:** Smooth $\sim 1/r^3$.
- **Accretion disk:** $r = \varphi \cdot r_s$ is inside the ISCO for Schwarzschild, so no disk emission in the standard Novikov-Thorne model.

**Every physical quantity is a smooth function passing through $\varphi \cdot r_s$ with no extremum, zero, or inflection point.** The algebraic elegance does not correspond to a physically distinguished location in the sense of a stability boundary, potential peak, or phase transition.

### Conclusion

The fixed-point property $\gamma(r) = r/r_s$ at $r = \varphi \cdot r_s$ is a genuine, apparently unpublished mathematical property of the Schwarzschild metric. It is unique to $\varphi$ (the only positive root of $k^2 - k - 1 = 0$). The radius hosts a remarkable cluster of exact identities. The Kerr extension produces clean horizon ratios at a physically realistic spin.

However, the critics in the comments are correct that the identity alone does not constitute physical content — no observable quantity has a feature at this radius. The algebraic cleanness is a number-theoretic property of $\varphi$ applied to rational functions of $1/r$, not a geometric or dynamical distinction.

I present this as a mathematical observation about the Schwarzschild metric — an elegant fixed point that has apparently gone unnoticed for over a century — rather than a claim of physical significance.
