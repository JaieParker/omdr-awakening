#!/usr/bin/env python3
"""
Domain Mapper — add a new domain, get its position in the consonance space.

Usage:
    python domain_mapper.py                     # show all domains + orthogonality matrix
    python domain_mapper.py add "HRV" 7:4 3:2 2:1   # add a domain with its ratios
    python domain_mapper.py predict "HRV"       # predict what ratios HRV should access
    python domain_mapper.py gaps                # show unobserved ratios + where to look
"""
import numpy as np
import sys
import json
from itertools import combinations
from fractions import Fraction
from math import gcd
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data" / "domains.json"

DEFAULT_DOMAINS = {
    "Exoplanets":    {"ratios": [[5,4],[3,2],[2,1],[5,3],[4,3]], "type": "physics"},
    "Hydrogen":      {"ratios": [[5,4],[3,2],[4,3],[6,5],[5,3]], "type": "physics"},
    "Particles":     {"ratios": [[5,4],[3,2],[2,1]], "type": "physics"},
    "Solar System":  {"ratios": [[5,4],[3,2],[2,1],[5,3],[4,3],[7,4]], "type": "physics"},
    "CMB":           {"ratios": [[5,4],[3,2]], "type": "physics"},
    "Crystals":      {"ratios": [[3,2],[4,3],[5,4]], "type": "physics"},
    "Brainwaves":    {"ratios": [[5,3],[4,3],[3,2],[2,1]], "type": "biology"},
    "Music":         {"ratios": [[2,1],[3,2],[4,3],[5,4],[6,5],[5,3],[8,5]], "type": "cognition"},
    "Psychedelics":  {"ratios": [[3,2],[4,3],[5,4]], "type": "biology"},
    "Propofol":      {"ratios": [[3,2],[4,3]], "type": "biology"},
    "Morphogenesis": {"ratios": [[5,4],[4,3],[3,2],[2,1]], "type": "biology"},
    "Colour":        {"ratios": [[3,2],[4,3],[5,4],[5,3]], "type": "cognition"},
}

def load_domains():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return dict(DEFAULT_DOMAINS)

def save_domains(domains):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(domains, indent=2), encoding="utf-8")

def all_ratios(domains):
    ratios = set()
    for d in domains.values():
        for r in d["ratios"]:
            ratios.add(tuple(r))
    return sorted(ratios, key=lambda x: x[0]/x[1])

def domain_vector(domain_info, ratio_list):
    v = np.zeros(len(ratio_list))
    for r in domain_info["ratios"]:
        if tuple(r) in ratio_list:
            v[ratio_list.index(tuple(r))] = 1.0
    return v

def angle_between(v1, v2):
    cos_t = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-10)
    return np.degrees(np.arccos(np.clip(cos_t, -1, 1)))

def show_all(domains):
    ratios = all_ratios(domains)
    names = list(domains.keys())
    vectors = {n: domain_vector(d, ratios) for n, d in domains.items()}

    print(f"\n{len(domains)} domains, {len(ratios)} ratios")
    print(f"Ratios: {[f'{p}:{q}' for p,q in ratios]}\n")

    # Orthogonality pairs
    pairs = []
    for n1, n2 in combinations(names, 2):
        theta = angle_between(vectors[n1], vectors[n2])
        pairs.append((n1, n2, theta))

    pairs.sort(key=lambda x: -x[2])
    print("Most orthogonal (new knowledge lives here):")
    for n1, n2, theta in pairs[:5]:
        frac = Fraction(theta).limit_denominator(8)
        print(f"  {n1:20s} <-> {n2:20s}: {theta:.1f} deg")

    print("\nMost parallel (same standing wave):")
    for n1, n2, theta in pairs[-5:]:
        print(f"  {n1:20s} <-> {n2:20s}: {theta:.1f} deg")

def add_domain(domains, name, ratios_str, dtype="unknown"):
    ratios = []
    for r in ratios_str:
        p, q = r.split(":")
        ratios.append([int(p), int(q)])
    domains[name] = {"ratios": ratios, "type": dtype}
    save_domains(domains)

    # Show where it sits
    all_r = all_ratios(domains)
    new_vec = domain_vector(domains[name], all_r)
    print(f"\nAdded '{name}' with ratios {ratios_str}")
    print(f"\nAngles to existing domains:")
    for other_name, other_info in domains.items():
        if other_name == name:
            continue
        other_vec = domain_vector(other_info, all_r)
        theta = angle_between(new_vec, other_vec)
        print(f"  {other_name:20s}: {theta:.1f} deg")

def predict_ratios(domains, name):
    if name not in domains:
        print(f"Domain '{name}' not found.")
        return

    all_r = all_ratios(domains)
    target_vec = domain_vector(domains[name], all_r)

    # Find most similar domains
    similarities = []
    for other_name, other_info in domains.items():
        if other_name == name:
            continue
        other_vec = domain_vector(other_info, all_r)
        theta = angle_between(target_vec, other_vec)
        similarities.append((other_name, theta, other_vec))

    similarities.sort(key=lambda x: x[1])

    # Predict: ratios accessed by nearest neighbours but not by target
    current = set(tuple(r) for r in domains[name]["ratios"])
    predictions = {}
    for other_name, theta, other_vec in similarities[:5]:
        other_ratios = set(tuple(r) for r in domains[other_name]["ratios"])
        missing = other_ratios - current
        for r in missing:
            if r not in predictions:
                predictions[r] = []
            predictions[r].append((other_name, theta))

    print(f"\nPredictions for '{name}':")
    print(f"Currently accesses: {[f'{p}:{q}' for p,q in sorted(current, key=lambda x:x[0]/x[1])]}")
    print(f"\nRatios it SHOULD access (from nearest neighbours):")
    for r, sources in sorted(predictions.items(), key=lambda x: len(x[1]), reverse=True):
        source_str = ", ".join(f"{s[0]} ({s[1]:.0f} deg)" for s in sources)
        print(f"  {r[0]}:{r[1]} -- suggested by {len(sources)} neighbours: {source_str}")

def show_gaps(domains):
    all_r = all_ratios(domains)

    # Farey mediants between adjacent ratios
    sorted_r = sorted(all_r, key=lambda x: x[0]/x[1])
    print("\nFarey mediants (predicted sub-structure):")
    for i in range(len(sorted_r)-1):
        p1, q1 = sorted_r[i]
        p2, q2 = sorted_r[i+1]
        mp, mq = p1+p2, q1+q2
        g = gcd(mp, mq)
        mp, mq = mp//g, mq//g
        found = any(abs(r[0]/r[1] - mp/mq) < 0.01 for r in all_r)
        if not found:
            print(f"  {mp}:{mq} = {mp/mq:.4f}  (between {p1}:{q1} and {p2}:{q2})")

    # Exclusive ratios
    by_type = {}
    for name, info in domains.items():
        t = info["type"]
        if t not in by_type:
            by_type[t] = set()
        for r in info["ratios"]:
            by_type[t].add(tuple(r))

    print("\nExclusive ratios (cross-domain predictions):")
    types = list(by_type.keys())
    for t in types:
        others = set()
        for t2 in types:
            if t2 != t:
                others |= by_type[t2]
        exclusive = by_type[t] - others
        if exclusive:
            print(f"  {t} only: {[f'{p}:{q}' for p,q in sorted(exclusive, key=lambda x:x[0]/x[1])]}")

if __name__ == "__main__":
    domains = load_domains()

    if len(sys.argv) < 2:
        show_all(domains)
        show_gaps(domains)
    elif sys.argv[1] == "add" and len(sys.argv) >= 4:
        name = sys.argv[2]
        ratios = sys.argv[3:]
        add_domain(domains, name, ratios)
    elif sys.argv[1] == "predict" and len(sys.argv) >= 3:
        predict_ratios(domains, sys.argv[2])
    elif sys.argv[1] == "gaps":
        show_gaps(domains)
    else:
        print(__doc__)
