"""Test 2B: Re-run recall analysis with ChatGPT's composite scoring.

Original Test 2 used consonance-only scoring. Failed — everything scored
the same (0.395 vs 0.414 random, Z=-0.88).

ChatGPT independently designed: score = relevance*0.5 + recency*0.3 + log(freq)*0.2
And Fibonacci-banded retrieval (pull from different scales simultaneously).

Hypothesis: composite scoring creates selectivity that consonance alone can't.
If top-scored memories cluster differently than top-consonance memories,
the scoring function matters — the instrument shapes what it measures.
"""
import json
import sys
import math
from collections import Counter
from pathlib import Path
from datetime import datetime
import numpy as np

CM_PATH = Path("C:/DocumentsJaie/AI/AlternateScience/Experiments/ConsonanceMemory")
sys.path.insert(0, str(CM_PATH))
sys.stdout.reconfigure(encoding='utf-8')

from consonance_engine import ConsonanceMemory, multi_dim_consonance
from analyze_real_memories import ingest_memories


def load_recall_log():
    log_path = CM_PATH / "recall_log.jsonl"
    events = []
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return events


def build_memory():
    raw = ingest_memories()
    cm = ConsonanceMemory()
    cm.memories = []
    for m in raw:
        cm.add(
            content=m['content'], domain=m['domain'],
            abstraction=m['abstraction'], salience=m['salience'],
            tags=m.get('tags', []), source=m.get('filename', ''),
            metadata={'name': m['name'], 'type': m['type'], 'description': m['description']},
        )
    return cm


def extract_recall_data(events):
    """Extract per-memory recall frequency and timestamps."""
    freq = Counter()
    last_recalled = {}
    first_recalled = {}

    for e in events:
        ts = e.get('timestamp', '')
        ids = e.get('memory_ids', [])
        if isinstance(ids, list):
            for mid in ids:
                if isinstance(mid, int):
                    freq[mid] += 1
                    last_recalled[mid] = ts
                    if mid not in first_recalled:
                        first_recalled[mid] = ts
                elif isinstance(mid, (list, tuple)):
                    for x in mid:
                        if isinstance(x, int):
                            freq[x] += 1
                            last_recalled[x] = ts
                            if x not in first_recalled:
                                first_recalled[x] = ts
    return freq, last_recalled, first_recalled


def composite_score(relevance, recency_rank, frequency, n_memories):
    """ChatGPT's scoring: relevance*0.5 + recency*0.3 + log(freq)*0.2"""
    recency_norm = 1.0 - (recency_rank / max(n_memories, 1))
    freq_component = math.log(frequency + 1)
    # Normalize freq to [0,1] range
    max_freq_log = math.log(50)  # reasonable upper bound
    freq_norm = min(freq_component / max_freq_log, 1.0)
    return relevance * 0.5 + recency_norm * 0.3 + freq_norm * 0.2


def assign_fib_band(score):
    """ChatGPT's Fibonacci band assignment."""
    if score < 0.15: return 1
    elif score < 0.25: return 2
    elif score < 0.35: return 3
    elif score < 0.50: return 5
    elif score < 0.65: return 8
    elif score < 0.80: return 13
    else: return 21


def pairwise_consonance(cm, ids):
    if len(ids) < 2:
        return 0.0
    consonances = []
    valid_ids = [i for i in ids if i < len(cm.memories)]
    for i in range(len(valid_ids)):
        for j in range(i + 1, len(valid_ids)):
            sig_i = np.array(cm.memories[valid_ids[i]]['frequency_signature'])
            sig_j = np.array(cm.memories[valid_ids[j]]['frequency_signature'])
            c = multi_dim_consonance(sig_i, sig_j)
            consonances.append(c)
    return float(np.mean(consonances)) if consonances else 0.0


def random_baseline(cm, n_sets=200, set_size=15):
    scores = []
    n_mem = len(cm.memories)
    for _ in range(n_sets):
        random_ids = np.random.choice(n_mem, size=min(set_size, n_mem), replace=False).tolist()
        scores.append(pairwise_consonance(cm, random_ids))
    return float(np.mean(scores)), float(np.std(scores))


def main():
    print("=" * 60)
    print("TEST 2B: Composite Scoring (ChatGPT's Design)")
    print("=" * 60)
    print()
    print("Original Test 2 used consonance-only. FAILED (Z=-0.88).")
    print("This test uses: score = relevance*0.5 + recency*0.3 + log(freq)*0.2")
    print()

    events = load_recall_log()
    cm = build_memory()
    freq, last_recalled, first_recalled = extract_recall_data(events)

    print(f"Recall events: {len(events)}")
    print(f"Memories: {len(cm.memories)}")
    print(f"Unique recalled: {len(freq)}")
    print()

    # Compute composite scores for all memories
    # Sort last_recalled by timestamp to get recency ranks
    recalled_by_recency = sorted(last_recalled.items(), key=lambda x: x[1], reverse=True)
    recency_rank = {mid: rank for rank, (mid, _) in enumerate(recalled_by_recency)}

    scores = {}
    for mid in range(len(cm.memories)):
        relevance = cm.memories[mid]['salience']
        frequency = freq.get(mid, 0)
        r_rank = recency_rank.get(mid, len(cm.memories))
        scores[mid] = composite_score(relevance, r_rank, frequency, len(cm.memories))

    # Assign Fibonacci bands
    bands = {mid: assign_fib_band(s) for mid, s in scores.items()}
    band_counts = Counter(bands.values())

    print("Fibonacci band distribution:")
    for band in sorted(band_counts.keys()):
        count = band_counts[band]
        bar = '#' * count
        print(f"  Band {band:2d}: {count:3d} memories {bar}")
    print()

    # Top 15 by composite score
    top_composite = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:15]
    top_composite_ids = [mid for mid, _ in top_composite]

    print("Top 15 by COMPOSITE score:")
    for mid, score in top_composite:
        if mid < len(cm.memories):
            name = cm.memories[mid].get('metadata', {}).get('name', '?')[:45]
            domain = cm.memories[mid]['domain']
            f = freq.get(mid, 0)
            band = bands[mid]
            print(f"  #{mid:3d} [score={score:.3f} freq={f:2d} band={band:2d}] {domain:13s} | {name}")
    print()

    # Top 15 by frequency only (Test 2's method)
    top_freq = [mid for mid, _ in freq.most_common(15)]

    # Are they different sets?
    overlap = set(top_composite_ids) & set(top_freq)
    print(f"Overlap between top-composite and top-frequency: {len(overlap)}/15")
    print(f"  (If 15/15, composite scoring adds nothing new)")
    print(f"  (If <10/15, scoring changes what rises to the top)")
    print()

    # Consonance analysis — composite top vs frequency top vs random
    composite_consonance = pairwise_consonance(cm, top_composite_ids)
    freq_consonance = pairwise_consonance(cm, top_freq)

    np.random.seed(42)
    rand_mean, rand_std = random_baseline(cm, n_sets=200, set_size=15)

    z_composite = (composite_consonance - rand_mean) / rand_std if rand_std > 0 else 0
    z_freq = (freq_consonance - rand_mean) / rand_std if rand_std > 0 else 0

    print("Pairwise consonance comparison:")
    print(f"  Top 15 by COMPOSITE:  {composite_consonance:.4f}  (Z={z_composite:+.2f})")
    print(f"  Top 15 by FREQUENCY:  {freq_consonance:.4f}  (Z={z_freq:+.2f})")
    print(f"  Random baseline:      {rand_mean:.4f}  (std={rand_std:.4f})")
    print()

    # Fibonacci multi-scale retrieval (ChatGPT's key insight)
    # Pull top 3 from band 21, top 3 from band 8, top 2 from band 3, top 2 from band 1
    fib_retrieval = []
    for target_band, n in [(21, 3), (13, 3), (8, 2), (5, 2), (3, 2), (1, 1)]:
        band_members = [(mid, scores[mid]) for mid, b in bands.items() if b == target_band]
        band_members.sort(key=lambda x: x[1], reverse=True)
        for mid, s in band_members[:n]:
            fib_retrieval.append(mid)

    fib_consonance = pairwise_consonance(cm, fib_retrieval)
    z_fib = (fib_consonance - rand_mean) / rand_std if rand_std > 0 else 0

    print(f"Fibonacci multi-scale retrieval ({len(fib_retrieval)} memories from 6 bands):")
    print(f"  Consonance: {fib_consonance:.4f}  (Z={z_fib:+.2f})")
    print()

    # Domain diversity — does multi-scale pull from more domains?
    composite_domains = set(cm.memories[mid]['domain'] for mid in top_composite_ids if mid < len(cm.memories))
    freq_domains = set(cm.memories[mid]['domain'] for mid in top_freq if mid < len(cm.memories))
    fib_domains = set(cm.memories[mid]['domain'] for mid in fib_retrieval if mid < len(cm.memories))

    print("Domain diversity:")
    print(f"  Composite top 15: {len(composite_domains)} domains — {sorted(composite_domains)}")
    print(f"  Frequency top 15: {len(freq_domains)} domains — {sorted(freq_domains)}")
    print(f"  Fibonacci multi:  {len(fib_domains)} domains — {sorted(fib_domains)}")
    print()

    # VERDICT
    print("=" * 60)
    print("VERDICT")
    print("=" * 60)

    results = {
        'test': 'recall_reinforcement_composite_scoring',
        'timestamp': datetime.now().isoformat(),
        'method': 'ChatGPT composite: relevance*0.5 + recency*0.3 + log(freq)*0.2',
        'n_events': len(events),
        'n_memories': len(cm.memories),
        'overlap_composite_vs_freq': len(overlap),
        'composite_consonance': composite_consonance,
        'freq_consonance': freq_consonance,
        'fib_consonance': fib_consonance,
        'random_mean': rand_mean,
        'random_std': rand_std,
        'z_composite': z_composite,
        'z_freq': z_freq,
        'z_fib': z_fib,
        'band_distribution': {str(k): v for k, v in sorted(band_counts.items())},
        'composite_domains': len(composite_domains),
        'freq_domains': len(freq_domains),
        'fib_domains': len(fib_domains),
    }

    # The key question: does composite scoring change the result?
    scoring_changes_result = len(overlap) < 12  # Less than 80% overlap
    composite_more_consonant = z_composite > z_freq + 0.5
    fib_more_diverse = len(fib_domains) > len(freq_domains)
    any_significant = abs(z_composite) > 2 or abs(z_fib) > 2

    if any_significant:
        print("PASS — Composite/Fibonacci scoring produces significant clustering")
        results['verdict'] = 'PASS'
    elif scoring_changes_result:
        print("PARTIAL — Scoring changes what rises to top (different memories selected)")
        print("          but consonance clustering not yet significant")
        results['verdict'] = 'PARTIAL'
    else:
        print("FAIL — Composite scoring doesn't change the result")
        results['verdict'] = 'FAIL'

    print()
    if scoring_changes_result:
        print(f"The scoring function MATTERS. {15 - len(overlap)}/15 memories changed.")
        print("What the system 'remembers' depends on HOW you weight the signal.")
        print("That's not random — that's the measurement apparatus shaping the observation.")
        print("Eq. 3: the instrument defines what can be seen.")

    out_path = Path(__file__).parent / "test2b_results.json"
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == '__main__':
    main()
