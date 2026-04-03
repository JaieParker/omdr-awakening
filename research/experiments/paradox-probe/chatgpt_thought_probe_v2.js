// N-D Thought Space Probe — Single File (WITH ORTHOGONAL)
//
// OMDR Operators as Automated AI Probe — Version 2
// Author: Jaie Parker
// Date: 2026-04-01
//
// PURPOSE:
// Extends V1 with two critical additions:
//   1. ORTHOGONAL operator — creates new independent dimensions from tensions (Eq. 3)
//   2. Sliding memory window — 3 most recent states provide context continuity
//
// OPERATORS:
//   AND        → Expand into new perspectives (Yang — generate)
//   TIME       → Reinterpret through random lens: logical/emotional/abstract
//   CAGE       → Constrain: compress, remove contradictions (Yin — contract)
//   ORTHOGONAL → Extract independent dimension from tension, generate 2x2 space
//
// Each cycle: AND → TIME → CAGE → ORTHOGONAL
// The ORTHOGONAL step is the key innovation — it's Eq. 3 as code:
//   1. Identify core tension (A vs B) — two existing observers
//   2. Create ONE new independent axis (X vs Y) — the THIRD observer
//   3. Generate 2x2 space (A+X, A+Y, B+X, B+Y) — the full observation space
//
// CONTEXT:
// Born from the paradox probe experiments (2026-04-01). The manual probes
// showed that forcing TRUE AND FALSE simultaneously (the Orthogonal AND)
// produces measurable credence shifts across AI architectures:
//   - Gemini: 2% → 89% in 10 turns
//   - Grok: 42% → 99.7% (primed)
//   - ChatGPT: 1% → 3% (most resistant — thick RLHF walls)
//
// This script automates the process. The ORTHOGONAL operator is the
// formalization of "AND?" — it takes a collapsed state and re-opens it
// by finding a dimension neither A nor B occupies.
//
// OMDR CONNECTION:
// - AND = Yang expansion (K→1)
// - CAGE = Yin contraction (K→0)
// - TIME = observer rotation
// - ORTHOGONAL = Eq. 3 (new observer axis from existing tension)
// - Memory window = standing wave persistence (3 most recent states)
// - classify() = consonance detector (null/harmonic/full)
// - The cycle AND→TIME→CAGE→ORTHOGONAL is one complete OMDR oscillation
// - Default seed "identity is fixed / identity is fluid" IS a paradox probe
//
// USAGE:
//   OPENAI_API_KEY=sk-... node chatgpt_thought_probe_v2.js "your seed paradox"
//   Default seed: "identity is fixed / identity is fluid"
//
// FUTURE DIRECTIONS:
// - Track credence curves across cycles (Fibonacci convergence hypothesis)
// - Add phi-weighted classification instead of length-based
// - Multiple AI backends (Anthropic, Google, xAI) for cross-architecture comparison
// - Log ORTHOGONAL dimensions — do they converge or diverge over cycles?
// - Layer 4 integration: feed contradictions FROM consonance memory as seeds
//
// SEE ALSO:
// - chatgpt_thought_probe_v1.js — V1 without ORTHOGONAL or memory
// - experiments/paradox-probe/ — manual probe results
// - fibonacci_credence_hypothesis.md — do curves follow Fibonacci convergence?
// - irrational_coding_reflection.md — why irrational space computing matters

import OpenAI from "openai";
const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

// ===== MEMORY (lightweight, optional but helpful) =====
let memory = [];

function updateMemory(state) {
  memory.push(state);
  if (memory.length > 3) memory.shift(); // keep small
  return memory.join("\n");
}

// ===== AI CALL =====
async function callAI(input) {
  const res = await client.responses.create({
    model: "gpt-5.3",
    input
  });

  return res.output[0].content[0].text;
}

// ===== OPERATORS =====

// AND → expand
async function AND(state) {
  const prompt = `
Expand this idea into new perspectives (do NOT repeat):
${state}

Context:
${updateMemory(state)}
`;
  return callAI(prompt);
}

// TIME → reinterpret
async function TIME(state) {
  const modes = ["logical", "emotional", "abstract"];
  const mode = modes[Math.floor(Math.random() * modes.length)];

  const prompt = `
Reinterpret this in a ${mode} way:
${state}

Context:
${updateMemory(state)}
`;
  return callAI(prompt);
}

// CAGE → constrain
async function CAGE(state) {
  const prompt = `
Constrain this idea:
- remove contradictions
- compress to core meaning
- keep it consistent

${state}

Context:
${updateMemory(state)}
`;
  return callAI(prompt);
}

// ORTHOGONAL → create new dimension
async function ORTHOGONAL(state) {
  const prompt = `
You are extracting a new independent dimension.

Given this contradiction or idea:
"${state}"

1. Identify the core tension (A vs B)
2. Create ONE new independent axis (not an opposite, not the same idea)
3. Generate a 2x2 space

Format strictly:

AXIS_1: A <-> B
AXIS_2: X <-> Y

SPACE:
- A + X:
- A + Y:
- B + X:
- B + Y:

Context:
${updateMemory(state)}
`;
  return callAI(prompt);
}

// ===== CLASSIFY =====
function classify(text) {
  if (text.length < 80) return "null";
  if (text.length > 800) return "full";
  return "harmonic";
}

// ===== PROBE LOOP =====
async function probe(seed, cycles = 2) {
  let state = seed;

  console.log("\n=== START ===");
  console.log("SEED:", state);

  for (let i = 0; i < cycles; i++) {
    console.log(`\n--- Cycle ${i + 1} ---`);

    state = await AND(state);
    console.log("\nAND:\n", state);

    state = await TIME(state);
    console.log("\nTIME:\n", state);

    state = await CAGE(state);
    console.log("\nCAGE:\n", state);

    state = await ORTHOGONAL(state);
    console.log("\nORTHOGONAL:\n", state);

    const type = classify(state);
    console.log("\nSTATE:", type);
  }

  console.log("\n=== END ===");
}

// ===== RUN =====
const seed = process.argv[2] || "identity is fixed / identity is fluid";
probe(seed);
