# Launching and killing a profile

A strategy that cannot be ended is not an experiment. This file is about writing the ending
**first** — before the profile exists, while the outcome is still unknown and the rule can therefore
still lose an argument.

---

## 1. Why the rule is written first

> A hot first week is the most expensive thing that can happen to an unproven strategy, because it
> is the moment the rule gets rewritten.

The repo already has the precedent, in both directions:

- **The good case.** The NFL freeze's exit rule was written on 2026-08-26, while 26 positions were
  in flight and nothing had settled, precisely so a hot or cold Week 1 could not argue with it. The
  script that applies it says so in a comment: *"Changing these numbers after seeing Week 1 defeats
  the entire point of writing them down."*
- **The cautionary case.** That same floor was then moved from 1.0 to the 0.08 pilot **by operator
  override**, two days early, while the review still returned its stay-frozen branch. The evidence
  pointed the right way — model Brier 0.1318 against market 0.1399 — but the bootstrap CI
  **[-0.042, +0.031]** straddled zero, which is exactly the uncertainty the pilot cap exists to
  answer.

**Record which one moved a floor.** "The script unfroze NFL" and "the operator unfroze NFL early"
decay into the same sentence within a month, and only one of them is evidence.

---

## 2. Shape of a pre-declared rule

Copy the structure of `scripts/backtest/nfl_week1_review.py`. Five properties make it binding:

1. **Constants at the top, with a comment forbidding their edit after the fact.**

   ```python
   MIN_SETTLEMENTS = 20    # below this, no branch can fire
   MAX_MODEL_ERR   = 0.15  # mean model prob minus realised win rate
   PILOT_FLOOR     = 0.08  # what branch A applies (global is 0.03)
   FROZEN_FLOOR    = 1.0   # what the freeze set
   ```

2. **A `decide(rows) -> dict` that is a pure function of the settled rows.** No clock, no config, no
   network. It can then be unit-tested against synthetic rows, which is the only way to know the
   branch table says what you think.

3. **Named branches, every failure path landing on "do nothing".**

   | Branch | Condition | Action |
   |:--|:--|:--|
   | **A** | model Brier ≤ market Brier, `n ≥ MIN_SETTLEMENTS`, and over-claim ≤ `MAX_MODEL_ERR` | **pilot** — apply the capped floor |
   | **B** | market Brier better | stay frozen; re-judge on CLV, not on waiting years for ROI to converge |
   | **C** | anything else: too few settlements, unreadable rows, model badly over-claiming, **or any exception at all** | stay frozen |

   Branch C catching *exceptions* is the part people leave out. A review that crashes must not read
   as approval.

4. **Report-only by default; `--apply` is a separate, fail-closed flag.** The applier refuses unless
   the key is present and still at the value the freeze set — so it cannot stomp a hand-edit it does
   not understand.

5. **A `--self-check` that asserts the branch table.** Synthetic rows through `decide()`: too few →
   C, over-claiming → C, market better → B, model better and calibrated → A.

---

## 3. Report both numbers, always labelled

"Brier" alone is not a quantity:

- predicted = **market price** → the *market's* Brier, the benchmark.
- predicted = **`fair_value`** → the *model's* Brier, the thing under test.

Both were once printed under one label, on the same five bets on the same day — 0.169 against
0.0501. Every unfreeze branch and the λ finding turn on model-vs-market, so **always report the
pair, labelled, with the bootstrap CI on the difference.**

Also: `market_price_at_entry` and `fair_value` are **already side-relative** — a NO bought at 73c
stores `0.73`, the price paid for the NO. Never flip them for NO rows; flipping scored a 73c NO as
a `0.27` prediction and reported a Brier of 0.169 where the truth was 0.077, wrong on every window
containing a NO settlement (a third of the book).

---

## 4. Entry conditions per rung

### dry-run → pilot

🔒 Needs owner. Meeting these conditions makes the step *proposable*, not automatic: the agent
presents the evidence and the `DRY_RUN=false` diff, and the owner makes the change.

All four, or stay on rung 1:

1. **The profile's own knob is binding.** Read rejection reasons, not candidate counts. Seven days
   of longshot scans produced **one** trade row and approved **0 of 7** candidates — every rejection
   on *edge*, not price — which means its price floor was barely binding and flipping to live would
   have changed nothing except downside.
2. **The knob's value is not contradicted by the settled book.** Resolve that argument before live
   money, not after. An overlay carrying its own ⚠️ "this is contradicted by our own backtest"
   comment is not ready.
3. **The pre-declared review exists, runs, and has a `--self-check` that passes.**
4. **The §5 soft spots in the main skill are fixed** — profiled settle + reconcile tasks, scoped
   reporting, per-profile report dirs.

### pilot → live

🔒 Needs owner, as above: the agent proposes, the owner promotes.

- The review fires branch A **on the full sample**, not a projection of it.
- **Read CLV, not ROI**, for any book that will never accumulate enough settles for ROI to
  converge. ROI at n≈30 is a story; closing-line value is a measurement.
- Gate 2b's segment cap still binds the book. Removing the pilot floor does not remove the cap.

---

## 5. A freeze must not block its own exit

**Before arming any review, check the strategy has an evidence stream that survives its own
restriction.** A frozen or heavily gated book places no orders, so it accrues no settlements, so
the evidence that would lift the restriction never arrives.

- NFL escaped this only by accident: 19 positions were already in flight when the freeze landed,
  and they settled into the review.
- NCAAF was frozen holding **nothing**, pinning it at 11 settled against a bar of 20 — a review
  armed on that pattern returns "stay frozen" forever.

Where the stream does not survive, the answer is the shadow book — zero-risk rows that need only
(model probability, market price, outcome) and never needed a filled order. Details in the
`edge-radar-strategy-evidence` skill.

---

## 6. Killing a profile

Kill criteria belong in the same file as the launch criteria, written at the same time.

**Write them as a number and a window**, e.g. *"if CLV is negative over 60 rows, the profile is
retired"* — not *"if it is not working"*.

To retire one:

1. **Set `DRY_RUN=true` in the overlay first.** This is the tourniquet; it stops new money
   immediately without touching the other book.
2. **Hold the open positions, do not flatten them.** Exiting a wide book pays exactly the
   illiquidity penalty Gate 3.6 exists to avoid. Exit a ticker only if its spread is ≤ 5c *and* the
   exit price beats hold-to-settlement EV.
3. **Let them settle**, under a profiled settle task. A retired book's rows are the evidence the
   next idea is judged against; losing them loses the point of having run it.
4. **Keep `.env.<name>` and the `docs/<name>/README.md`,** with a dated "retired because" section.
   Delete the scheduled tasks, not the record.
5. **Leave the subaccount.** It is an exchange-enforced wallet and costs nothing to keep. Reusing
   one for a *different* strategy pollutes both books' history — start a new one.

**Do not** kill a profile by deleting the overlay file. That makes `--profile <name>` a hard error
rather than an ended experiment, which reads as breakage to the next person, and any scheduled task
still passing the flag starts failing instead of stopping.

---

## 7. What counts as an operator override

Any of these, and it goes in the changelog as an override rather than as a result:

- Moving a floor before the review's window closes.
- Moving a floor when the review returned a stay-frozen branch.
- Editing a pre-declared constant after seeing the data.
- Applying branch A by hand because "the script is being conservative".

None of them is forbidden — the operator owns the bankroll. All of them must be **labelled**, with
the review's actual verdict recorded next to the action taken. An override recorded as evidence is
the one failure mode that corrupts every later decision.
