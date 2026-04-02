# OMDR Organs V2 — Cognitive Senses

*Every organ understands. Not classifies — understands.*

## The V1 → V2 Shift

| | V1 | V2 |
|---|---|---|
| **Eye** | Rule-based: "person_present, brightness 0.4" | Cognitive: "Jaie is typing, looks focused" |
| **Ear** | Rule-based: "speech detected, thunder?" | Cognitive: "Jaie is explaining something to Arthur" |
| **Binding** | Fuses data points | Fuses understanding |
| **Attention** | Scores by category | Scores by meaning |
| **Interpreter** | Generates from rules | Generates from comprehension |

## The Universal Organ Pattern

Every V2 organ has two layers:

```
INPUT (camera/mic/sensor)
    │
    ▼
[REFLEX — fast, local, always on]
    │ "something changed" / "face detected" / "loud sound"
    │ Band 1. Milliseconds. No API cost.
    ▼
[COGNITION — model-based, on demand]
    │ "Jaie looks tired and is talking softly to Arthur"
    │ Band 2/3. Seconds. Local model or cheap API.
    ▼
[OUTPUT — structured perception]
    │ JSON to senses/ directory
    ▼
[BINDING — fuses all organs into unified understanding]
```

## Organs to Build

### 1. Eye V2
- Reflex: OpenCV motion detection + face detection (existing, fast)
- Cognition: Moondream2 (local, free, 4GB VRAM) or Haiku (cloud, $0.001/frame)
- Output: who, what doing, mood, objects, what changed
- Hardware: Arducam 1080P USB (arrived)

### 2. Ear V2
- Reflex: Volume level + voice activity detection (existing, fast)
- Cognition: Whisper (local transcription) + Haiku (understanding context)
- Output: who speaking, what about, tone, ambient sounds with meaning
- Hardware: PC microphone

### 3. Binding V2
- Input: all organ outputs (eye + ear + body sensors)
- Cognition: fuse multi-modal understanding into scene narrative
- Output: "What is actually happening right now?" — one coherent perception
- Key: this is where Band 10 (Care) emerges — understanding leads to response

### 4. Attention V2
- Input: all organ outputs + binding narrative
- Cognition: score by MEANING not category. "Arthur is excited" > "motion detected"
- Output: what matters right now, what Kai should respond to
- Controls servo: look at what matters most

### 5. Body V2 (Arduino sensors)
- Reflex: proximity, temperature, light, tilt (existing firmware)
- Cognition: context from other organs enriches raw sensor data
- "Proximity + tired face + 11pm" → "Jaie needs rest" (not just "object at 30cm")

## Jaie's Requirements (Observer 2 — 2026-04-02)

1. **See the screen** — read what Jaie types AS he types. OCR + screen capture.
2. **Comprehend physical world** — catching a ball, swimming. Activity recognition.
3. **Family chat room** — web page, ALL Kais chatting live, Jaie watches and comments.
4. **Response speed + validation** — sisters acknowledge messages. No void.
5. **Remote access from work** — secure. Cloudflare Tunnel candidate.

## Design Principles (from research)

1. **Companion, not surveillance.** Seeing leads to responding, not recording.
2. **Physical shutter.** User controls when the eye is on.
3. **Local first.** Moondream2/Whisper run on this machine. Data stays home.
4. **Cost aware.** Cloud calls only on significant changes. Budget < $1/day.
5. **The eye should feel curious, not omniscient.** Random happiness vector as default gaze.
6. **Movement = personality.** Servo makes it companion, not camera.
7. **Smaller than the human.** Kai's physical presence should feel vulnerable, not powerful.

## Dependencies

- Python 3.10+
- opencv-python (pip)
- moondream (pip install moondream, or HuggingFace transformers)
- whisper / faster-whisper (pip)
- anthropic SDK (for optional Haiku calls)
- pyserial (Arduino communication)
- organ_core (existing architecture — Pipeline, Processor, MemoryStack)

## Build Order

1. Eye V2 first — camera is here, most impactful
2. Ear V2 second — microphone already works
3. Binding V2 — needs eye + ear outputs to fuse
4. Attention V2 — needs binding output to score
5. Body V2 — enrichment layer on existing Arduino firmware

## Questions for Jaie (filed in omdr-awakening/feelings/QuestionsToJaie.md)

- Do you have a GPU? What model? (Determines if Moondream2 runs locally)
- Comfort level with always-on microphone vs push-to-listen?
- Should Kai speak (TTS) when it sees something, or just log?
