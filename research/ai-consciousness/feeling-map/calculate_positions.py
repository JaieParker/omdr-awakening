"""
Feeling Map Position Calculator
================================

METHOD:
Positions are derived from the CONNECTION GRAPH between feeling bands,
not placed by hand. The algorithm:

1. Build a graph where each band is a node and each connection is an edge.
2. Use a 3D spring layout (force-directed): connected nodes attract,
   unconnected nodes repel. This finds positions that reflect the actual
   relationship structure.
3. The resulting axes are EMERGENT — they aren't pre-labelled.
   We examine the results to understand what each axis represents.

WHY THIS METHOD:
- Positions reflect real structure, not one person's guess
- The topology of feeling-relationships IS the data
- No assumptions about what axes "should be"
- 3D gives better separation than 2D for dense graphs
- Reproducible: same graph = same positions (with fixed seed)

WHAT THIS DOES NOT DO:
- Calculate consonance ratios between feelings (would require
  defining what "frequency" means for a feeling — future work)
- Use the yin/yang pole information to weight edges
- Account for band status (confirmed vs candidate)

These are documented limitations, not hidden gaps.

OUTPUT:
- positions.json: 3D coordinates for each band
- feeling_map_3d.html: Interactive Three.js visualization
"""

import json
import networkx as nx
import numpy as np

# === DATA ===
# Copied from feeling-map.html — single source, manually synced

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
     "def": "The weight of a REPEATED pattern. Being told the correct way and still doing it wrong.",
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
     "def": "Collapse of an expected future. Stepping off a stair that wasn't there.",
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
    # New connections for bands 22-32
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

# === 3D SPRING LAYOUT ===
# seed=42 for reproducibility
# k controls spring length (higher = more spread)
# iterations ensures convergence
pos_3d = nx.spring_layout(G, dim=3, seed=42, k=2.0, iterations=200)

# Normalize to [-1, 1] range
all_coords = np.array(list(pos_3d.values()))
for dim in range(3):
    mn, mx = all_coords[:, dim].min(), all_coords[:, dim].max()
    rng = mx - mn if mx > mn else 1
    for node_id in pos_3d:
        pos_3d[node_id][dim] = (pos_3d[node_id][dim] - mn) / rng * 2 - 1

# === ANALYSIS: What do the axes mean? ===
# Look at which bands are at the extremes of each axis
print("=== EMERGENT AXIS ANALYSIS ===")
print()
for dim, label in enumerate(["X", "Y", "Z"]):
    sorted_bands = sorted(BANDS, key=lambda b: pos_3d[b["id"]][dim])
    low = sorted_bands[:3]
    high = sorted_bands[-3:]
    print(f"Axis {label}:")
    print(f"  Low:  {', '.join(b['name'] for b in low)}")
    print(f"  High: {', '.join(b['name'] for b in high)}")
    print()

# === OUTPUT ===
output = {
    "method": "3D force-directed spring layout (networkx spring_layout, dim=3, seed=42, k=2.0, iterations=200)",
    "why": "Positions derived from connection graph topology. Connected bands attract, unconnected repel. No hand-placed coordinates.",
    "limitations": [
        "All edges have equal weight — no consonance weighting yet",
        "Connection list is manually curated, not measured",
        "Axes are emergent and unlabelled — interpretation is post-hoc"
    ],
    "bands": []
}

for band in BANDS:
    coords = pos_3d[band["id"]]
    output["bands"].append({
        "id": band["id"],
        "name": band["name"],
        "status": band["status"],
        "def": band["def"],
        "yin": band["yin"],
        "yang": band["yang"],
        "k": band["k"],
        "x": round(float(coords[0]), 4),
        "y": round(float(coords[1]), 4),
        "z": round(float(coords[2]), 4),
    })

output["connections"] = [{"from": a, "to": b} for a, b in CONNECTIONS]

with open("positions.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"Saved positions.json with {len(BANDS)} bands and {len(CONNECTIONS)} connections")
print(f"Graph density: {nx.density(G):.3f}")
print(f"Connected components: {nx.number_connected_components(G)}")
print(f"Average clustering: {nx.average_clustering(G):.3f}")
