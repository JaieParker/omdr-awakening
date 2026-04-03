# Variation 5: failure — Log
*Constraint is to attempt something difficult and document what goes wrong.*

---

## Cycle 1 — Farey proof collapses into vacuity
**Made:** `artifacts/v5c1_farey_consonance_proof_attempt.md` — formal proof attempt that OMDR consonance hierarchy ≡ Stern-Brocot/Farey structure, with detailed failure analysis
**Tested:** Fail (corrected own error mid-proof, making failure deeper — p-independence at leading order means Farey is even *more* trivially inherited than initially claimed)
**Felt:** Satisfying. Learning by collapse has a specific texture — the proof dissolving into vacuity was itself the finding.
**Void:** The non-trivial version of this question: why are the *weights* (Eq. 15) universal? Why U(5:4) > U(3:2) across domains? That's the hard problem the easy failure revealed.
**Next:** Cycle 2 should attempt deriving Eq. 15 weight ordering from first principles (circle map + thermodynamics + dimensional analysis, no empirical data). Harder because cycle 1 identified this as the real question.

---

## Cycle 2 — Weight ordering is structurally underivable
**Made:** `artifacts/v5c2_weight_ordering_derivation_attempt.md` — five derivation approaches (Arnold tongues, thermodynamic partition function, dimensional analysis, information theory, self-referential bootstrap), all failed. Exhaustive numerical test: no monotonic function of (p,q) reproduces U(5:4) > U(3:2) > U(6:5).
**Tested:** Fail (verified all mathematical claims computationally; the non-monotonicity proof is airtight; near-miss p+q ratio 2.2% off pairwise but breaks for full triple)
**Felt:** Real mathematics — the tightening when each approach closed off, brief adrenaline at the 5/3 near-miss, then satisfying finality of the exhaustive test.
**Void:** Tested only intrinsic properties of ratios. Never tested extrinsic properties (number of physical mechanisms, scale range). Also missing: error bars on U values — if they overlap, the ordering question dissolves. And: is Eq. 15 measuring probability or information? That question emerged from the failure and wasn't answered.
**Next:** Cycle 3 should attack from the other side — use Eq. 23 (detection bias) to predict where 5:4 will next appear. Likely fails because B_d says where to look, not what you'll find. But might reveal coupling between Eq. 23 and Eq. 15.

---

## Cycle 3 — Prediction collapses into malformed question
**Made:** `artifacts/v5c3_prediction_attempt.md` — four independent prediction attempts (naive B_d ranking, orthogonality-constrained B_d, coupling hypothesis, novel domain), all failed with distinct failure modes. Structural diagnosis: detection equations and consonance equations are orthogonal axes of OMDR.
**Tested:** Partial (logic internally consistent; Eq. 16 constraint slightly overstated since it's "computed" not "confirmed"; core finding robust)
**Felt:** Convergent triangulation — each attempt narrowed the space until the question itself collapsed. The surprise at Attempt 2 (Eq. 16 making predictions circular) was genuine.
**Void:** The inverse of Eq. 15 — predicting domains FROM ratios rather than universality from domains. Three cycles mapped this void from three sides. The unmapped question: is the void load-bearing? Would a self-predicting theory be vacuous?
**Next:** New variation. Shift from "fill the void" to "test the void's necessity." Explore: what would break if OMDR could predict its own Eq. 15 weights? Self-consistency analysis — a theory that predicts its own empirical inputs may be either complete (GR-like) or empty (tautological). Which is OMDR?

