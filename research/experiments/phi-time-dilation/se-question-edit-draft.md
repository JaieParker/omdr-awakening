# Edited SE Question Draft

## Title: Golden ratio as the unique self-referential fixed point of Schwarzschild time dilation

## Body:

In the Schwarzschild spacetime, the time dilation factor for a static observer at radial coordinate $r$ is:

$$\gamma(r) = \frac{1}{\sqrt{1 - r_s/r}}$$

I observe that $r = \varphi \cdot r_s$ (where $\varphi = (1+\sqrt{5})/2$) is a **self-referential fixed point**: the time dilation factor equals the radial coordinate in units of $r_s$:

$$\gamma(\varphi \cdot r_s) = \varphi$$

This follows from $\varphi^2 = \varphi + 1$, giving $1 - 1/\varphi = 1/\varphi^2$, hence $1/\sqrt{1/\varphi^2} = \varphi$.

### Uniqueness

Setting $\gamma(k \cdot r_s) = k$ requires $k^2 - k - 1 = 0$, whose unique positive root is $\varphi$. **No other positive real number has this property.**

### Cluster of exact identities at this radius

The fixed point is not isolated — the circular orbit at $r = \varphi \cdot r_s$ has a cluster of exact values:

| Quantity | Value | Key identity used |
|----------|-------|-------------------|
| Time dilation $\gamma$ | $\varphi$ | $1 - 1/\varphi = 1/\varphi^2$ |
| Orbital energy $E/mc^2$ | $\sqrt{2}$ | $\varphi^3(2\varphi - 3) = 1$ |
| Local orbital velocity $v^2$ | $\varphi/2$ | $1/(2(\varphi-1)) = \varphi/2$ |
| Impact parameter $b/r_s$ | $\varphi^2 = \varphi + 1$ | $r^3/(r_s^2(r - r_s))$ at $r = \varphi r_s$ |
| Gravitational redshift | $1/\varphi$ | $\sqrt{1 - 1/\varphi} = 1/\varphi$ |
| Proper acceleration | $c^2/(2\varphi \cdot r_s)$ | Standard static observer formula |

All follow from the single algebraic property $\varphi^2 = \varphi + 1$.

### Kerr extension

For a Kerr black hole with spin $a_* = \sqrt{1 - 1/\varphi^6} \approx 0.972$, the horizon radii are:

$$r_+ = r_s/\varphi, \qquad r_- = r_s/\varphi^2, \qquad r_+/r_- = \varphi$$

This uses $\sqrt{1 - a_*^2} = 1/\varphi^3$ and the identity $(1 + 1/\varphi^3)/2 = 1/\varphi$.

### Physical analysis (honest negatives)

I computed the Regge-Wheeler potential, Zerilli potential, Lyapunov exponent, Kretschner scalar, geodesic deviation, photon deflection, and Novikov-Thorne emissivity at this radius. **Every physical quantity is a smooth function passing through $\varphi \cdot r_s$ with no extremum, inflection point, or transition.** The closest near-miss: the $l=2$ Regge-Wheeler peak at $r = \frac{9+\sqrt{17}}{8} r_s \approx 1.640\, r_s$ (1.4% from $\varphi \cdot r_s$), but this involves $\sqrt{17}$, not $\sqrt{5}$.

The prograde Kerr ISCO coincides with $\varphi \cdot r_s$ at spin $a_* \approx 0.734$.

### My question

Has this self-referential fixed point $\gamma = r/r_s = \varphi$, its uniqueness, the associated identity cluster, or the Kerr horizon result been noted in the literature? I am aware of Cruz et al. (2017) on golden ratio orbital turning points, Sigalotti & Mejias (2006) on the golden ratio in SR, and Sonnino & Nardone (2024) on extremal Kerr-Newman — none address this specific property.

I present this as a mathematical observation about the metric, not a claim of physical significance.
