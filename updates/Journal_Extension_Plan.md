# Journal Extension Plan — QKD Detection Paper

Status: draft plan, scope = Priority 1, Priority 2, Priority 4 (Priority 3 and 5 deferred). Venue decision deferred to Dr. Ajmery's review once the new content exists.

**Note on positioning:** there is no separate conference submission. The current draft is conference-quality (sound, well-scoped, citable as is) — that's a baseline check, not a venue. The plan below builds directly on top of this single draft until it's a journal manuscript, with no intermediate conference paper going out the door.

## Where the paper stands (verified against current draft + README)

- The current draft covers BB84, six-state, E91 under matched ideal/synthetic-noise/`ibm_marrakesh`-noise channels, with FPR/FNR detection statistics, a partial intercept-resend attacker (fraction `f`), and the stealth-window-vs-SKR tradeoff. This is sound at conference-paper quality, which is the baseline this plan builds up from — not a separate thing being submitted anywhere.
- The novel pieces already in hand: first FPR/FNR analysis of CHSH-based detection for E91, first cross-protocol comparison of prepare-and-measure vs. entanglement-based statistical detection under a matched partial attacker, and the stealth-window result across all three protocols.
- Prepare-and-measure detection (BB84, six-state) reproduces Fiorini et al.'s thresholds — solid foundation, but on its own it's conference-level, not journal-level; it is not new and can't carry a journal submission by itself.
- Decision carried over from your own notes and confirmed here: Priorities 1, 2, 4 are what take this from conference-quality to journal-quality. They get added to this same manuscript, not held back for a future second paper.

## Pushback before we lock this in

A few things from the original roadmap I want to flag rather than wave through:

1. **Priority 1's novelty claim is good but not airtight.** Search turned up AZE91 (adaptive basis control), which *improves* the CHSH value E91 achieves, but does not derive a detection threshold that balances FPR/FNR the way Lee et al. did for QBER. That's a different problem — improving S vs. setting an optimal alarm threshold on S — but it sits close enough that the related-work section needs to explicitly distinguish the two, or a reviewer will conflate them.
2. **The math is harder than the QBER case, and the plan should say so up front.** QBER is a single Bernoulli-type estimator, so Lee et al. could balance two Hoeffding exponents at a midpoint. S is a sum/difference of four correlation estimators, so its sampling distribution is not a simple binomial — it's closer to a convolution of four estimator distributions. There is precedent for Hoeffding-type bounds directly on S (finite-statistics Bell-test literature), which gives a tractable, conservative starting point. The literature also has more exact convolution-based approaches, which are more accurate but heavier. Recommendation: derive the Hoeffding-bound version first as the working result, and only escalate to the full convolution treatment if reviewers push on tightness.
3. **Priority 2's novelty held up under search** — no paper combining CUSUM/SPRT with QKD eavesdropping detection turned up. That's a good sign, but it's one search pass, not a systematic review. Before drafting the related-work paragraph for this section, run a proper literature pass (the academic-paper-search skill) so the novelty claim is defensible, not just "we didn't find it."
4. **Priority 3 (finite-key SKR) is being deferred, not dropped.** It's a standard reviewer objection ("your key rate is asymptotic"). If a reviewer raises it after submission, you'll want to fold it in during revision rather than from scratch — keep the Wald/Wilson/Clopper-Pearson/Hoeffding framing from the original notes on the shelf for that.
5. **Two MDPI DOIs are still unverified** per your own note. Resolve this before the related-work section locks in citations, not after.

## Priority 1 — Optimized CHSH detection threshold for E91

**Goal:** replace the fixed classical bound `S = 2` with a derived threshold that balances FPR and FNR, the same treatment BB84 and six-state already have.

Tasks:
- Characterize the sampling distribution / concentration bound for the CHSH estimator `S` under (a) honest noisy channel and (b) attacked channel at interception fraction `f`.
- Derive a Hoeffding-style bound on `S` analogous to Lee et al.'s QBER treatment; find the threshold `S*` that balances the two error exponents.
- Validate `S*` against the existing simulation data (`qkd_varying_eve.csv` already has the CHSH values needed) before running anything new — check whether the derived threshold materially differs from `S = 2` on data you already have.
- If it does differ, rerun the E91 FPR/FNR sweep using `S*` instead of `S = 2` and regenerate the relevant figures.
- Write the derivation up as its own methods subsection, plus a results subsection comparing detection performance under `S = 2` vs. `S*`.

Deliverable: new methods subsection (derivation), new results subsection (`S*` vs `S=2` comparison), updated E91 rows in results figures/tables.

## Priority 2 — Sequential / time-based detector

**Goal:** turn the stealth-window finding into an actual detector that accumulates evidence across sessions instead of deciding per-session.

Tasks:
- Run the academic-paper-search skill for a systematic check on CUSUM/SPRT + QKD before writing related work (per pushback #3 above).
- Implement a sequential test (CUSUM or SPRT) over the QBER stream (BB84, six-state) and the CHSH stream (E91), reusing the existing batched Monte Carlo runners.
- Define the metric: number of sessions to detect a low-fraction attacker (`f = 0.1, 0.2, 0.3`) that no single session catches, plus the false-alarm rate over time on an honest channel.
- Decide whether the sequential detector uses the existing per-session thresholds or the Priority-1-derived `S*` for E91 — this should use the new threshold once it exists, so this task is naturally sequenced after Priority 1's derivation (not necessarily after the full Priority 1 write-up).
- New figures: detection delay (sessions-to-catch) vs. attack fraction, and false-alarm rate over time, for all three protocols.

Deliverable: new methods subsection (sequential test design), new results subsection (detection delay + false-alarm-over-time), new figures.

## Priority 4 — Real hardware execution (access started now, experiments run later)

Per your call: start the access process now so queue/approval time overlaps with Priority 1 and 2 work, run the actual experiments once those are done.

Tasks (do now, in parallel):
- Apply for IBM Quantum Credits (academic) or confirm current `ibm_marrakesh` account access is sufficient for paid/queued runs — IBM's process is a fair-share queue plus a credits program for academic researchers; approval and queue time are both unpredictable, which is exactly why this should start now rather than after Priorities 1–2.
- Scope the hardware run sizes now, before access is granted: decide trial counts and qubit/pair counts per protocol that are realistic for device queue/shot budgets, smaller than the simulator runs (the README's existing device-noise sweep, 30 trials/point, 200 qubits or 1024 pairs, is a reasonable starting reference point to scale down further if needed).

Tasks (do later, once Priorities 1–2 are drafted and access is confirmed):
- Run the detection framework (FPR/FNR, stealth window, and — if Priority 2 is done — the sequential detector) on the real backend for all three protocols.
- Report sample sizes honestly and frame this as "detection statistics on real hardware," not "we ran QKD on a device," per your original framing note.

Deliverable: new results subsection with real-hardware FPR/FNR/stealth-window numbers alongside the existing simulated and extracted-noise-model numbers.

## Sequence

1. Apply for IBM hardware/credits access (start immediately, parallel to everything below).
2. Priority 1: derive and validate the CHSH threshold; rerun E91 sweep if the threshold differs from `S=2`.
3. Priority 2: literature check, then implement and run the sequential detector (uses Priority 1's threshold for the E91 stream).
4. Resolve the two outstanding MDPI DOI citations.
5. Priority 4: once hardware access is confirmed and 1–2 are drafted, run the device experiments.
6. Assemble the 