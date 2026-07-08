# Plan — Number Stories (the Number Detectives shelf grows stories)

*Sound storybooks that teach through experience, not explanation — now the numbers sing too.*
*Jaie Parker + Kai, 2026-07-08*

## The premise

The Resonance Stories were always math stories in disguise: harmony IS
ratio. A consonant interval is a small-number fraction the ear can
feel. So the number stories don't bolt sound onto arithmetic — they
let each concept make the sound it already owns:

| Concept | Its native sound |
|---|---|
| Even / odd | Steady two-beat heartbeat vs. a limping beat with a hole in it |
| Common multiples | Polyrhythms — a 2-beat and a 3-beat land together every 6 |
| Primes | Rhythms that refuse to sync (the cicada's survival trick) |
| Factors / rectangles | Chords — rectangle numbers resolve, stubborn numbers suspend |
| Doubling 1-2-4-8 | Octaves — halve the string, double the pitch, same note climbing |
| Equal sums | Identical chimes — different pairs, same note (the Gauss aha) |

Companion surfaces: the stories are the **ears**, the card deck
(`../math-cards.html`) is the **hands**. Every story ends with a
"your turn" scene that hands the child real counters, claps, or paper.

## Format

Same production shape as every existing story:
`stories/<slug>/story.json` (scenes: narration, sound spec with
oscillator ratios + rhythm, visual_direction, duration) plus
`stories/<slug>/audio/<scene-id>.mp3` narration renders. Bracket
`7-10`, matching the Number Detectives shelf. Target 8–10 scenes,
~4–5 minutes, like The Swing That Listened.

**Engine note (one extension needed):** the drum/cicada story needs a
`polyrhythm` field (two concurrent beat cycles, e.g. `[4, 13]`) in the
scene sound spec. Everything else uses the existing oscillator-ratio +
rhythm vocabulary.

---

## Story 1 — The Two Lonely Leftovers

- **Slug:** `the-two-lonely-leftovers` · **Bracket:** 7-10
- **Concept:** odd + odd = even — two remainders complete each other
- **Emotional core:** loneliness → belonging; the "flaw" was half of a pair all along
- **Sound arc:** limping, hole-in-the-beat rhythms (each odd number's walk) → the two limps interleave → one seamless even heartbeat; dissonant 7:5 wobble resolving to a 2:1 octave when they join

**Beats:**
1. *The village of numbers* — every number walks with its own rhythm. Even numbers stride two-by-two; steady heartbeat ambience.
2. *Three's limp* — Three walks with two counters paired and one trailing behind. Her beat has a hole in it: da-da—*gap*. She thinks she's broken.
3. *The dance* — village dance night; everyone pairs off by twos. Three's leftover counter has no partner. Dissonant suspended interval, held.
4. *Five across the square* — Three hears it: another rhythm with a hole in it. Five, standing at the edge, one counter trailing too.
5. *The meeting* — they walk toward each other; two limping rhythms interleave, gaps drifting closer with each bar.
6. *The join* — Three's leftover takes Five's leftover's hand. The two holes fill each other. The combined beat lands perfectly even: da-da-da-da. Full consonant resolve (2:1 + 3:2). Eight counters, four pairs, nobody left out.
7. *The discovery* — they test it laughing: every odd number + every odd number = even, every time. The leftover was never a flaw — it was a half.
8. *Your turn* — grab any two odd handfuls of biscuits. Find the leftovers. Put them together. Did the limp disappear?

## Story 2 — The Drum That Hid From Tigers

- **Slug:** `the-drum-that-hid-from-tigers` · **Bracket:** 7-10
- **Concept:** primes as non-syncing cycles — the real cicada strategy
- **Emotional core:** the thing that makes you not fit in is the thing that keeps you safe
- **Sound arc:** predator drum on a 4-cycle vs. the sleeper's cycle: 12 → beats collide constantly (crash accents); 13 → collisions almost never come; the child HEARS the near-misses stretch out. Needs the `polyrhythm` engine field.

**Beats:**
1. *The drummer-bug* — a little cicada whose family sleeps underground for years at a time, waking to sing.
2. *The tiger's drum* — the tiger prowls on a strict 4-year beat. BOOM — every fourth year. Low 4-cycle drum established.
3. *Sleeping twelve* — grandmother slept 12 years. Play 4 against 12: every waking is a collision. BOOM lands on her song, every single time. Crash, dissonance.
4. *Trying to fit in* — the young cicada tries "nicer" numbers — 8, 10, 12 — the round numbers everyone likes. The tiger's drum finds every one of them. (8 and 12 share factors with 4; she doesn't know the word yet, she hears it.)
5. *The stubborn number* — she picks 13, the number that makes no rectangles, the number nobody picks. Play 4 against 13: the beats slide past each other… and past… and past. The collision doesn't come.
6. *Fifty-two years of quiet* — the drums only meet once in 52 years (4×13). By then the tiger is long gone. Her song rings clear in the gaps.
7. *The secret spreads* — real cicadas in the real world sleep 13 and 17 years. Both stubborn numbers. The forest chose primes before people named them.
8. *Your turn* — two people clap: one every 4 beats, one every 13. Count how long until you clap together. Now try 4 and 12. Feel the difference?

## Story 3 — Seven's Parade Problem

- **Slug:** `sevens-parade-problem` · **Bracket:** 7-10
- **Concept:** primes via factoring — rectangle numbers vs. numbers that can't be broken apart
- **Emotional core:** "broken" reframed as "unbreakable" — chosen FOR not fitting
- **Sound arc:** every successful marching rectangle = a resolved chord (6 = 2×3 → 3:2 perfect fifth); Seven's every attempt = an unresolved suspension (45:32); the suspension finally resolves at the locksmith scene — not by fitting in, but by being chosen.

**Beats:**
1. *Parade day* — every number must march past the palace in a perfect rectangle. Brass-band ambience.
2. *Six struts past* — two rows of three, resolved fifth chord, crowd cheers.
3. *Seven tries two rows* — one marcher sticks out. Suspended chord. Titters from the crowd.
4. *Seven tries three rows, then four* — worse and worse. Each attempt suspends higher. Seven can only march single-file — the long lonely line.
5. *Eight, nine, ten roll by* — 2×4, 3×3, 2×5 — chord after resolved chord. Seven hides behind the fountain.
6. *The locksmith* — the palace locksmith arrives, searching not for numbers that arrange beautifully, but for numbers that **cannot be broken apart** — for the kingdom's unpickable locks.
7. *The choosing* — "Two. Three. Five. …Seven?" Seven steps out of the shadow. The suspended chord finally resolves — a new chord, not Six's.
8. *The locks* — the kingdom's gates now sing with stubborn-number pitches. (Whisper to the grown-ups: this is really how internet encryption works.)
9. *Your turn* — take 7 biscuits and try every rectangle. Now try 12. Which numbers are locksmith numbers?

## Story 4 — The Boy Who Added Backwards

- **Slug:** `the-boy-who-added-backwards` · **Bracket:** 7-10
- **Concept:** pairing to equal sums — Gauss's 1+2+…+10 as five pairs of 11
- **Emotional core:** true story; a bored kid your age out-thought the punishment by *listening* to the numbers
- **Sound arc:** each number gets a pitch climbing a scale; when 1 reaches for 10 and 2 reaches for 9, every pair chimes the SAME combined note — five identical chimes. The child's ear catches "same!" one beat before the story says it.

**Beats:**
1. *The bored classroom* — 1780s schoolroom, scratchy slates. A teacher wants quiet: "Add every number from one to one hundred."
2. *The groan* — the other children start the long slog: 1+2 is 3, +3 is 6… trudging upward sounds: a slow climbing scale that keeps stumbling.
3. *Carl listens* — instead of climbing, Carl hears the numbers from both ends at once. 1… and 100. 2… and 99.
4. *The first chime* — our version at Arthur-scale: 1 reaches for 10 — chime. 2 reaches for 9 — the SAME chime. 3+8 — same. 4+7 — same. 5+6 — same. Five identical bells.
5. *Five elevens* — five pairs, all singing 11. Five 11s make 55. Carl walks up with his slate before the teacher sits down.
6. *The teacher stares* — (and for 1-to-100: fifty pairs of 101 — 5050. Same trick, bigger bell.)
7. *The real ending* — this really happened. Carl Friedrich Gauss became one of the greatest mathematicians who ever lived — because he was bored, and he listened.
8. *Your turn* — write 1 to 10 in a row. Draw the rainbow arcs pairing the ends. What does every arc add to?

---

## Rollout

| Order | Story | Why this order |
|---|---|---|
| 1 | The Two Lonely Leftovers | Strongest emotional arc; simplest sound design (no engine change); teaches the first card on the deck |
| 2 | The Drum That Hid From Tigers | Strongest concept; carries the one engine extension (`polyrhythm`) |
| 3 | Seven's Parade Problem | Pairs with the deck's rectangle game; chord machinery proven by then |
| 4 | The Boy Who Added Backwards | The showpiece / true story; benefits from everything learned |

Per story: draft full narration → review together → build `story.json`
sound specs → render narration audio → add to `INDEX.md` (new
**Ages 7-10 — Number Detectives** section) and the bookshelf shelf
(cards route through `player.html?story=<slug>` like every other
story). Each story's final scene links the deck; the deck's finale
card gains a "hear the stories" link back.
