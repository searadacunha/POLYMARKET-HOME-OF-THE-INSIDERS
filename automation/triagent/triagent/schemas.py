"""Strict output schemas (OpenAI strict mode: every property required, no extra keys)."""
from __future__ import annotations

TIER = {"type": "string", "enum": ["CONFIRMED", "SUPPORTED", "HYPOTHESIS", "REFUTED", "UNRESOLVED"]}
STR_LIST = {"type": "array", "items": {"type": "string"}}


def obj(props: dict, **extra) -> dict:
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False, **extra}


FINDING = obj({"statement": {"type": "string"}, "tier": TIER, "evidence_ids": STR_LIST,
               "alternative_explanations": STR_LIST})
EDGE = obj({"src": {"type": "string"}, "dst": {"type": "string"},
            "kind": {"type": "string", "enum": ["DIRECT_TRANSFER", "SAME_FUNDER", "SAME_DEPOSIT_ADDRESS",
                                                "BRIDGE_ORDER", "SHARED_SERVICE", "TEMPORAL_CORRELATION",
                                                "HYPOTHESIS"]},
            "chain": {"type": "string"}, "tx_hash": {"type": "string"}, "token": {"type": "string"},
            "amount": {"type": "string"}, "timestamp": {"type": "integer"}, "method": {"type": "string"}})
METHOD = obj({"method": {"type": "string"}, "version": {"type": "string"},
              "window_start": {"type": "integer"}, "window_end": {"type": "integer"},
              "scope": {"type": "string"},
              "outcome": {"type": "string", "enum": ["positive", "negative", "inconclusive"]}})

CLAUDE_REPORT = obj({
    "summary": {"type": "string"},
    "findings": {"type": "array", "items": FINDING},
    "edges": {"type": "array", "items": EDGE},
    "wallets_examined": STR_LIST,
    "methods_used": {"type": "array", "items": METHOD},
    "negative_results": STR_LIST,
    "unresolved": STR_LIST,
    "disproof_tests": STR_LIST,
    "code_changes": {"type": "string"},
})

X_LEAD = obj({"claim": {"type": "string"}, "post_url": {"type": "string"}, "post_id": {"type": "string"},
              "posted_at": {"type": "string"}, "addresses": STR_LIST, "transactions": STR_LIST,
              "first_hand": {"type": "boolean"}, "proposed_onchain_check": {"type": "string"},
              "already_in_repo": {"type": "boolean"}})
GROK_REPORT = obj({"summary": {"type": "string"}, "leads": {"type": "array", "items": X_LEAD},
                   "unresolved": STR_LIST, "proposed_tests": STR_LIST})

FOLLOWUP = obj({
    "agent": {"type": "string", "enum": ["claude", "grok"]},
    "kind": {"type": "string", "enum": ["analysis", "develop", "x_research"]},
    "novelty_key": {"type": "string"},
    "task": {"type": "string"},
    "falsifier": {"type": "string"},
    "expected_information_gain": {"type": "integer", "minimum": 1, "maximum": 5},
    "est_cost_usd": {"type": "number"},
})

REVIEW = obj({
    "analysis": {"type": "string"},
    "claims": {"type": "array", "items": obj({"statement": {"type": "string"}, "tier": TIER,
                                              "evidence_ids": STR_LIST, "objection": {"type": "string"}})},
    "novelty": {"type": "integer", "minimum": 0, "maximum": 5},
    "novelty_reason": {"type": "string"},
    "duplicates_existing": STR_LIST,
    "calculation_checks": STR_LIST,
    "temporal_consistency": {"type": "string"},
    "falsification_tests": STR_LIST,
    "decision": {"type": "string", "enum": ["continue", "stop_no_new_information",
                                            "stop_insufficient_basis", "needs_human"]},
    "followups": {"type": "array", "items": FOLLOWUP},
    "risks": STR_LIST,
})

PLAN = obj({"tasks": {"type": "array", "items": FOLLOWUP}, "no_useful_lead_reason": {"type": "string"}})
