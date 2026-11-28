# Graph viewer

`phi_forensics.viz` turns the JSON answers of the toolkit into one HTML page that opens offline: a graph of the money
relations, the funding sources, the withdrawal destinations, the graded links, the clusters, a timeline and a table of
every transfer. The page draws only what the answers contain. It infers nothing and it does not say who controls an
address.

Example built from published evidence: [`examples/nobel-funding.html`](examples/nobel-funding.html) (download it and
open it in a browser; the input is [`examples/nobel-funding.input.json`](examples/nobel-funding.input.json)).

## Build a graph for a set of wallets

The first three commands read public APIs and Polygon nodes; the last two run offline.

```sh
# graded links and clusters among 2 to 25 wallets
python3 -m phi_forensics link_wallets --wallets 0xWALLET_A 0xWALLET_B 0xWALLET_C > links.json
# deposits and withdrawals of each wallet, with every counterparty classified at the block of its payment
python3 -m phi_forensics trace_funding --wallet 0xWALLET_A > funding_a.json
# optional: payers (upstream) or payees (downstream) of an address around a block
python3 -m phi_forensics trace_address --address 0xWALLET_A --direction downstream --at_block 77500000 > trace_a.json

python3 -m phi_forensics.viz build links.json funding_a.json trace_a.json graph.html --title "Wallets A, B and C"
python3 -m phi_forensics.viz serve . --port 8080      # or open graph.html directly
```

`build` takes one or more input files and writes the page to the last path. An input file holds one answer
(`link_wallets`, `trace_funding`, `trace_address`, or a bare list of links or clusters from `phi_forensics.cluster`),
or `{"answers": [...], "sources": [...]}` when the sources of the answers should be named on the page. The same
input gives the same bytes.

The kind of an address (protocol, labelled service, contract, high-volume key, key) comes from `trace_funding` and
`trace_address`. `link_wallets` does not return the kinds it used, so with its answer alone every counterparty is shown
as "kind not established"; add the `trace_funding` answers of the wallets to see them. Labels also come from the
registry of the package (`phi_forensics/registry.py`).

From Python:

```python
from phi_forensics import viz
page = viz.render_html(viz.graph_document(links_answer, funding_answer), "Wallets A, B and C")
```

`serve` uses the standard library HTTP server, binds to 127.0.0.1 unless `--host` says otherwise, and sends a
Content-Security-Policy that forbids every request a page could make. `deploy/viewer/` holds a container image that
runs it read-only, as a non-root user, with a health check.

## How to read the page

| Style | Meaning |
|---|---|
| Solid arrow | A demonstrated payment: one or more token transfers read from the chain, from payer to payee. The label counts them. |
| Thick solid line | `COMMON_CONTROL_DEMONSTRATED`: the same key can sign for both smart wallets. |
| Solid line | `FINANCIAL_RELATION_DEMONSTRATED`: money moved between the wallets or through one non-service address. One owner is not shown. |
| Dashed line, labelled with its grade | `PROBABLE_COORDINATION` or any other grade that is not a demonstrated relation. Hidden by default. |
| Dashed ring around an address | `NOT_A_LINK`: a shared service, drawn as a service and never as a line between its users. Hidden by default. |
| Square node | An address classified as a service: protocol, labelled service, contract, high-volume key, mint. |
| Circle node, dotted outline | An address whose kind is not established. |
| Filled node | One of the investigated wallets. |

Investigated wallets sit in the middle column, payers to the left and payees to the right, one column per hop. The
filters show demonstrated relations only until another grade is ticked.

Selecting a line, a node or a table row (mouse, or Tab then Enter) opens the evidence panel: transaction hash, log
index, block, time, token, exact amount, the evidence level when the input records one, and the command that re-reads
the transfer from two independent Polygon nodes:

```sh
python3 -m phi_forensics verify_transfer --transaction 0x... --sender 0x... --recipient 0x... --token 0x... --amount 40000.000000 --log_index 611
```

The command is shown only when every field is well formed. The block explorer link is a plain link: nothing is fetched
until it is followed.

The table of all transfers repeats every edge as text for screen readers and for copying.

## What the page does not show

- Who controls an address. A transfer is a movement of money between two addresses.
- That the same money continued along a path: tokens are fungible.
- Relations the answers do not contain. A missing line is not evidence that no relation exists: money can pass through
  an exchange, a bridge or another chain, and `link_wallets` counts the popularity of a shared address inside the set
  of wallets only.
- Transfers beyond what the answers list. `trace_funding` returns the first 200 deposits and withdrawals; the page
  states it in its limits when a list was shortened. A link shows at most 12 of its supporting transfers and gives
  their total count.

Each answer's own `limits` are listed at the end of the page.

## Safety of the page

Addresses, labels and titles come from third parties. The page embeds the document as JSON that cannot close its
script element, and builds every element with `textContent` and `setAttribute`: no value is parsed as markup. A
Content-Security-Policy meta tag allows only the page's own script and style (by hash) and forbids every network
request, images, fonts, frames and forms. `phi_forensics/tests/test_viz.py` checks these properties.

## The example

`docs/examples/build_nobel_funding_example.py` builds the example from files this repository already publishes:

- the 14 transfers of finding F-001 of `investigations/followup-20261113` (`sources/data/nobel_funding_transfers.csv`),
  with the level that `FINDINGS.md` records for that finding (CONFIRMED);
- their log indexes and token contracts from `research_notes/nobel-strict-replay-2026-11-20/data/accounts_inflows.csv`,
  matched on transaction, sender, recipient and amount; the script stops if a transfer does not match exactly one log.

It draws no graded link and no withdrawal: the source records the transfers, the withdrawals of F-002 went through
Relay orders, and finding F-007 (one person controls the eight accounts) is UNRESOLVED. Rebuild or check it with:

```sh
python3 docs/examples/build_nobel_funding_example.py           # rewrite the input and the page
python3 docs/examples/build_nobel_funding_example.py --check   # exit 1 if the committed files differ
```

## Limits

- The layout is a fixed column layout, not a force simulation: a wallet with hundreds of counterparties gives a tall
  column that scrolls.
- Several transfers between the same two addresses are drawn as one arrow with a count; each is listed in the panel.
- The page reads collateral transfers on Polygon only, because the toolkit does.
- The container image (`deploy/viewer/`) is built and tested by `.github/workflows/viewer-image.yml`; the Python base
  image is pinned by tag, not by digest.
