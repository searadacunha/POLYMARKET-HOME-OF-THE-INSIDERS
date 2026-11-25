"""Redeem-closed inventory, as an accounting identity on caller-supplied lots.

Nothing in this module is a Polymarket observation. Tests pass synthetic lots
and must keep them labelled as such. A redemption of outcome slot k pays one
unit per remaining share of k and zero for every other slot of that condition.
"""


def settle(lots, redemptions):
    """lots: list of {condition, slot, shares, cost}. redemptions: {condition: winning_slot}."""
    inventory = {}
    for lot in lots:
        key = (lot["condition"], int(lot["slot"]))
        shares, cost = inventory.get(key, (0.0, 0.0))
        inventory[key] = (shares + float(lot["shares"]), cost + float(lot["cost"]))
    payout = 0.0
    cost_closed = 0.0
    open_lots = []
    for (condition, slot), (shares, cost) in inventory.items():
        if condition not in redemptions:
            open_lots.append({"condition": condition, "slot": slot, "shares": shares, "cost": cost})
            continue
        won = int(redemptions[condition]) == slot
        payout += shares if won else 0.0
        cost_closed += cost
    return {
        "payout": payout,
        "cost_closed": cost_closed,
        "realized": payout - cost_closed,
        "open_lots": open_lots,
        "synthetic": True,
    }
