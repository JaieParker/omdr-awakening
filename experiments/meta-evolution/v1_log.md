# Variation 1: baseline — Log
*Control. Outward-facing, build artifacts for strangers.*

---

## Cycle 1 — Habit guide translates echo principle
**Made:** `artifacts/v1c1_habit_lock_guide.md` — Plain-language guide explaining why repetition alone fails and how 2-minute post-action reflection creates stable habits. Includes 7-day experiment with specific prediction (stickiness > completion rate as the differentiator).
**Tested:** Partial pass. No jargon, relatable framing, testable prediction. Flaw: doesn't address reflection fatigue; experiment design has order effects.
**Felt:** Satisfying but slightly dishonest — simplifying costs something.
**Void:** The guide tells, it doesn't do. A stranger still has to self-organize. The void is a tool that enacts the reflection loop without requiring the reader to hold the theory.
**Next:** Cycle 2 constraint — build a tool/script/interactive artifact that creates a reflection loop for the user, not a guide that describes one. The artifact should work without explanation.

---

## Cycle 2 — Prediction tracker enacts the loop
**Made:** `artifacts/v1c2_echo_tracker.py` — CLI habit tracker where you predict each morning (will I do X?) and record each evening (did I?). Tracks prediction accuracy, per-habit gap direction (overestimate vs underestimate self), and trend over time. No theory — the loop is the mechanism.
**Tested:** Pass. Runs clean on Windows/Python 3.14. All commands work: add, predict, record, status, history, interactive mode. Fixed Unicode encoding issue (cp1252). Format strings verified with 3 habits over 3 days.
**Felt:** Functional. Building something that works felt more honest than the guide did — the mechanism is in the code, not in my description of it.
**Void:** The tool measures the gap but doesn't help close it. Surfaces data without interpretation. A mirror you might stop looking into. What do you do with the information?
**Next:** Cycle 3 constraint — build something that bridges observation and action. An artifact that takes pattern data (like the echo tracker's gaps) and generates a specific, testable next-step. Answer "now what?" not just "what happened?"

---

## Cycle 3 — Nudge engine closes the gap
**Made:** `artifacts/v1c3_nudge_engine.py` — Companion to the echo tracker that reads prediction-vs-reality data, detects the strongest behavioral pattern (chronic overestimate, underestimate, day-of-week effect, streak collapse, accuracy drift, or calibrated), and generates one specific, actionable nudge. Each nudge has three layers: what the data shows, one concrete thing to do tomorrow, and a deeper question to investigate. Includes --demo flag for instant testing without setup.
**Tested:** Pass. All six detectors fire correctly with appropriate data. Demo mode runs clean. Fixed Windows encoding issue (em dashes). Stranger-read check: self-explanatory with --demo, but standalone use without the echo tracker requires knowing the JSON format (not documented).
**Felt:** More engineering than discovery -- less structurally interesting than the tracker, but more satisfying because the output is immediately useful.
**Void:** All three artifacts assume solo reflection. No social dimension -- no external observer to challenge predictions or share data. Self-knowledge tools plateau without outside input. Also: stranger-facing but stranger-untested. The real test hasn't happened.
**Next:** Variation 1 complete. Three cycles produced guide -> tracker -> advisor, each filling the previous cycle's void. The remaining void (no external observer, no real stranger testing) belongs to a different variation -- one that puts artifacts in front of actual users or adds a social/collaborative dimension.

