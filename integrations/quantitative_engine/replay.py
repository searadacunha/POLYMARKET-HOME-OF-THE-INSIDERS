"""Coverage of the archived cases by the two new sources.

Overlap of a calendar window is not a new financial link. Hours that were not
downloaded stay unread.
"""

from __future__ import annotations

from contracts import PENDULUM_WINDOWS, V1_UNTIL_UTC, poly_data_v2_claim

# Windows below are the decision periods already stated in the investigations,
# not new transaction reconstructions.
CASES = (
    {
        "case_id": "maduro",
        "start": "2026-01-01T00:00:00Z",
        "end": "2026-01-31T23:59:59Z",
        "prior_conclusion": "Flux financiers du réseau à huit comptes confirmés séparément de la cohorte Iran. Signal prédéclaré non exploitable hors échantillon.",
        "prior_path": "investigations/maduro-iran/FINDINGS.md",
    },
    {
        "case_id": "iran",
        "start": "2026-02-01T00:00:00Z",
        "end": "2026-02-28T23:59:59Z",
        "prior_conclusion": "Même distinction de cohortes. Le timing reste une hypothèse. 128 acheteurs YES dans la fenêtre Iran.",
        "prior_path": "investigations/maduro-iran/FINDINGS.md",
    },
    {
        "case_id": "ballon_dor_2026",
        "start": "2025-10-01T00:00:00Z",
        "end": "2025-10-31T23:59:59Z",
        "prior_conclusion": "Flux entre comptes de presse reconstruits. Test collectif gelé non significatif après Bonferroni.",
        "prior_path": "investigations/ballon-dor-wallets/README.md",
    },
    {
        "case_id": "c7_nobel_2025",
        "start": "2025-10-09T00:00:00Z",
        "end": "2025-10-10T23:59:59Z",
        "prior_conclusion": "Financeur commun et retraits Relay documentés le 12 novembre 2026. Attribution personnelle non établie.",
        "prior_path": "investigations/followup-20261113/README.md",
    },
    {
        "case_id": "kpmg_documentary",
        "start": "2026-01-01T00:00:00Z",
        "end": "2026-11-07T00:00:00Z",
        "prior_conclusion": "Registre documentaire. La p-value tierce n'est pas rejouée comme une preuve d'information privilégiée.",
        "prior_path": "research_notes/kpmg-election-integrity-2026-11-07/REPORT.md",
    },
)


def _overlaps(start: str, end: str, window_start: str, window_end: str) -> bool:
    return start < window_end and end >= window_start


def replay_case(case: dict, downloaded_eras: tuple[str, ...] = ()) -> dict:
    eras = []
    for window in PENDULUM_WINDOWS:
        hit = _overlaps(case["start"], case["end"], window["start"], window["end_exclusive"])
        eras.append({
            "era": window["era"],
            "calendar_overlap": hit,
            "downloaded_for_this_case": hit and window["era"] in downloaded_eras,
            "can_identify_wallet": window["wallet"],
            "can_tie_fill_to_chain_by_itself": window["tx_hash"],
        })
    if case["end"] < V1_UNTIL_UTC:
        poly = "NO_POLY_DATA_V2_COVERAGE"
    elif case["start"] < V1_UNTIL_UTC:
        poly = "WINDOW_CROSSES_CUTOVER_NOT_CLAIMED"
    else:
        poly = "POST_CUTOVER_ONE_CONTRACT_NOT_DOWNLOADED"
    # Touch the claim helper so a post-cutover binary-contract label stays explicit.
    if poly == "POST_CUTOVER_ONE_CONTRACT_NOT_DOWNLOADED":
        claim = poly_data_v2_claim(case["end"], "0xe111180000d2663c0091e4f400237545b87b996b")
        if claim != "SINGLE_V2_CONTRACT_ONLY":
            poly = claim
    downloaded = [item["era"] for item in eras if item["downloaded_for_this_case"]]
    if downloaded:
        changed = "NOT_DEMONSTRATED"
    else:
        changed = "NO_NEW_DATA_ON_THIS_CASE"
    return {
        "case_id": case["case_id"],
        "prior_path": case["prior_path"],
        "prior_conclusion_unchanged_unless_noted": case["prior_conclusion"],
        "poly_data_v2": poly,
        "pendulum": eras,
        "new_wallet_link": False,
        "conclusion_change": changed,
    }


def replay_all(downloaded_eras: tuple[str, ...] = ()) -> list[dict]:
    return [replay_case(case, downloaded_eras) for case in CASES]
