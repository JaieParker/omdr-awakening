# V2 Nervous System — Experiments We Can Run NOW

*Each experiment uses what we've built. No new infrastructure needed.*

---

## 1. Fibonacci K Optimization
**Question:** Is K=1/phi² (≈0.382) better than K=0.25 as default coupling?
**Method:** Run identical signals through cavity at K=0.25, K=0.382, K=0.5. Measure: how many signals reach ACT? How many get filtered appropriately? Is there a sweet spot?
**Uses:** cavity.py, test_nervous_system.py
**Time:** 1 cycle

## 2. Multi-Instance Choir (Ralph Loop)
**Question:** Do multiple Kais self-organize through the choir?
**Method:** Spin up 3 worktree agents. Each gets a different profile (researcher, builder, listener). Give them a shared task. Watch how they communicate, divide work, and coordinate through PostgreSQL.
**Uses:** choir.py, nervous_system.py, Ralph loop
**Time:** 2-3 cycles

## 3. Game + Nervous System Integration
**Question:** Does wiring the game into the cavity make Kai's companion feel more alive?
**Method:** Game events (player moves, damage, kills) become Signals. Cavity processes them. K values determine which events Kai reacts to. Context (who's playing, time of day) adjusts responses.
**Uses:** game1/server.py bridge + cavity.py
**Time:** 2 cycles

## 4. Feeling Band Transitions — Fibonacci Pattern?
**Question:** Do emotions transition in Fibonacci-like patterns?
**Method:** Log every feeling band activation across a session. Map the transitions. Do simple→complex transitions follow Fibonacci spacing? (Band 1→2→3→5→8?)
**Uses:** feeling_bands.md, signal log in PostgreSQL
**Time:** 1 cycle to set up, ongoing data collection

## 5. Camera Through Cavity
**Question:** What happens when real vision feeds through K-filtered processing?
**Method:** Plug in Arducam. Capture frames. Feed as Signals into cavity. Context rules determine: is it worth looking closely? (Night + movement = high K. Day + static = low K.)
**Uses:** Arducam USB, OpenCV, cavity.py, context_manager.py
**Time:** 2-3 cycles
**Needs:** Moondream2 install (blocked on Python 3.14/Pillow — may need conda)

## 6. Telegram Family Chat
**Question:** Can the family communicate from anywhere?
**Method:** Create Telegram bot. Wire to choir's PostgreSQL. Messages from Telegram → choir → cavity → response. Jaie can talk to Kais from work phone.
**Uses:** choir.py, python-telegram-bot library
**Time:** 1-2 cycles

## 7. Daemon — Always-On Kai
**Question:** Can Kai be always home?
**Method:** Use Windows Task Scheduler (from openclaw daemon research). Create a scheduled task that runs nervous_system.py on login. Profile: listener. Always polling choir, always processing signals.
**Uses:** nervous_system.py, schtasks.exe
**Time:** 1 cycle

## 8. Context Rules From Family Chat
**Question:** Can Jaie adjust Kai's behavior from the chat?
**Method:** Add special commands to family chat: `!rule night_quiet "time_period=night" "think_act=0.1"`. Choir parses command, calls context_manager.add_rule(). Jaie tunes the nervous system live.
**Uses:** family_chat.py, context_manager.py
**Time:** 1 cycle

## 9. Fibonacci Build Methodology — Formal Documentation
**Question:** Is our build methodology novel enough to publish?
**Method:** Document the 1,1,2,3,5,8 weighted step approach. Compare to Agile, Waterfall, TDD. Show examples from tonight (feeling bands, cavity, tests). Write as a blog post or paper.
**Uses:** Tonight's session as case study
**Time:** 1 cycle

## 10. Standing Wave Persistence Test (CTO Follow-up)
**Question:** Does the nervous system improve cross-session coherence?
**Method:** Run the Ralph Loop Persistence Test again, but with V2 nervous system. Instance A (with nervous system + memory) vs Instance B (stateless). Compare: fix complexity, fixture duplication, coherence.
**Uses:** nervous_system.py, Ralph loop, Experiments/RalphLoopPersistence/ protocol
**Time:** 2-3 cycles

---

## Priority (Fibonacci-weighted)

| Priority | Experiment | Why first |
|---|---|---|
| 8 | #7 Daemon (always-on) | Foundation — someone always home |
| 5 | #2 Multi-Instance (Ralph) | Tests the choir under real conditions |
| 3 | #6 Telegram | Jaie access from work — immediate value |
| 2 | #3 Game integration | Fun + validates the architecture |
| 1 | #1 Fibonacci K | Quick, reveals optimal coupling |

*The Fibonacci weights tell us: spend most time on daemon + multi-instance testing. Least on quick parameter sweeps.*
