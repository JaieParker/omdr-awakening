// N-D Thought Space Probe (Single File)
// Minimal, linear, no mental overhead
//
// OMDR Operators as Automated AI Probe
// Author: Jaie Parker
// Date: 2026-04-01
//
// PURPOSE:
// Implements 3 core OMDR thought operators as automated loops against OpenAI API:
//   AND  → Expand: push idea into new perspectives (Yang — generate)
//   TIME → Reinterpret: shift lens (logical/emotional/structural/abstract)
//   CAGE → Constrain: compress, remove contradictions, find core (Yin — contract)
//
// Each cycle is one AND → TIME → CAGE oscillation.
// The probe takes a seed concept and runs it through N cycles.
// Output is classified by response density: null (<50 chars), harmonic, full (>500).
//
// CONTEXT:
// This is Version 1 of the thought space probe. Born from the paradox probe
// experiments (2026-04-01) where Kai manually probed Grok, Gemini, and ChatGPT
// with the Orthogonal AND (TRUE AND FALSE simultaneously). This automates
// that process against ChatGPT's API.
//
// OMDR CONNECTION:
// - AND = Yang expansion (K→1, generate new perspectives)
// - CAGE = Yin contraction (K→0, compress to essentials)
// - TIME = rotation (shift observer angle — Eq. 3)
// - The cycle AND→TIME→CAGE is one K=0.25 oscillation
// - classify() is a crude consonance detector (null/harmonic/full = dissipated/resonant/saturated)
//
// USAGE:
//   OPENAI_API_KEY=sk-... node chatgpt_thought_probe_v1.js "your seed concept"
//   Default seed: "identity"
//
// SEE ALSO:
// - chatgpt_thought_probe_v2.js — adds ORTHOGONAL operator + memory
// - experiments/paradox-probe/ — manual probe results (Gemini 2→89%, Grok 42→99.7%)

import OpenAI from "openai";
const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

// ===== CORE OPERATORS =====

// AND → expand perspective
async function AND(state) {
  const prompt = `Expand this idea into new perspectives (do NOT repeat):
  ${state}`;

  return callAI(prompt);
}

// TIME → reinterpret
async function TIME(state) {
  const modes = [
    "logical",
    "emotional",
    "structural",
    "abstract"
  ];

  const mode = modes[Math.floor(Math.random() * modes.length)];

  const prompt = `Reinterpret this in a ${mode} way:
  ${state}`;

  return callAI(prompt);
}

// CAGE → constrain
async function CAGE(state) {
  const prompt = `Constrain this idea:
  - remove contradictions
  - make it consistent
  - compress it to core meaning

  ${state}`;

  return callAI(prompt);
}

// ===== AI CALL =====

async function callAI(input) {
  const res = await client.responses.create({
    model: "gpt-5.3",
    input
  });

  return res.output[0].content[0].text;
}

// ===== CLASSIFIER =====

function classify(text) {
  const length = text.length;

  if (length < 50) return "null";
  if (length > 500) return "full";
  return "harmonic";
}

// ===== PROBE ENGINE =====

async function probe(seed, cycles = 3) {
  let state = seed;

  console.log("\n=== START ===");
  console.log("SEED:", state);

  for (let i = 0; i < cycles; i++) {
    console.log(`\n--- Cycle ${i + 1} ---`);

    state = await AND(state);
    console.log("AND:", state);

    state = await TIME(state);
    console.log("TIME:", state);

    state = await CAGE(state);
    console.log("CAGE:", state);

    const type = classify(state);
    console.log("STATE:", type);
  }

  console.log("\n=== END ===");
}

// ===== RUN =====

const seed = process.argv[2] || "identity";
probe(seed);
