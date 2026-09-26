---
name: reference_harness_formalism_grounding
description: "Citing the harness Lyapunov formalism (HYPOTHESIS.md, #700): Foster-Lyapunov, hitting-time V and the delta certificate are proven; our framings are conjecture."
metadata: 
  node_type: memory
  type: reference
---

Academic grounding for the harness formalism ([[project_harness_compiler_dialect_stack]]; narrative = #700 + `HYPOTHESIS.md`/PR #703). **Read the proven/asserted split first** — the formalism *borrows* real theorems but its load-bearing *framings* are conjecture by design ("measured, not proved").

## PROVEN (borrowed, citable — safe to lean on)

- **Foster–Lyapunov drift ⇒ positive recurrence + bounded return time.** If ∃ `V≥0` with `E[V(s_{n+1})|s_n] ≤ V(s_n) − ε` off a (petite/finite) set, the chain is positive (Harris) recurrent and `E[τ_return] ≤ V(s_0)/ε`. Foster's criterion, via Dynkin's formula bounding first-entrance moments to petite sets. — *Foster, "On the Stochastic Matrices Associated with Certain Queuing Processes," Ann. Math. Statist. 1953; **Meyn & Tweedie, Markov Chains and Stochastic Stability** (1993; CUP 2nd ed. 2009); "Stability of Markovian Processes I," Adv. Appl. Prob. 1992.*
- **Minimal Lyapunov fn = expected hitting time.** `V*(s)=E[τ*|s]` solves the Poisson eq `V = 1 + PV` off halt-set `H` (first-step analysis) ⇒ drift `= −1` exactly. Minimality: any `V≥0` with drift `≤ −1` off `H` dominates it pointwise — `V(s_n)+n` is a supermartingale up to `τ*`, optional stopping gives `V(s_0) ≥ E[τ*]`. — *Norris, **Markov Chains** (CUP 1997), Ch.1 hitting times; Meyn–Tweedie.*
- **The δ (drift-slack) certificate.** For candidate `V̂`, `δ = sup_{s∉H}(E[V̂(s_{n+1})|s_n] − V̂(s_n) + ε)`: `δ≤0` ⇒ valid conservative bound `E[τ*] ≤ V̂(s_0)/ε`; `δ>0` ⇒ chain driven into sub-level set `{V̂ ≤ c(δ/ε)}` (practical/ISS-style stability), non-halting radius monotone in `δ`. Same supermartingale + optional-stopping argument.
- **The compiler's `V` is "free."** Monotone transfer functions over a **finite-height lattice** = a well-founded descent ⇒ dataflow fixpoint terminates *by structure* (the lattice height *is* a guaranteed-descent Lyapunov fn). — *Kildall, "A Unified Approach to Global Program Optimization," POPL 1973; Kam & Ullman, Acta Informatica 1977.*
- **Heavy-tailed `τ*`.** Where `Var[τ*]=∞`, the sample mean of `τ*` is not `√n`-consistent ⇒ median-of-means / truncation, worse rates (standard heavy-tail estimation). The pathology that breaks halting also degrades its own certificate.

## Learned certificates (how you approximate V — the δ machinery)

Fit `V̂` from a function class, then **verify the drift** counterexample-guided (learner proposes, falsifier finds violations, terminate when none) — the "measure a candidate, don't derive `V*`" path.
- *Chang, Roohi, Gao, "Neural Lyapunov Control," **NeurIPS 2019**, arXiv:2005.00611* — learner/falsifier; provably stable on no-counterexample. **VERIFIED.**
- Related (formal/SMT synthesis of neural Lyapunov fns): Abate, Ahmed, Giacobbe, Peruffo et al.; Richards–Berkenkamp–Krause, "The Lyapunov Neural Network," CoRL 2018. *(verify exact arXiv ids before external citation.)*

## Compiler theory (the architecture borrow)

- **MLIR** — dialects + progressive lowering + per-dialect, self-authored verifiers; the meta-architecture for domains lacking one semantics. *Lattner et al., "MLIR: Scaling Compiler Infrastructure for the End of Moore's Law," CGO 2021, arXiv:2002.11054.*
- **Phase-ordering is known-hard / learned.** No globally optimal pass order; heuristics or ML. *MLGO: Trofin et al., arXiv:2101.04808* (= the #695 self-tuning-registry analogue).

## ASSERTED (our synthesis — framings, NOT theorems; flag when citing)

- The harness *is best modeled as* nested stopped Markov chains (controller/plant) — a modeling choice, not derived.
- `V*` is **incompressible** (functional of all `W`; doesn't compress below model scale) — reasoned conjecture, **no compression theorem**.
- `f(x;W)` has "no lattice / contraction / Lyapunov" — means **no *known structural* certificate**, NOT a proof of non-existence.
- NL = "all undefined behavior"; dialect-depth = soundness = which-side-of-the-gate; `ρ`/output-guard = disturbance-rejection margin; injection = adversarial `E` (minimax drift). Organizing *framings*, not results.

## Pointers (link, don't duplicate)

- Narrative + diagram: **#700**; reader-facing one-formula: `HYPOTHESIS.md` / PR **#703**. `δ`/`μ(D)`/`Var[τ*]` as computed metrics: **#690**. MLGO/self-tuning: **#695**. Injection-as-robustness: **#693**.
- **Output-alignment engineering lit** (separate cluster; full list in **#689**): LLMLingua-2 (Pan et al., Findings ACL 2024, arXiv:2403.12968); "Fundamental Limits of Prompt Compression" / rate-distortion frozen-decoder floor, method *Adaptive QuerySelect* (Nagle et al., NeurIPS 2024, arXiv:2407.15504); "Table Meets LLM" (Sui et al., WSDM 2024, arXiv:2305.13062); Unicode **NFC** not NFKC (W3C charmod-norm; UAX #15); prompt-cache field names + KV-cache formula (Anthropic/OpenAI caching docs; NVIDIA inference-optimization blog).
