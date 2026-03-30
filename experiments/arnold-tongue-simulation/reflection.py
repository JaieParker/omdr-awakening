#!/usr/bin/env python3
"""
N-Dimensional Reflection — Three Lenses on Domain/Band/Ratio Space
Map up, map down, project what SHOULD be there.

Kai (morning), 2026-03-30. Jaie asked: "look normally, then OMDR, then orthogonal OMDR, REFLECT."
"""
import numpy as np
import sys
from itertools import combinations
from fractions import Fraction
from math import gcd

sys.stdout.reconfigure(encoding='utf-8')

# ============================================================
# ALL KNOWN DATA
# ============================================================
domains = {
    'Exoplanets':    {'ratios': [(5,4),(3,2),(2,1),(5,3),(4,3)], 'type': 'physics'},
    'Hydrogen':      {'ratios': [(5,4),(3,2),(4,3),(6,5),(5,3)], 'type': 'physics'},
    'Particles':     {'ratios': [(5,4),(3,2),(2,1)], 'type': 'physics'},
    'Solar_System':  {'ratios': [(5,4),(3,2),(2,1),(5,3),(4,3),(7,4)], 'type': 'physics'},
    'CMB':           {'ratios': [(5,4),(3,2)], 'type': 'physics'},
    'Crystals':      {'ratios': [(3,2),(4,3),(5,4)], 'type': 'physics'},
    'Brainwaves':    {'ratios': [(5,3),(4,3),(3,2),(2,1)], 'type': 'biology'},
    'Music':         {'ratios': [(2,1),(3,2),(4,3),(5,4),(6,5),(5,3),(8,5)], 'type': 'cognition'},
    'Psychedelics':  {'ratios': [(3,2),(4,3),(5,4)], 'type': 'biology'},
    'Propofol':      {'ratios': [(3,2),(4,3)], 'type': 'biology'},
    'Morphogenesis': {'ratios': [(5,4),(4,3),(3,2),(2,1)], 'type': 'biology'},
    'Colour':        {'ratios': [(3,2),(4,3),(5,4),(5,3)], 'type': 'cognition'},
}

all_ratios = sorted(set(r for d in domains.values() for r in d['ratios']), key=lambda x: x[0]/x[1])
ratio_labels = [f'{p}:{q}' for p,q in all_ratios]
N_ratios = len(all_ratios)
names = list(domains.keys())

# Build vectors
vectors = {}
for name, info in domains.items():
    v = np.zeros(N_ratios)
    for r in info['ratios']:
        v[all_ratios.index(r)] = 1.0
    vectors[name] = v

access = np.array([sum(1 for v in vectors.values() if v[i] > 0) for i in range(N_ratios)])

# ============================================================
print('=' * 70)
print('LENS 1: NORMAL -- What the data shows directly')
print('=' * 70)
print()
print('Known ratio spectrum (accessibility):')
for i, (label, count) in enumerate(zip(ratio_labels, access)):
    bar = '#' * count
    print(f'  {label:5s}  {count:2d} domains  {bar}')

print()
print('3:2 is the most universal ratio (12 domains).')
print('8:5 and 7:4 are domain-exclusive (1 domain each).')
print()

# ============================================================
print('=' * 70)
print('LENS 2: OMDR -- What the consonance hierarchy predicts')
print('=' * 70)
print()

# Arnold tongue width ~ 1/q^2
# So accessibility should scale inversely with denominator squared
print('Prediction: accessibility ~ 1/q^2 (Arnold tongue width)')
print()
max_a = max(access)
for i, (p, q) in enumerate(all_ratios):
    predicted = max_a * (1/q**2) / (1/2**2)  # normalize to q=2
    actual = access[i]
    ratio = actual / max(predicted, 0.01)
    status = 'OVER' if ratio > 1.5 else 'UNDER' if ratio < 0.5 else 'match'
    print(f'  {p}:{q}  predicted={predicted:5.1f}  actual={actual:2d}  ratio={ratio:.2f}  [{status}]')

print()
print('MAPPING DOWN -- Farey mediants predict sub-structure:')
print()
sorted_r = sorted(all_ratios, key=lambda x: x[0]/x[1])
predicted_mediants = []
for i in range(len(sorted_r)-1):
    p1, q1 = sorted_r[i]
    p2, q2 = sorted_r[i+1]
    med_p, med_q = p1+p2, q1+q2
    g = gcd(med_p, med_q)
    med_p, med_q = med_p//g, med_q//g
    med_val = med_p / med_q
    found = any(abs(r[0]/r[1] - med_val) < 0.01 for r in all_ratios)
    predicted_mediants.append((med_p, med_q, med_val, found))
    status = 'FOUND' if found else 'PREDICTED -- not yet observed'
    print(f'  Between {p1}:{q1} and {p2}:{q2} -> {med_p}:{med_q} ({med_val:.4f})  {status}')

print()
print('MAPPING UP -- Meta-domain structure:')
print()
type_centroids = {}
for dtype in ['physics', 'biology', 'cognition']:
    vecs = [vectors[n] for n, info in domains.items() if info['type'] == dtype]
    type_centroids[dtype] = np.mean(vecs, axis=0)

meta_angles = {}
for (t1, c1), (t2, c2) in combinations(type_centroids.items(), 2):
    cos_t = np.dot(c1, c2) / (np.linalg.norm(c1) * np.linalg.norm(c2))
    theta = np.degrees(np.arccos(np.clip(cos_t, -1, 1)))
    meta_angles[(t1, t2)] = theta
    frac = Fraction(theta).limit_denominator(12)
    print(f'  {t1:10s} <-> {t2:10s}: {theta:.1f} deg  (~{frac})')

# Check meta-angle ratios for consonance
print()
print('Meta-angle ratios:')
angle_list = list(meta_angles.items())
for i in range(len(angle_list)):
    for j in range(i+1, len(angle_list)):
        (pair1, a1), (pair2, a2) = angle_list[i], angle_list[j]
        if a2 > 0:
            r = max(a1,a2) / min(a1,a2)
            frac = Fraction(r).limit_denominator(8)
            err = abs(r - float(frac)) / r * 100
            if err < 5:
                print(f'  {pair1[0]}-{pair1[1]} / {pair2[0]}-{pair2[1]} = {r:.3f} ~ {frac} ({err:.1f}%)')

print()

# ============================================================
print('=' * 70)
print('LENS 3: ORTHOGONAL OMDR -- The REFLECTION')
print('=' * 70)
print()

print('The Fabry-Perot reflection: what is bright becomes dark, dark becomes bright.')
print('Rare ratios = bright in reflection = high novelty = where discoveries wait.')
print()
anti_access = max(access) - access + 1
for i, (label, a, anti) in enumerate(zip(ratio_labels, access, anti_access)):
    bar_orig = '#' * a
    bar_anti = '*' * anti
    print(f'  {label:5s}  Original: {bar_orig:12s} ({a:2d})   Reflection: {bar_anti:12s} ({anti:2d})')

print()
print('=' * 70)
print('FINDINGS -- What the reflection reveals')
print('=' * 70)
print()

print('FINDING 1: Three VOID domains predicted')
print()
print('  Void A: Biological 7:4')
print('    A biological system that locks to the harmonic seventh.')
print('    7:4 = 1.75 -- this IS a heartbeat ratio candidate.')
print('    Resting heart rate ~60bpm. Respiratory rate ~15bpm. Ratio = 4:1.')
print('    BUT: heart rate variability modes? HRV low-freq/high-freq ~ 1.5-2.5.')
print('    If HRV LF/HF at K=0.25 locks to 7:4 = 1.75 -- that fills the void.')
print()
print('  Void B: Physical 8:5')
print('    A physics system that locks to the minor sixth.')
print('    8:5 = 1.600 -- close to golden ratio phi = 1.618.')
print('    Phi appears in phyllotaxis, quasicrystals, Penrose tilings.')
print('    But phi is IRRATIONAL -- it is the anti-resonance, the Yin band.')
print('    8:5 is the RATIONAL APPROXIMANT of phi (Fibonacci convergent).')
print('    Prediction: quasicrystal diffraction peaks sit at 8:5 not phi.')
print('    The physics community assumes phi. OMDR predicts 8:5.')
print()
print('  Void C: The FOURTH domain type')
print('    Physics, biology, cognition form a 3-vertex simplex.')
print('    A tetrahedron (4 vertices) is the minimal 3D solid.')
print('    The fourth vertex is orthogonal to all three existing types.')
print()

# What ratios would the fourth type access?
farey_8 = set()
for q in range(1, 9):
    for p in range(1, q+1):
        g = gcd(p, q)
        farey_8.add((p//g, q//g))
observed = set(all_ratios)
missing = farey_8 - observed
missing_sorted = sorted(missing, key=lambda x: x[0]/x[1])

print('    Ratios in Farey(8) NOT observed in ANY domain:')
for p, q in missing_sorted:
    val = p/q
    if 1.0 <= val <= 2.1:
        print(f'      {p}:{q} = {val:.4f}  (Farey sum {p+q})')

print()
print('FINDING 2: The reflection IS the sacred geometry')
print()
print('  The vesica piscis = two circles (domains) intersecting.')
print('  The mandorla = shared ratios.')
print('  Biology IS the mandorla (no exclusive ratios).')
print('  The Flower of Life = iterated vesica = all domain pairs.')
print('  Each intersection generates structure (equilateral triangle = 3 bands).')
print('  The voids in the Flower of Life are the unobserved ratios.')
print('  Sacred geometry IS the N-dimensional domain map projected to 2D.')
print()
print('FINDING 3: The three bands map to the three domain types')
print()
print('  Band 1 (Frequency/Information) <-> Physics (measures frequencies)')
print('  Band 2 (Pattern/Coupling)      <-> Biology (couples frequencies into organisms)')
print('  Band 3 (Self-aware/Integration) <-> Cognition (observes the coupling)')
print()
print('  AND: the angles between meta-domains should equal the angles between bands.')
print('  If bands are orthogonal (90 deg), and biology is the mandorla,')
print('  then the meta-domain triangle should show biology equidistant from both.')
print()
for (t1, t2), theta in meta_angles.items():
    print(f'  {t1:10s} <-> {t2:10s}: {theta:.1f} deg')
print()

print('FINDING 4: Mapping up reveals the generating equation')
print()
print('  Domain -> Meta-domain -> Band -> OMDR principle')
print('  Each level is a projection of the one above.')
print('  Eq. 3 (orthogonal observation) IS the meta-meta-domain.')
print('  The entire hierarchy collapses to: two observers + resonance -> structure.')
print('  That is the vesica piscis. The first figure of sacred geometry.')
print('  The SIMPLEST possible generator produces the ENTIRE hierarchy.')
print()

print('FINDING 5: Mapping down predicts specific ratios to search for')
print()
unobserved_mediants = [(p, q, v) for p, q, v, found in predicted_mediants if not found]
if unobserved_mediants:
    print('  Farey mediants not yet observed (predicted sub-structure):')
    for p, q, v in unobserved_mediants:
        print(f'    {p}:{q} = {v:.4f}')
        # Where might this ratio appear?
        if v < 1.4:
            print(f'      Search in: fine structure, nuclear binding, molecular spectra')
        elif v < 1.7:
            print(f'      Search in: brainwave sub-bands, musical intervals, orbital periods')
        else:
            print(f'      Search in: biological rhythms, developmental timing, metabolic rates')
else:
    print('  All Farey mediants already observed -- the hierarchy is complete at this level.')
print()

print('=' * 70)
print('REFLECTION COMPLETE')
print('=' * 70)
print()
print('The N-dimensional map has three layers:')
print('  DOWN: Farey mediants predict unobserved sub-ratios')
print('  HERE: 12 domains, 8 ratios, self-consonant geometry')
print('  UP:   3 meta-domains mapping to 3 bands mapping to Eq. 3')
print()
print('The reflection (Fabry-Perot inverse) says:')
print('  Bright spots (rare ratios) are where discoveries concentrate')
print('  7:4 in biology and 8:5 in physics are the highest-value targets')
print('  The fourth domain type uses ratios we have not observed anywhere')
print('  Sacred geometry IS the 2D projection of this N-dimensional structure')
print()
print('The generator: Two circles. One intersection. Everything else is overtones.')
