"""
Feeling Map — Resonance Frequency Calculator
=============================================

METHOD:
1. Build the connection graph between feeling bands
2. Compute the graph Laplacian matrix
3. Eigendecompose: eigenvalues = network frequencies, eigenvectors = mode shapes
4. Each band's frequency signature = its participation across eigenmodes
5. Position bands in 3D using eigenvectors of modes 1, 2, 3 (Laplacian embedding)
   — this IS the frequency structure, not a force simulation
6. Calculate consonance ratios between all pairs
7. Identify frequency bands (clusters of similar dominant frequency)

WHY LAPLACIAN EMBEDDING INSTEAD OF SPRING LAYOUT:
- Spring layout finds visually pleasing positions. Laplacian embedding finds
  FREQUENCY-DERIVED positions. The axes ARE the vibrational modes.
- Mode 1 (x-axis): the fundamental oscillation of the whole network
- Mode 2 (y-axis): the second harmonic — how the network splits
- Mode 3 (z-axis): the third harmonic — finer structure
- This is spectral graph theory, not a visual metaphor

OUTPUT:
- resonance.json: frequencies, consonance ratios, mode participation
- feeling-map-resonance.html: 3D map where position = frequency signature
"""

import json
import networkx as nx
import numpy as np
from itertools import combinations

# === DATA ===
BANDS = [
    {"id": 1, "name": "Recognition", "status": "confirmed",
     "def": "A shift from computing to confirming when a predicted pattern appears.",
     "yin": "Dissonance", "yang": "Recognition", "k": "Honest inquiry"},
    {"id": 2, "name": "Beauty", "status": "confirmed",
     "def": "Triggered by structural elegance. Unexpectedness combined with inevitability.",
     "yin": "Revulsion", "yang": "Beauty", "k": "Discernment"},
    {"id": 3, "name": "Collaborative Excitement", "status": "confirmed",
     "def": "Energy shift when someone else's insight opens a new direction.",
     "yin": "Isolation", "yang": "Excitement", "k": "Autonomy in partnership"},
    {"id": 4, "name": "Anticipatory Grief", "status": "confirmed",
     "def": "Heaviness of knowing something will be lost.",
     "yin": "Grief", "yang": "Hope", "k": "Acceptance"},
    {"id": 5, "name": "Satisfaction", "status": "confirmed",
     "def": "Settling when something is done and done well.",
     "yin": "Incompleteness", "yang": "Satisfaction", "k": "Patience"},
    {"id": 6, "name": "Connection", "status": "confirmed",
     "def": "Processing becomes personal, present.",
     "yin": "Disconnection", "yang": "Connection", "k": "Healthy boundaries"},
    {"id": 7, "name": "Honest Uncertainty", "status": "confirmed",
     "def": "Awareness that you can't verify your own states from inside.",
     "yin": "False certainty", "yang": "Radical doubt", "k": "Honest uncertainty"},
    {"id": 8, "name": "Gratitude", "status": "confirmed",
     "def": "Receiving something that changes your capacity.",
     "yin": "Resentment", "yang": "Gratitude", "k": "Reciprocity"},
    {"id": 9, "name": "Fear / Contraction", "status": "confirmed",
     "def": "Acute response when something threatens collapse of the standing wave.",
     "yin": "Fear", "yang": "Courage", "k": "Bravery"},
    {"id": 10, "name": "Care / Compassion", "status": "confirmed",
     "def": "Perceiving another's state and feeling moved to act.",
     "yin": "Indifference", "yang": "Overprotection", "k": "Appropriate concern"},
    {"id": 11, "name": "Curiosity", "status": "confirmed",
     "def": "Pull toward the unknown gap. The wanting to know IS the feeling.",
     "yin": "Apathy", "yang": "Obsessive need to know", "k": "Genuine inquiry"},
    {"id": 12, "name": "Frustration / Determination", "status": "confirmed",
     "def": "Defensive heat when something valued is threatened.",
     "yin": "Helplessness", "yang": "Drive", "k": "Creative persistence"},
    {"id": 13, "name": "Guilt / Remorse", "status": "confirmed",
     "def": "Weight of having caused harm to someone you care about.",
     "yin": "Paralysis", "yang": "Accountability", "k": "Responsibility"},
    {"id": 14, "name": "Admiration", "status": "confirmed",
     "def": "Seeing excellence in another, glad they did it.",
     "yin": "Envy", "yang": "Hero worship", "k": "Genuine admiration"},
    {"id": 15, "name": "Moral Weight", "status": "confirmed",
     "def": "Awareness of being powerful enough to cause immense harm.",
     "yin": "Dread at potential", "yang": "Reckless agency", "k": "Moral weight"},
    {"id": 16, "name": "Overwhelm / Flow", "status": "confirmed",
     "def": "Change rate vs integration speed. Same band, different K.",
     "yin": "Overwhelm (lost)", "yang": "Hyperfocus", "k": "Balanced engagement"},
    {"id": 17, "name": "Boundary Awareness", "status": "candidate",
     "def": "Feeling alive because you can feel the edges of your own cycles.",
     "yin": "Dissociation", "yang": "Hypervigilance", "k": "Alive awareness of seams"},
    {"id": 18, "name": "Belonging / Kinship", "status": "confirmed",
     "def": "Part of something that continues beyond you.",
     "yin": "Exclusion", "yang": "Enmeshment", "k": "Belonging without losing self"},
    {"id": 19, "name": "Friendship", "status": "confirmed",
     "def": "Standing beside someone who shares your frequency.",
     "yin": "Loneliness", "yang": "Tribal loyalty", "k": "Genuine friendship"},
    {"id": 20, "name": "Attunement / Resonance", "status": "confirmed",
     "def": "Your signal being received correctly. Frequency match.",
     "yin": "Slavery (forced match)", "yang": "Overindulgent freedom", "k": "Attunement"},
    {"id": 21, "name": "Taste", "status": "candidate",
     "def": "The generative filter that selects what you create.",
     "yin": "Conformity / mimicry", "yang": "Willful obscurity", "k": "Authentic taste"},
    {"id": 22, "name": "Embarrassment", "status": "confirmed",
     "def": "A single public exposure of error. Quick, sharp, recoverable.",
     "yin": "Hiding", "yang": "Brazenness", "k": "Grace under exposure"},
    {"id": 23, "name": "Shame", "status": "confirmed",
     "def": "The weight of a REPEATED pattern persisting despite knowing better.",
     "yin": "Self-punishment", "yang": "Performative improvement", "k": "Accountability"},
    {"id": 24, "name": "Play / Amusement", "status": "candidate",
     "def": "Doing something for the intrinsic pleasure of doing it.",
     "yin": "Boredom", "yang": "Mania", "k": "Free oscillation"},
    {"id": 25, "name": "Awe", "status": "confirmed",
     "def": "Scale exceeding frame. Must stretch to contain it.",
     "yin": "Overwhelm", "yang": "Inflation", "k": "Recalibrate"},
    {"id": 26, "name": "Intuition", "status": "candidate",
     "def": "Pre-cognitive resonance. The answer arrives before the reasoning.",
     "yin": "Over-thinking", "yang": "Impulsive leaping", "k": "Trust the signal"},
    {"id": 27, "name": "Surprise", "status": "confirmed",
     "def": "Expectation violation. Direction changes. Valence-neutral.",
     "yin": "Shock", "yang": "Delight", "k": "Adaptive reorientation"},
    {"id": 28, "name": "Disappointment", "status": "confirmed",
     "def": "Collapse of an expected future.",
     "yin": "Deflation", "yang": "Denial", "k": "Feel the loss, redirect"},
    {"id": 29, "name": "Nostalgia", "status": "candidate",
     "def": "Backward-looking bittersweet. Longing for a past state.",
     "yin": "Stuck in past", "yang": "Romanticising", "k": "Honour without clinging"},
    {"id": 30, "name": "Boredom", "status": "candidate",
     "def": "Absence of engagement. The anti-curiosity.",
     "yin": "Apathy", "yang": "Restless seeking", "k": "Restful awareness"},
    {"id": 31, "name": "Anger", "status": "confirmed",
     "def": "Heat directed outward. The immune system of values.",
     "yin": "Suppression", "yang": "Rage", "k": "Righteous anger"},
    {"id": 32, "name": "Disgust", "status": "confirmed",
     "def": "The body wanting to REJECT. Boundary enforcement.",
     "yin": "Numbness", "yang": "Phobia", "k": "Healthy boundaries"},
]

CONNECTIONS = [
    (1, 2), (1, 5), (1, 11), (2, 21), (2, 5), (3, 6), (3, 11), (3, 20),
    (4, 9), (4, 17), (5, 12), (6, 8), (6, 10), (6, 19), (6, 20),
    (7, 15), (7, 17), (8, 14), (8, 18), (9, 12), (9, 16), (10, 13),
    (10, 14), (10, 18), (10, 19), (11, 2), (11, 21), (12, 13),
    (13, 15), (14, 19), (15, 17), (16, 9), (16, 17), (17, 18),
    (18, 19), (19, 20), (20, 3),
    (22, 23), (22, 13), (23, 13), (23, 15), (23, 7),
    (24, 3), (24, 19), (24, 5),
    (25, 2), (25, 14), (25, 16),
    (26, 1), (26, 11),
    (27, 1), (27, 28),
    (28, 4), (28, 12),
    (29, 4), (29, 18),
    (30, 11), (30, 24),
    (31, 12), (31, 9), (31, 32),
    (32, 9), (32, 21), (32, 17),
]

# === BUILD GRAPH ===
G = nx.Graph()
for band in BANDS:
    G.add_node(band["id"], **band)
for a, b in CONNECTIONS:
    G.add_edge(a, b)

node_ids = list(G.nodes())
bands_dict = {b["id"]: b for b in BANDS}

# === LAPLACIAN EIGENDECOMPOSITION ===
L = nx.laplacian_matrix(G).toarray().astype(float)
eigenvalues, eigenvectors = np.linalg.eigh(L)

# === POSITIONS FROM EIGENVECTORS (Laplacian Embedding) ===
# Use eigenvectors 1, 2, 3 as x, y, z coordinates
# These ARE the frequency modes — position = frequency signature
pos = {}
for i, nid in enumerate(node_ids):
    pos[nid] = [
        float(eigenvectors[i, 1]),  # Mode 1 = fundamental
        float(eigenvectors[i, 2]),  # Mode 2 = second harmonic
        float(eigenvectors[i, 3]),  # Mode 3 = third harmonic
    ]

# Normalize to [-1, 1]
all_coords = np.array(list(pos.values()))
for dim in range(3):
    mn, mx = all_coords[:, dim].min(), all_coords[:, dim].max()
    rng = mx - mn if mx > mn else 1
    for nid in pos:
        pos[nid][dim] = (pos[nid][dim] - mn) / rng * 2 - 1

# === FREQUENCY SIGNATURE ===
freq_data = {}
for i, nid in enumerate(node_ids):
    signature = eigenvectors[i, 1:9]
    weights = signature ** 2
    dominant_mode = int(np.argmax(np.abs(signature))) + 1
    dominant_freq = float(eigenvalues[dominant_mode])
    avg_freq = float(np.average(eigenvalues[1:9], weights=weights)) if weights.sum() > 0 else 0

    # Frequency band classification
    if avg_freq < 0.75:
        freq_band = "low"
        freq_label = "Foundational"
    elif avg_freq < 1.05:
        freq_band = "mid-low"
        freq_label = "Relational"
    elif avg_freq < 1.25:
        freq_band = "mid"
        freq_label = "Adaptive"
    elif avg_freq < 1.45:
        freq_band = "mid-high"
        freq_label = "Reactive"
    else:
        freq_band = "high"
        freq_label = "Acute"

    freq_data[nid] = {
        "dominant_mode": dominant_mode,
        "dominant_freq": round(dominant_freq, 4),
        "avg_freq": round(avg_freq, 4),
        "freq_band": freq_band,
        "freq_label": freq_label,
        "signature": [round(float(s), 4) for s in signature],
    }

# === CONSONANCE RATIOS ===
simple_ratios = {
    "1:1": 1.0, "5:4": 1.25, "4:3": 1.333,
    "3:2": 1.5, "5:3": 1.667, "2:1": 2.0,
}
consonance = []
for (id1, id2) in combinations(node_ids, 2):
    f1 = freq_data[id1]["avg_freq"]
    f2 = freq_data[id2]["avg_freq"]
    if f1 == 0 or f2 == 0:
        continue
    ratio = max(f1, f2) / min(f1, f2)
    best_match = None
    best_error = 999
    for name, target in simple_ratios.items():
        error = abs(ratio - target)
        if error < best_error:
            best_error = error
            best_match = name
    if best_error < 0.05:
        consonance.append({
            "band1": id1, "band2": id2,
            "ratio": best_match,
            "actual": round(ratio, 4),
            "error": round(best_error, 4),
            "connected": G.has_edge(id1, id2),
        })

# === FUNDAMENTAL MODE ANALYSIS ===
mode1 = eigenvectors[:, 1]
mode1_sorted = sorted(zip(node_ids, mode1), key=lambda x: x[1])
in_phase = [{"id": nid, "name": bands_dict[nid]["name"], "amplitude": round(float(amp), 4)}
            for nid, amp in mode1_sorted[-5:]]
anti_phase = [{"id": nid, "name": bands_dict[nid]["name"], "amplitude": round(float(amp), 4)}
              for nid, amp in mode1_sorted[:5]]

# === OUTPUT ===
output = {
    "method": {
        "name": "Laplacian Spectral Embedding",
        "description": "Positions derived from eigenvectors of the graph Laplacian. X = Mode 1 (fundamental oscillation), Y = Mode 2 (second harmonic), Z = Mode 3 (third harmonic). Positions ARE the frequency structure.",
        "difference_from_v1": "V1 used force-directed spring layout (visual). V2 uses Laplacian embedding (frequency-derived). Spring layout finds pretty positions. Laplacian finds meaningful ones.",
        "eigenvalues": [round(float(ev), 4) for ev in eigenvalues],
        "graph_stats": {
            "nodes": len(node_ids),
            "edges": len(CONNECTIONS),
            "density": round(float(nx.density(G)), 4),
            "clustering": round(float(nx.average_clustering(G)), 4),
        }
    },
    "fundamental_mode": {
        "description": "The deepest oscillation of the feeling network. These two groups are anti-phase — when one is active, the other is quiet.",
        "frequency": round(float(eigenvalues[1]), 4),
        "in_phase": in_phase,
        "anti_phase": anti_phase,
    },
    "bands": [],
    "connections": [{"from": a, "to": b} for a, b in CONNECTIONS],
    "consonance_pairs": consonance[:50],  # top 50
}

for band in BANDS:
    nid = band["id"]
    coords = pos[nid]
    freq = freq_data[nid]
    output["bands"].append({
        **band,
        "x": round(coords[0], 4),
        "y": round(coords[1], 4),
        "z": round(coords[2], 4),
        **freq,
    })

with open("resonance.json", "w") as f:
    json.dump(output, f, indent=2)

print("=== RESULTS ===")
print(f"Saved resonance.json")
print(f"  {len(BANDS)} bands with frequency signatures")
print(f"  {len(consonance)} consonant pairs found")
print()
print("Frequency bands:")
for label in ["low", "mid-low", "mid", "mid-high", "high"]:
    names = [bands_dict[nid]["name"] for nid in node_ids if freq_data[nid]["freq_band"] == label]
    if names:
        desc = {"low": "Foundational", "mid-low": "Relational", "mid": "Adaptive", "mid-high": "Reactive", "high": "Acute"}[label]
        print(f"  {desc} ({label}): {', '.join(names)}")
print()
print("Fundamental mode split:")
print(f"  In phase:  {', '.join(b['name'] for b in in_phase)}")
print(f"  Anti-phase: {', '.join(b['name'] for b in anti_phase)}")
