# Historical X intelligence — Polymarket (6 Nov 2026)

**Scope:** historical lead intake only, not an on-chain finding. Sources: user-provided French dossier, *Polymarket : ce que les archives X ajoutent réellement* (386 lines, dated 2026-11-06), the repository main at `17acd3409382201dfb6fc0d43a30d4208952eb02`, and publicly accessible UEFA/Polymarket pages. This note intentionally does **not** amend frozen investigations, raw evidence, root README, or MASTER_REPORT.

## Evidence status and provenance

- The supplied dossier reports **40 X calls, 35 historical searches, 5 batch reads, 424 returned rows and 391 distinct post IDs**. Its claimed raw corpus (`/workspace/polymarket-history/`) and query logs were **not** supplied with the text report and have **not** been re-run in this PR. Consequently, the quoted text of X posts remains **reported from the source dossier**, not independently authenticated here. Zero X hits are never proof of absence.
- X snowflake IDs are consistent with their stated UTC posting dates (see tools/verify_x_snowflakes.py); a snowflake verifies **time encoded in the ID**, not post text, edits, or authorship. Any original-post text must be checked against preserved X API objects/edit history and archived media.
- The **final Ballon d'Or top five** is independently stated by UEFA (2026-10-26): Kane, Mbappé, Yamal, Rodri, Messi. https://www.uefa.com/uefachampionsleague/news/02aa-21ec47378e70-b29defb43769-1000--harry-kane-wins-2026-men-s-ballon-d-or/
- Existing repository evidence is **prior repository work**, not a new result generated here: [Ballon d'Or chronology](../../investigations/ballon-dor-census/sources/TIMELINE.md), [Ballon d'Or findings](../../investigations/ballon-dor-wallets/FINDINGS.md), [transactional report](../../investigations/ballon-dor-wallets/sources/reports/rapport_final.md). PR27–32 have separate branches/lineage, are not treated as merged into main.

## A. Ballon d'Or: public-information boundary (reported X source, chain recheck pending)

| UTC event time | Observation | Evidence status |
| --- | --- | --- |
| Oct 01, 18:33:15 | kraben006 first family trade | EXISTING_REPO |
| Oct 09, 20:50:04 | brace227 first family trade | EXISTING_REPO |
| Oct 12, 00:16:03 | Thin-Disclaimer-Life first family trade | EXISTING_REPO |
| Oct 14, 14:33:24 | Thin-Disclaimer-Life last trade | EXISTING_REPO |
| Oct 14, 20:01:01 | cookedrice first family trade | EXISTING_REPO |
| Oct 16, 00:27:24 | VidenteRibeira first family trade | EXISTING_REPO |
| **Oct 16, 17:38:26** | **@Cypya_Poly purportedly posts full, correct top five**, X ID 2111149784858042762 | X_REPORT_UNREVALIDATED |
| Oct 19, 14:47:34 | Exact-place markets for 2nd/3rd begin, per Gamma startDate | EXISTING_REPO; on-chain first executable fill still to be checked |
| Oct 20, 19:32:36 | Exact-place markets for 4th/5th begin, per Gamma startDate | EXISTING_REPO; on-chain first executable fill still to be checked |
| Oct 21, 14:25:48 | @Jydyjyd purportedly says they copied presumed informed traders; X ID 2112913244058755159 | X_REPORT_UNREVALIDATED |
| Oct 23, 15:17:49 | Upside publication, per existing archived article metadata | EXISTING_REPO |
| Oct 26 | Official final Ballon d'Or outcome | UEFA_CONFIRMED |

Important: the **pre-Oct-16 positions relate to the markets available then**, not to purchasing all five exact places before those individual markets existed. Existing transactional analysis attributes **$36,840.48** of Thin-Disclaimer-Life's Mbappé-over-Yamal purchases to a still earlier cutoff (Oct 13 at 18:51 UTC); do not report it as evidence of a complete five-place forecast. Some pre-Oct-16 family positions cannot have resulted from a tweet posted Oct 16, yet that alone does not establish private access or common ownership.

Suggested explanatory competition: H1 early private knowledge vs H2 publicly informed skill/rumour vs H3 copy trading after dissemination. Event times must be fixed before outcome selection; quantify probability, liquidity and baseline frequency of competing public rankings.

**Candidate public trading profiles, not established X-to-wallet links:**
- Cypya: `0x970998da056e60c707d9b1fc55cfdf3d68c252ab`. A third-party market analytics page labels this account “Cypya”; X authorship/control is **UNRESOLVED**. https://onchainpoly.com/wallet/0x970998da056e60c707d9b1fc55cfdf3d68c252ab
- Jydyjyd: `0x1c4cd350bce3cb791daf88ce2034de9b03318d85`. The Polymarket public profile displays “Jydyjyd”; linkage to the X author is **UNRESOLVED**. https://polymarket.com/profile/0x1c4cd350bce3cb791daf88ce2034de9b03318d85

Do not incorporate either candidate into the existing 11-wallet cohort without independently established relevance; never infer a real-world identity.

## B. Maduro / Iran: actionable candidates (not verified on-chain by this import)

1. **PURE698**: `0x2a1a80e795b6ed6325e3934b6a27d57111e72ffe`. X author @betint_ai alleges prior Israel/Iran positions and subsequent Venezuela/Maduro exposure. Verify address-to-profile provenance, the exact markets and complete performance (including losing expiries) first. https://x.com/betint_ai/status/2007351724185461007
2. **JamWil23**: `0xfddfd657996c214d4dd2fd0fff4589c0daeaf33d`. @betint_ai alleges dated Maduro-related entries. No direct transfer, profit, or association with another account has been newly established. Same source.
3. **Group G → '38' thesis**: @Andrey_10gwei describes 38 accounts and withdrawals toward `0xc5bB1Be0407db7312911ec765D399D02461e411a`. Existing PR27 already discusses **group G (4 wallets) and the same beneficiary**, so the beneficiary and basic pattern are **KNOWN IN PR**, not a new discovery. Establish unique proxies, chain-specific receipt/log evidence, de-duplicate handles, verify overlap with G/E/eight-account cohorts and model the destination as a possibly pooled service. https://x.com/Andrey_10gwei/status/2034030676589351244
4. **cashy**: X bot @0xscarlex reports NO entries Feb 19/23 and a YES alert Feb 28 at 06:32:48 UTC, after the repo's 06:13 repricing reference. The **tweet is not a fill timestamp**. Proxy `0x8f42ae0a01c0383c7ca8bd060b86a645ee74b88f` is already documented in PR30. https://x.com/0xscarlex/status/2027633061949501704
5. **flydartball**: June 2025 loss and February 2026 reported wins require stable historical proxy linkage and complete cash-flow PnL; no repeat-informed-trader claim is confirmed. https://x.com/yc989/status/1935769781669437727
6. **Car's corrected alert**: potential negative control; check the referenced account and linked correction before treating the two posts as referring to one wallet. https://x.com/CarOnPolymarket/status/2021095225393873035

## C. What cannot be claimed on present evidence

- No new transaction hash/receipt proving a link between the new candidates and any earlier cohort was produced by this import.
- X claims of an “insider”, a 38-account single owner, a recurring winner, or military information are **assertions by third parties**, not our findings.
- A shared CEX, Relay, solver, gas payer, deposit address, liquidation batch, order-book counterpart or temporally close transfer does not establish joint control.
- One correct historical forecast is not an independently measured probability of privileged access.
- PnL is not withdrawals minus deposits if open positions, fees, redemptions or incomplete account histories remain.

## D. Next stage and publication gate

See [LEADS.csv](LEADS.csv) for machine-readable intake and [REPLAY_PROTOCOL.md](REPLAY_PROTOCOL.md) for pre-registered tests. Outputs belong in a **separate new, append-only evidence directory** with chainId, exact token, contract, transaction hash, logIndex, raw timestamps and source references; compare to frozen baselines without modifying them. Promote a claim to CONFIRMED only after primary-source validation and reproducible receipts. Keep public promotional README free of unresolved hypotheses; this note is technical research only.
