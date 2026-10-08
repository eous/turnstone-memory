---
name: feedback_negative_verdicts_carry_scope
description: "Reporting a negative result (no hits, doesn't apply): name the check's scope in the verdict; a grep is not a clearance, and 'doesn't bite' is not 'nothing to learn'."
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-08T05:20:00.000Z
---

A negative verdict ("nothing here touches the document", "this result doesn't apply", "no hits") must carry the scope of the check that produced it, in terms the reader can verify without re-running it. "Clean against a term match on abstracts" and "clean" are different claims; only the first is earned by a grep. A confident clearance closes a question, which is worse than an open one, so the fix is not lower confidence everywhere but an explicit scope on every negative.

Two sub-rules. **Relevance is semantic; a grep is syntactic** — the document's own line, syntactic soundness is free and semantic adequacy is not, applies to the review of the document. A result can bear on a claim under vocabulary nobody searched, or through its proof technique rather than its headline. **"Doesn't bite" ≠ "nothing to learn"** — a result that contradicts no claim can still sharpen one; before dismissing a harness-shaped result, map it onto the tuple (what plays π, M_W, γ/ρ, H and τ_H; where the loop and the unbounded memory live) and ask what the mapping shows.

**Why (2026-10-07):** after the openai/math release, a 46-item scan plus a full-catalog keyword grep were reported as "nothing in the 722 touches the citations" — true as a term match, overclaimed as a verdict. Family 376 (universal computation in forced Navier–Stokes flows) was dismissed on the word "incompressible" as fluid dynamics; read and mapped onto the tuple, it produced the C4 class-level impossibility theorem and the C5 specification obligation (HYPOTHESIS.md rules 7–8). Two rounds of independent second-model review then refused the inferences drawn from that mapping (a Turing-in-shell / compression-in-plant partition; "universality lives in the shell"; finite-plant ⇒ computable outer V*) while keeping the observations — the pattern to copy: keep observations, refuse inferences.

**How to apply:** when reporting any negative result, name the method and its coverage in the same sentence as the verdict ("no abstract names X" rather than "nothing touches X"). For "doesn't apply" verdicts on structurally similar results, state the mapping that was checked. When a reviewer refuses an inference, concede the inference and restate what the observation alone supports.
