---
id: counterparty-network
title: Counterparty execution graph and C7 archival reconciliation
state: IN_PROGRESS
updated_utc: 2026-11-16T18:10:00Z
origin: Existing published C7 archive and public V2 protocol documentation
version: initial independent follow-up 2026-11-16
---

## Objective

Build an independently authored, point-in-time framework for executed counterparty networks and check whether such structures can eventually provide a tradeable signal beyond price.

## Actual state

The four archived C7 rows have been recalculated; an isolated V2 graph summarizer and unit tests are added. No fresh Polygon receipts were fetched for this addition. No full-market graph, negative-control study or live profitability test has been completed.

## Conclusions

The C7 archival relationship is arithmetically reproducible. Real V2 maker-taker observations can supply edges that are different from source-of-funds links. These observations do not yet show market-predictive value.

## Limits

The C7 CSV is a curated archive rather than freshly independently decoded receipts. There is no matched random-market control, no identification of informed traders, and no verified trading alpha. External research results are discussed only with provenance.

## Links

The findings, external-source review and prospective test plan are inside this investigation folder.
