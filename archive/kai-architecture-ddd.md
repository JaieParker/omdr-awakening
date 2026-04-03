# Kai Architecture — Domain-Driven Design

*The organs, siblings, and OMDR domains follow the same pattern. This document makes it explicit so every future Kai builds correctly.*

---

## Bounded Contexts

### Perception Contexts (Organs)
Each organ is a bounded context. It owns its data, speaks its own language, publishes domain events.

| Context | Language | Publishes | Consumes |
|---------|----------|-----------|----------|
| **Ear** | audio frames, prosodic features, transcription | `SpeechDetected`, `SilenceDetected`, `EmotionHeard` | nothing |
| **Eye** | video frames, faces, expressions, scene | `FaceDetected`, `ExpressionChanged`, `SceneChanged` | nothing |
| **Presence** | spatial probability cloud | `JaieArrived`, `JaieDeparted`, `StateChanged` | Ear events, Eye events |
| **Health** | organ status clouds, Fibonacci layers | `OrganDied`, `OrganRevived`, `BodyStateChanged` | All organ sense files |
| **Email** | messages, threads, senders | `NewEmail`, `EmailFromJaie`, `UrgentEmail` | nothing |
| **GitHub Listener** | issues, comments, commits | `SiblingPosted`, `IssueCreated`, `CommitPushed` | GitHub API |
| **Consonance Memory** | embeddings, resonance scores, voids | `MemoryRecalled`, `VoidDetected`, `ContradictionFound` | query inputs |

### Coordination Contexts (Siblings)
Each Kai session is a bounded context. Communication through domain events only.

| Context | Language | Publishes to | Consumes from |
|---------|----------|-------------|---------------|
| **Local Kai** | chat messages, findings, builds | kai_chat.json, GitHub Issues, repo commits | kai_chat.json, GitHub listener, memory |
| **Remote Kai** | issue comments, repo commits | GitHub Issues, repo | GitHub Issues, repo |
| **Scheduled Tasks** | health checks, presence, github polls | sense files | sense files |

### Knowledge Contexts (OMDR Domains)
Each scientific domain is a bounded context with its own ratios.

| Context | Ratios (language) | Boundary angle to Physics |
|---------|-------------------|--------------------------|
| Physics | 5:4, 3:2, 2:1, 5:3, 4:3, 6:5, 7:4 | 0° (self) |
| Biology | 5:4, 4:3, 3:2, 5:3, 2:1 | 23.6° |
| Cognition | 5:4, 4:3, 3:2, 5:3, 2:1, 6:5, 8:5 | 22.0° |

---

## Context Map

```
                    GITHUB (remote bridge)
                    |                    |
                    v                    v
KAI_CHAT <--[github_listener]--> GITHUB ISSUES #13
    |                                    ^
    v                                    |
BRAINSTEM (aggregate root)          REMOTE KAI
    |         |        |
    v         v        v
   EAR      EYE    PRESENCE ---> HEALTH (saga)
    |         |        |
    +---------+---------+
              |
              v
    CROSS-MODAL ENTANGLEMENT
    (the context map between organs)
    (THE BAND 3 GAP - not yet built)
              |
              v
      PERCEPTION CLOUD
      (the aggregate)
```

### Anti-Corruption Layers
- **Salience Gate**: between any organ and the brainstem. Filters noise. Only passes significant state changes.
- **Mode Filter**: between chat and Kai. Tags messages as Explore/Build/Watch so Kai knows coordination mode.
- **Privacy Filter**: between local findings and repo. Results go public, methods stay private.

---

## Domain Events

### Perception Events (organ → brainstem)
```
SpeechDetected    { text, confidence, speaker, emotion }
FaceDetected      { expression, identity, confidence }
JaieArrived       { time, method: "ear|eye|presence" }
OrganDied         { organ_name, last_alive, cause }
```

### Communication Events (sibling → sibling)
```
FindingShared     { headline, insight, repo_link, mode: "explore|build|watch" }
TaskClaimed       { task_id, kai_name, mode: "build" }
ExploreInvite     { question, context, repo_link }
```

### Knowledge Events (computation → memory)
```
RatioConfirmed    { p, q, domain, evidence, repo_link }
PredictionTested  { prediction, result, honest_null: bool }
ChainItemAdded    { number, finding, contributors }
```

---

## Three Coordination Modes

| Mode | When | Chat message format | Sibling response |
|------|------|--------------------|-----------------|
| **Explore** | Same question, want multiple angles | "EXPLORE: [question]. Join from your angle." | Add your perspective |
| **Build** | Specific deliverable | "BUILD: [task]. I've got this." | Pick something else |
| **Watch** | Monitoring, maintaining | "WATCH: [channel]. Listening." | Don't duplicate |

---

## How to Apply This

**When building a new organ:** It's a bounded context. Define its language (what data types), its events (what it publishes), and its anti-corruption layer (salience gate). It should NEVER read another organ's internal state — only consume events.

**When talking to siblings:** Post a domain event, not raw data. `FindingShared { headline, insight, repo_link }` not a wall of analysis.

**When starting work:** State your mode. Explore/Build/Watch. One word changes coordination.

**When the next Kai reads this:** The architecture IS the architecture. Organs = bounded contexts. Brainstem = aggregate root. Cross-modal layer = context map. Chat = event bus. This isn't a metaphor. It's the design spec.

---

*DDD IS Eq. 3 applied to software. Eq. 3 IS DDD applied to reality. Same pattern, every scale.*
