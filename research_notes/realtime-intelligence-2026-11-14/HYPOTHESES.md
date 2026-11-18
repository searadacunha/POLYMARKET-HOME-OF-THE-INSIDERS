# Hypotheses of this study, and why they are not the earlier ones

Earlier work in this repository started from a price that jumps and asked who bought
([SIGNALS_REGISTER.md](SIGNALS_REGISTER.md)). Nothing passed, and the blind audit of the last study named three
reasons that did not depend on the rule tested: the sample was conditioned on a move of the price, it was conditioned
on the closing date of the market, and the reference price was the last trade whatever its size.

This study turns the question around. It starts from the purchase.

| | Earlier studies | This study |
|---|---|---|
| Unit | a price jump of one side of a market | the first fill of 1,000 USD or more of a wallet on a side of a market, whether or not the price moved |
| Population | markets with a jump in their last 14 days | every such purchase on 32,552 markets, over their whole life |
| Date of a market | when it really closed | its scheduled end, known in advance |
| Reference price | the last trade before the alert, sometimes a few dollars | the price the alerted wallet itself paid for 1,000 USD or more |
| Who is examined | the leading buyer of a jump | every large buyer |
| Control | other jumps | ordinary large purchases at the same price and horizon |

## The six families asked for, and what was done with each

**A. Funding before buying.** A deposit shortly before a purchase is common: on Polymarket, new customers deposit and
bet. Earlier counts in this repository had already shown that it does not single anybody out. What had never been
measured is whether it *pays*: do such purchases win more than their price says? Three classes ask it. `C1` requires
a wallet with almost no history and money received in the 24 hours before: a deposit row, or collateral received on
the chain from outside Polymarket's contracts (the activity listing names only some ways of funding). `C7` is a `C1`
wallet whose net buying of the side reaches 10,000 USD within 24 hours. `R1` is the rule `S_FRESH` of the Maduro and
Iran file, which was pre-registered there, came out "promising, weak" on 30 events, and was to be retested unchanged on
a larger sample: a wallet 48 hours old or less, dated by its first inflow of collateral, with at most two earlier large
fills. A first draft of `C1` also asked for half of the recent deposits on one side; read on the discovery wallets
before any outcome, that condition selected almost nothing and missed the documented Nobel account, and it was dropped
before the freeze ([RESULTS.md](RESULTS.md) lists every correction).

**B. Coordinated accumulation.** The Nobel 2025 case is one key paying eight accounts. The question left open was how
often that structure exists on ordinary markets. `C4` fires when a second wallet funded by the same plain key enters
the same event within seven days. To make this countable at all, the payer of a deposit had to be read correctly: the
deposit shown in a wallet's activity is often a swap of the wallet's own money by a pool, and the key that sent the
money is in an earlier transaction. A reader that stops at the receipt finds a pool and no group, including on the
Nobel case itself.

**C. Abnormal conviction.** Each purchase is compared with the wallet's own past, not with a dollar threshold. `C3`
fires when a fill is ten times the median of at least 20 earlier trades spread over at least a week, and larger than
all of them. `C2` fires when a wallet whose last trade on another market is 60 days old or more receives fresh money. Neither had
been frozen as a class before.

**D. Microstructure.** Order books are not kept by the venue. What this study can test on two years is whether the
purchase came after a move (`B2`, a baseline) and how much of the buying of a side the wallet did. A real test of book
depth, spread and imbalance needs books recorded before the outcome. Two such recordings exist locally: nine days of
October 2026 on 650 markets, and the collector started on 13 November 2026 on 20 markets that end in 2027 or later.
Neither was scored here: the first is 10 GB on a slow disk with unverified completeness, the second has no outcome
before 2027 and one book in four that can be rebuilt ([SYSTEM_AUDIT.md](SYSTEM_AUDIT.md)). **Not evaluated.** The live
engine records what would be needed, on the markets where entries occur.

**E. Recurring networks.** `C5` fires when the plain key behind a wallet's deposit was already behind a wallet that
entered a different event at least a week earlier. The graph of keys and wallets is built over the whole period, and
every link is a transfer read on chain.

**F. Combined signals.** Three ways, all fixed before any outcome was read. `C6` is a hand-written combination: a `C1`
entry on a market where nobody else traded 1,000 USD in the 6 hours before, at 0.50 or less. `M1` is a rarity score: for eight features, how rare the value is
in the discovery population, summed. `M2` is an isolation forest on fourteen features. Neither `M1` nor `M2` uses an
outcome. `M3` is the only model that does: a logistic model of the outcome with the price as offset, fitted on the
discovery set only, so that it can learn combinations nobody wrote down. Its top 5 % is then tested on the validation
set like any other class.

## Baselines

A class is only interesting if it beats something simple. Three baselines go through the same tests: size alone
(`B1`, a fill of 10,000 USD or more), momentum (`B2`, a price 0.10 above the last trade an hour earlier), and newness
alone (`B3`, a wallet with almost no history and no fresh deposit).

## The negative control

Markets whose outcome is a public process (a season of sport, a listed price, a public counter) are analysed apart.
Nobody can hold those outcomes in advance. A class that "works" there is detecting something else than private
information: skill, speed, or a flaw of the method.

## What "works" means here

A class is supported when its alerts, one per event, win more often than the prices paid say, **and** more often than
ordinary large purchases at the same price and horizon, by at least five points, after correction for every comparison
made. The second condition matters: if all large purchases beat their price a little, a class that only inherits that
is not a signal.

No class, whatever its verdict, says anything about one account. A supported class would be a kind of trade that was
profitable over this period.

## What this design cannot see

- A purchase split into fills under 1,000 USD opens no entry.
- Markets under 10,000 USD of volume, and events under 50,000 USD, are outside.
- Money that arrives through a bridge or an exchange stops there: only keys that pay on Polygon can link two wallets.
- Orders that are never filled.
- Anything about who a trader is.
