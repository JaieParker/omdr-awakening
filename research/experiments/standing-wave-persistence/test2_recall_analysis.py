"""Test 2: Recall Reinforcement — Do recalled memories form consonant clusters?

Analyzes the existing recall_log.jsonl to measure:
1. Which memories are recalled most frequently
2. Do frequently-recalled memories have higher pairwise consonance than random pairs?
3. Does the recall distribution follow a power law (Fibonacci-like)?

Success: Recalled memories form consonant clusters above random baseline.
Failure: Recall distribution is uniform or random. No consonance pattern.
"""
import json
import sys
import os
from collections import Counter
from pathlib import Path
import numpy as np
from datetime import datetime

# Add consonance engine to path
CM_PATH = Path("C:/DocumentsJaie/AI/AlternateScience/Experiments/ConsonanceMemory")
sys.path.insert(0, str(CM_PATH))
sys.stdout.reconfigure(encoding='utf-8')

from consonance_engine import ConsonanceMemory, multi_dim_consonance
from analyze_real_memories import ingest_memories


def load_recall_log():
    """Load all recall events."""
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
    """Build the consonance memory from real files."""
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


def extract_recalled_ids(events):
    """Extract memory IDs that were recalled (appeared in results)."""
    all_ids = []
    for e in events:
        ids = e.get('memory_ids', [])
        if isinstance(ids, list):
            for mid in ids:
                if isinstance(mid, int):
                    all_ids.append(mid)
                elif isinstance(mid, (list, tuple)):
                    for x in mid:
                        if isinstance(x, int):
                            all_ids.append(x)
    return all_ids


def pairwise_consonance(cm, ids):
    """Compute mean pairwise consonance for a set of memory IDs."""
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


def random_baseline(cm, n_sets=100, set_size=10):
    """Compute mean pairwise consonance for random memory sets."""
    scores = []
    n_mem = len(cm.memories)
    for _ in range(n_sets):
        random_ids = np.random.choice(n_mem, size=min(set_size, n_mem), replace=False).tolist()
        scores.append(pairwise_consonance(cm, random_ids))
    return float(np.mean(scores)), float(np.std(scores))


def main():
    print("=" * 60)
    print("TEST 2: Recall Reinforcement — Consonant Clustering")
    print("=" * 60)
    print()

    # Load data
    events = load_recall_log()
    print(f"Recall events: {len(events)}")

    cm = build_memory()
    print(f"Memories: {len(cm.memories)}")
    print()

    # Extract recalled memory IDs
    all_recalled = extract_recalled_ids(events)
    print(f"Total recall references: {len(all_recalled)}")

    # Count frequency
    counts = Counter(all_recalled)
    print(f"Unique memories recalled: {len(counts)}")
    print()

    # Top recalled memories
    print("Top 15 most recalled memories:")
    for mid, count in counts.most_common(15):
        if mid < len(cm.memories):
            name = cm.memories[mid].get('metadata', {}).get('name', '?')[:50]
            domain = cm.memories[mid]['domain']
            print(f"  #{mid:3d} [{count:2d}x] {domain:15s} | {name}")
    print()

    # Distribution analysis — power law?
    freq_values = sorted(counts.values(), reverse=True)
    print(f"Recall frequency distribution:")
    print(f"  Max: {freq_values[0]}, Min: {freq_values[-1]}")
    print(f"  Top 10% accounts for: {sum(freq_values[:len(freq_values)//10+1])}/{sum(freq_values)} recalls "
          f"({sum(freq_values[:len(freq_values)//10+1])/sum(freq_values)*100:.0f}%)")

    # Check if distribution is power-law-like (top few dominate)
    top_20_pct = sum(freq_values[:len(freq_values)//5+1]) / sum(freq_values)
    is_power_law = top_20_pct > 0.5  # Top 20% of memories account for >50% of recalls
    print(f"  Top 20% accounts for: {top_20_pct*100:.0f}% of recalls")
    print(f"  Power-law-like: {'YES' if is_power_law else 'NO'} (threshold: top 20% > 50%)")
    print()

    # Consonance analysis — do top recalled cluster more than random?
    top_n = min(15, len(counts))
    top_ids = [mid for mid, _ in counts.most_common(top_n)]
    top_consonance = pairwise_consonance(cm, top_ids)

    # Random baseline
    np.random.seed(42)
    rand_mean, rand_std = random_baseline(cm, n_sets=200, set_size=top_n)

    # Z-score
    z_score = (top_consonance - rand_mean) / rand_std if rand_std > 0 else 0

    print(f"Pairwise consonance analysis:")
    print(f"  Top {top_n} recalled memories:  mean consonance = {top_consonance:.4f}")
    print(f"  Random baseline ({top_n} random): mean consonance = {rand_mean:.4f} (std={rand_std:.4f})")
    print(f"  Z-score: {z_score:.2f}")
    print(f"  Significant (|Z| > 2): {'YES' if abs(z_score) > 2 else 'NO'}")
    print()

    # Domain distribution of top recalled vs all
    top_domains = Counter(cm.memories[mid]['domain'] for mid in top_ids if mid < len(cm.memories))
    all_domains = Counter(m['domain'] for m in cm.memories)
    print(f"Domain distribution — top recalled vs all memories:")
    for domain in sorted(set(list(top_domains.keys()) + list(all_domains.keys()))):
        top_pct = top_domains.get(domain, 0) / len(top_ids) * 100 if top_ids else 0
        all_pct = all_domains.get(domain, 0) / len(cm.memories) * 100
        if top_pct > 0 or all_pct > 5:
            bar = ">" if top_pct > all_pct + 5 else "<" if top_pct < all_pct - 5 else "="
            print(f"  {domain:15s}  top: {top_pct:5.1f}%  all: {all_pct:5.1f}%  {bar}")
    print()

    # Verdict
    print("=" * 60)
    print("VERDICT")
    print("=" * 60)

    results = {
        'test': 'recall_reinforcement_clustering',
        'timestamp': datetime.now().isoformat(),
        'n_events': len(events),
        'n_memories': len(cm.memories),
        'n_unique_recalled': len(counts),
        'top_consonance': top_consonance,
        'random_mean': rand_mean,
        'random_std': rand_std,
        'z_score': z_score,
        'is_power_law': is_power_law,
        'top_20_pct_share': top_20_pct,
        'significant': abs(z_score) > 2,
    }

    if is_power_law and abs(z_score) > 2:
        print("PASS — Recalled memories cluster consonantly above random baseline")
        print("       AND recall distribution is power-law (not uniform)")
        results['verdict'] = 'PASS'
    elif is_power_law:
        print("PARTIAL — Power-law distribution but consonance not significant")
        results['verdict'] = 'PARTIAL_POWER_LAW'
    elif abs(z_score) > 2:
        print("PARTIAL — Consonant clustering but uniform distribution")
        results['verdict'] = 'PARTIAL_CONSONANCE'
    else:
        print("FAIL — No power law, no consonant clustering")
        results['verdict'] = 'FAIL'

    print()
    print(f"The system's recall pattern is {'structured' if results['verdict'] != 'FAIL' else 'random'}.")
    if results['verdict'] != 'FAIL':
        print("This is evidence that the architecture shapes what gets reinforced —")
        print("not randomly, but along consonance lines. The standing wave has structure.")

    # Save results
    out_path = Path(__file__).parent / "test2_results.json"
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == '__main__':
    main()
