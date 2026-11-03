# Graph of the traced accounts

Written by `engine/tools/build_graph.py` from every `trace.json` at the date of the run. Partial: it holds only the accounts traced so far, and light traces stop early.

Money is not identity. An edge shows a transfer or a read, never a common owner. Hubs, services and contracts cannot join two files.

| Item | Value |
|---|---:|
| Files traced | 116 |
| Addresses | 3343 |
| Relations | 7211 |
| Layer financial | 1453 |
| Layer control | 116 |
| Layer infrastructure | 3108 |
| Layer behaviour | 0 |
| Layer market | 2534 |
| Addresses shared by files on the money layer | 12 |

## Files

| File | Group | Mode | Polymarket history complete | Edges | Stops |
|---|---|---|---|---:|---|
| 0x86544e4dfde | ballon-dor-named | full | True | 47 | SERVICE_OR_SHARED 31, NO_FLOW_IN_WINDOW 16, NO_LATER_OUTFLOW 5, WINDOW_SCAN_NEEDED 2, DUST_NOT_FOLLOWED 1 |
| 0xdd97e6 | ballon-dor-named | full | True | 4 | NO_FLOW_IN_WINDOW 10, NO_LATER_OUTFLOW 7, WINDOW_SCAN_NEEDED 1 |
| brace227 | ballon-dor-named | full | True | 209 | SERVICE_OR_SHARED 161, NO_LATER_OUTFLOW 34, NO_FLOW_IN_WINDOW 7, DUST_NOT_FOLLOWED 5, WINDOW_SCAN_NEEDED 4, BRIDGE_HOP_NOT_PROVEN 1 |
| burdensome-mix | federal-case | full | True | 13 | SERVICE_OR_SHARED 13, AMBIGUOUS_PATH 1 |
| chileno777 | maduro-iran-network | full | True | 7 | SERVICE_OR_SHARED 7 |
| chiwawas | maduro-iran-network | full | True | 429 | SERVICE_OR_SHARED 308, NO_LATER_OUTFLOW 53, DUST_NOT_FOLLOWED 3, HISTORY_INCOMPLETE 1, HUB_AT_READ 1, WINDOW_SCAN_NEEDED 1 |
| cn-0x09b831e67e | changenow-26 | light: depth 2, 14 nodes, 12 largest flows per node, 30 money rows | False | 52 | SERVICE_OR_SHARED 24, NO_FLOW_IN_WINDOW 10, DEPTH_BUDGET 9, NODE_BUDGET 4, NO_LATER_OUTFLOW 4, WINDOW_SCAN_NEEDED 2, LIGHT_FLOW_CAP 2, DUST_NOT_FOLLOWED 1 |
| cn-0x12852f9976 | changenow-26 | light: depth 2, 14 nodes, 12 largest flows per node, 30 money rows | True | 0 |  |
| cn-0x14d03db8fb | changenow-26 | light: depth 2, 14 nodes, 12 largest flows per node, 30 money rows | True | 54 | NODE_BUDGET 62, SERVICE_OR_SHARED 30, NO_LATER_OUTFLOW 9, NO_FLOW_IN_WINDOW 8, DUST_NOT_FOLLOWED 2, LIGHT_FLOW_CAP 1 |
| cn-0x19bb95ea82 | changenow-26 | light: depth 2, 14 nodes, 12 largest flows per node, 30 money rows | True | 30 | NODE_BUDGET 50, SERVICE_OR_SHARED 19, NO_FLOW_IN_WINDOW 9, NO_LATER_OUTFLOW 9, WINDOW_SCAN_NEEDED 2 |
| cn-0x227ce6a529 | changenow-26 | light: depth 2, 14 nodes, 12 largest flows per node, 30 money rows | True | 6 | NO_FLOW_IN_WINDOW 10, NO_LATER_OUTFLOW 10, SERVICE_OR_SHARED 4 |
| cn-0x3067fecf27 | changenow-26 | light: depth 2, 14 nodes, 12 largest flows per node, 30 money rows | True | 32 | NODE_BUDGET 28, SERVICE_OR_SHARED 9, NO_FLOW_IN_WINDOW 9, NO_LATER_OUTFLOW 4, BRIDGE_HOP_NOT_PROVEN 3, WINDOW_SCAN_NEEDED 2, LIGHT_FLOW_CAP 1 |
| cn-0x3591ac128a | changenow-26 | light: depth 2, 14 nodes, 12 largest flows per node, 30 money rows | True | 79 | SERVICE_OR_SHARED 57, NODE_BUDGET 20, NO_FLOW_IN_WINDOW 8, NO_LATER_OUTFLOW 8, LIGHT_FLOW_CAP 6, DUST_NOT_FOLLOWED 3, WINDOW_SCAN_NEEDED 3 |
| cn-0x391112d827 | changenow-26 | light: depth 2, 14 nodes, 12 largest flows per node, 30 money rows | True | 27 | SERVICE_OR_SHARED 16, NO_LATER_OUTFLOW 11, NO_FLOW_IN_WINDOW 8, NODE_BUDGET 4, DUST_NOT_FOLLOWED 1 |
| cn-0x4a4f1fbc70 | changenow-26 | light: depth 2, 14 nodes, 30 money rows | False | 142 | SERVICE_OR_SHARED 110, NODE_BUDGET 21, NO_FLOW_IN_WINDOW 10, NO_LATER_OUTFLOW 9, BRIDGE_HOP_NOT_PROVEN 2, DUST_NOT_FOLLOWED 1 |
| cn-0x55bb88498e | changenow-26 | light: depth 2, 14 nodes, 12 largest flows per node, 30 money rows | True | 6 | NO_FLOW_IN_WINDOW 11, NO_LATER_OUTFLOW 6, SERVICE_OR_SHARED 4, NODE_BUDGET 4 |
| cn-0x5c1aad9549 | changenow-26 | light: depth 2, 14 nodes, 30 money rows | True | 99 | SERVICE_OR_SHARED 65, NO_LATER_OUTFLOW 9, NO_FLOW_IN_WINDOW 6, NODE_BUDGET 6, DUST_NOT_FOLLOWED 4, WINDOW_SCAN_NEEDED 2 |
| cn-0x6e793da348 | changenow-26 | light: depth 2, 14 nodes, 12 largest flows per node, 30 money rows | True | 2 | NO_LATER_OUTFLOW 6, NO_FLOW_IN_WINDOW 5, SERVICE_OR_SHARED 2, DUST_NOT_FOLLOWED 1 |
| cn-0x7678aa83a3 | changenow-26 | light: depth 2, 14 nodes, 12 largest flows per node, 30 money rows | True | 0 | NO_FLOW_IN_WINDOW 6, NO_LATER_OUTFLOW 6 |
| cn-0x814fd93538 | changenow-26 | light: depth 2, 14 nodes, 12 largest flows per node, 30 money rows | True | 12 | NO_LATER_OUTFLOW 11, SERVICE_OR_SHARED 9, NO_FLOW_IN_WINDOW 9, NODE_BUDGET 4 |
| cn-0xa8566ea1e9 | changenow-26 | light: depth 2, 14 nodes, 12 largest flows per node, 30 money rows | True | 30 | NODE_BUDGET 38, SERVICE_OR_SHARED 9, NO_LATER_OUTFLOW 9, NO_FLOW_IN_WINDOW 8, WINDOW_SCAN_NEEDED 2 |
| cn-0xadd9ab62b2 | changenow-26 | light: depth 2, 14 nodes, 30 money rows | False | 0 |  |
| cn-0xaf0f3a3f50 | changenow-26 | light: depth 2, 14 nodes, 12 largest flows per node, 30 money rows | True | 0 |  |
| cn-0xc31ed9f0f0 | changenow-26 | light: depth 2, 14 nodes, 12 largest flows per node, 30 money rows | True | 53 | NODE_BUDGET 92, SERVICE_OR_SHARED 23, NO_LATER_OUTFLOW 8, NO_FLOW_IN_WINDOW 5, WINDOW_SCAN_NEEDED 5, DUST_NOT_FOLLOWED 4, LIGHT_FLOW_CAP 3 |
| cn-0xd18ef9f072 | changenow-26 | light: depth 2, 14 nodes, 12 largest flows per node, 30 money rows | True | 39 | NODE_BUDGET 26, SERVICE_OR_SHARED 16, NO_FLOW_IN_WINDOW 10, NO_LATER_OUTFLOW 8, WINDOW_SCAN_NEEDED 3, LIGHT_FLOW_CAP 2, DUST_NOT_FOLLOWED 1, BRIDGE_HOP_NOT_PROVEN 1 |
| cn-0xd55776adc3 | changenow-26 | light: depth 2, 14 nodes, 12 largest flows per node, 30 money rows | True | 24 | NODE_BUDGET 34, SERVICE_OR_SHARED 15, NO_LATER_OUTFLOW 10, NO_FLOW_IN_WINDOW 9, WINDOW_SCAN_NEEDED 2, LIGHT_FLOW_CAP 1 |
| cn-0xd55dad050d | changenow-26 | light: depth 2, 14 nodes, 12 largest flows per node, 30 money rows | True | 12 | NO_FLOW_IN_WINDOW 11, NO_LATER_OUTFLOW 10, SERVICE_OR_SHARED 9, NODE_BUDGET 4 |
| cn-0xd67b91b9ce | changenow-26 | light: depth 2, 14 nodes, 12 largest flows per node, 30 money rows | True | 18 | NODE_BUDGET 22, SERVICE_OR_SHARED 11, NO_LATER_OUTFLOW 9, NO_FLOW_IN_WINDOW 3 |
| cn-0xd7e5841553 | changenow-26 | light: depth 2, 14 nodes, 12 largest flows per node, 30 money rows | True | 14 | SERVICE_OR_SHARED 13, NO_LATER_OUTFLOW 9, NO_FLOW_IN_WINDOW 3, WINDOW_SCAN_NEEDED 2, DUST_NOT_FOLLOWED 1 |
| cn-0xdec4c18831 | changenow-26 | light: depth 2, 14 nodes, 12 largest flows per node, 30 money rows | True | 18 | NODE_BUDGET 22, SERVICE_OR_SHARED 12, NO_FLOW_IN_WINDOW 10, NO_LATER_OUTFLOW 9, WINDOW_SCAN_NEEDED 2, DUST_NOT_FOLLOWED 1 |
| cn-0xe0bf7ab5b1 | changenow-26 | light: depth 2, 14 nodes, 12 largest flows per node, 30 money rows | False | 50 | SERVICE_OR_SHARED 28, NO_FLOW_IN_WINDOW 9, NO_LATER_OUTFLOW 9, NODE_BUDGET 8, WINDOW_SCAN_NEEDED 3, DUST_NOT_FOLLOWED 2, DEPTH_BUDGET 2, LIGHT_FLOW_CAP 1 |
| cn-0xf0b29b5cf6 | changenow-26 | light: depth 2, 14 nodes, 12 largest flows per node, 30 money rows | True | 29 | SERVICE_OR_SHARED 24, NODE_BUDGET 16, NO_LATER_OUTFLOW 10, NO_FLOW_IN_WINDOW 4, LIGHT_FLOW_CAP 1 |
| cookedrice | ballon-dor-named | full | True | 3 | NO_FLOW_IN_WINDOW 11, NO_LATER_OUTFLOW 6, BRIDGE_HOP_NOT_PROVEN 2 |
| d-0x000d257d2d | discovery | light: depth 2, 14 nodes, 30 money rows | False | 169 | SERVICE_OR_SHARED 165, AMBIGUOUS_PATH 25, NO_LATER_OUTFLOW 9 |
| d-0x0026ca70e9 | discovery | light: depth 2, 14 nodes, 30 money rows | False | 140 | NODE_BUDGET 158, SERVICE_OR_SHARED 85, NO_FLOW_IN_WINDOW 10, NO_LATER_OUTFLOW 10, DUST_NOT_FOLLOWED 1 |
| d-0x02c1ec85e7 | discovery | light: depth 2, 14 nodes, 30 money rows | True | 22 | SERVICE_OR_SHARED 22, AMBIGUOUS_PATH 1 |
| d-0x02f236089f | discovery | light: depth 2, 14 nodes, 30 money rows | True | 16 | SERVICE_OR_SHARED 16, AMBIGUOUS_PATH 14 |
| d-0x03f8aae7ae | discovery | light: depth 2, 14 nodes, 30 money rows | True | 1 | NO_FLOW_IN_WINDOW 6, NO_LATER_OUTFLOW 6, AMBIGUOUS_PATH 1, SERVICE_OR_SHARED 1 |
| d-0x04bf21c252 | discovery | light: depth 2, 14 nodes, 30 money rows | False | 28 | SERVICE_OR_SHARED 28, NO_FLOW_IN_WINDOW 6, NO_LATER_OUTFLOW 6, AMBIGUOUS_PATH 2 |
| d-0x05670a9813 | discovery | light: depth 2, 14 nodes, 12 largest flows per node, 30 money rows | True | 74 | SERVICE_OR_SHARED 49, NODE_BUDGET 34, NO_FLOW_IN_WINDOW 10, NO_LATER_OUTFLOW 10, LIGHT_FLOW_CAP 2, AMBIGUOUS_PATH 1, BRIDGE_HOP_NOT_PROVEN 1 |
| d-0x0573b1fc54 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 11 | BRIDGE_HOP_NOT_PROVEN 6, NO_FLOW_IN_WINDOW 3, NO_LATER_OUTFLOW 3, SERVICE_OR_SHARED 2 |
| d-0x05e26c775e | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | False | 20 | SERVICE_OR_SHARED 20, AMBIGUOUS_PATH 10 |
| d-0x0645d65c4f | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 63 | SERVICE_OR_SHARED 44, AMBIGUOUS_PATH 19, NODE_BUDGET 7, LIGHT_FLOW_CAP 5, DUST_NOT_FOLLOWED 2, NO_FLOW_IN_WINDOW 1, NO_LATER_OUTFLOW 1 |
| d-0x06c0d07d5b | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | False | 20 | SERVICE_OR_SHARED 20, AMBIGUOUS_PATH 3 |
| d-0x088ffbbc6f | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | False | 80 | SERVICE_OR_SHARED 55, AMBIGUOUS_PATH 18, LIGHT_FLOW_CAP 9, NODE_BUDGET 7, DUST_NOT_FOLLOWED 4, NO_FLOW_IN_WINDOW 2, NO_LATER_OUTFLOW 2, HISTORY_INCOMPLETE 1, DEPTH_BUDGET 1 |
| d-0x0a26054fe1 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | False | 51 | SERVICE_OR_SHARED 37, AMBIGUOUS_PATH 16, LIGHT_FLOW_CAP 3, NO_LATER_OUTFLOW 2, NODE_BUDGET 1 |
| d-0x0a39f55ae1 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | False | 89 | SERVICE_OR_SHARED 57, LIGHT_FLOW_CAP 9, AMBIGUOUS_PATH 7, NODE_BUDGET 5, DUST_NOT_FOLLOWED 4, NO_FLOW_IN_WINDOW 2, DEPTH_BUDGET 2, NO_LATER_OUTFLOW 1 |
| d-0x0e9310b9a1 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | False | 9 | SERVICE_OR_SHARED 6, AMBIGUOUS_PATH 1, NO_FLOW_IN_WINDOW 1 |
| d-0x0ee4357446 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | False | 30 | SERVICE_OR_SHARED 10, NO_FLOW_IN_WINDOW 2, AMBIGUOUS_PATH 1 |
| d-0x0fe90c2282 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 8 | AMBIGUOUS_PATH 22, SERVICE_OR_SHARED 8 |
| d-0x114651b7ad | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 8 | SERVICE_OR_SHARED 6 |
| d-0x168b100d7a | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 9 | SERVICE_OR_SHARED 9 |
| d-0x18a0a99716 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 1 | AMBIGUOUS_PATH 4, SERVICE_OR_SHARED 1 |
| d-0x18bbf3c90b | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 45 | NODE_BUDGET 35, SERVICE_OR_SHARED 27, LIGHT_FLOW_CAP 5, DUST_NOT_FOLLOWED 4, NO_FLOW_IN_WINDOW 4, NO_LATER_OUTFLOW 3 |
| d-0x19974ce598 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | False | 32 | SERVICE_OR_SHARED 7, NO_FLOW_IN_WINDOW 2, WINDOW_SCAN_NEEDED 2, BRIDGE_HOP_NOT_PROVEN 1 |
| d-0x19c5ed7a84 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 35 | SERVICE_OR_SHARED 14, NODE_BUDGET 13, NO_FLOW_IN_WINDOW 3, LIGHT_FLOW_CAP 3, NO_LATER_OUTFLOW 2, AMBIGUOUS_PATH 1, DUST_NOT_FOLLOWED 1 |
| d-0x1a56e000bf | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 23 | SERVICE_OR_SHARED 20, NO_FLOW_IN_WINDOW 1 |
| d-0x1b2277a6e3 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 90 | SERVICE_OR_SHARED 76, LIGHT_FLOW_CAP 7, NODE_BUDGET 7, DUST_NOT_FOLLOWED 4, AMBIGUOUS_PATH 2, NO_LATER_OUTFLOW 2, NO_FLOW_IN_WINDOW 1 |
| d-0x1c0773fd87 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 45 | SERVICE_OR_SHARED 23, DUST_NOT_FOLLOWED 2, LIGHT_FLOW_CAP 2, HUB_AT_READ 1, DEPTH_BUDGET 1 |
| d-0x1c587df39e | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 24 | SERVICE_OR_SHARED 23, AMBIGUOUS_PATH 3, NO_FLOW_IN_WINDOW 3, NO_LATER_OUTFLOW 3, LIGHT_FLOW_CAP 1 |
| d-0x1caa6a7ad0 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 13 | SERVICE_OR_SHARED 13 |
| d-0x1cb63fd92e | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | False | 24 | SERVICE_OR_SHARED 18, AMBIGUOUS_PATH 9, LIGHT_FLOW_CAP 1, NO_FLOW_IN_WINDOW 1 |
| d-0x1cf7feb013 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 25 | SERVICE_OR_SHARED 13, NODE_BUDGET 4, NO_LATER_OUTFLOW 3, NO_FLOW_IN_WINDOW 1, DUST_NOT_FOLLOWED 1, LIGHT_FLOW_CAP 1 |
| d-0x1d3cbeae45 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 23 | SERVICE_OR_SHARED 15, LIGHT_FLOW_CAP 2, BRIDGE_HOP_NOT_PROVEN 2, NO_FLOW_IN_WINDOW 1, NO_LATER_OUTFLOW 1 |
| d-0x1e55bd7f65 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 4 | SERVICE_OR_SHARED 4 |
| d-0x1fce4555b1 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 26 | SERVICE_OR_SHARED 13, NO_FLOW_IN_WINDOW 4, AMBIGUOUS_PATH 1, DUST_NOT_FOLLOWED 1, LIGHT_FLOW_CAP 1, DEPTH_BUDGET 1 |
| d-0x21d9a69fac | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | False | 38 | SERVICE_OR_SHARED 28, AMBIGUOUS_PATH 20, NODE_BUDGET 7, LIGHT_FLOW_CAP 4, NO_LATER_OUTFLOW 4, DUST_NOT_FOLLOWED 1, NO_FLOW_IN_WINDOW 1 |
| d-0x21fe95443d | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 17 | AMBIGUOUS_PATH 19, SERVICE_OR_SHARED 15, NO_FLOW_IN_WINDOW 2, LIGHT_FLOW_CAP 1 |
| d-0x234cc49e43 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 1 | NO_FLOW_IN_WINDOW 3, NO_LATER_OUTFLOW 3, AMBIGUOUS_PATH 2, SERVICE_OR_SHARED 1 |
| d-0x23658ba009 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | False | 25 | SERVICE_OR_SHARED 15, NO_LATER_OUTFLOW 6, AMBIGUOUS_PATH 4, LIGHT_FLOW_CAP 4, NODE_BUDGET 4, DUST_NOT_FOLLOWED 2, NO_FLOW_IN_WINDOW 1 |
| d-0x23f45f43c4 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 84 | SERVICE_OR_SHARED 69, NODE_BUDGET 16, LIGHT_FLOW_CAP 8, DUST_NOT_FOLLOWED 3, NO_LATER_OUTFLOW 2 |
| d-0x247dd6acad | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 28 | SERVICE_OR_SHARED 15, NO_FLOW_IN_WINDOW 5, NODE_BUDGET 5, NO_LATER_OUTFLOW 5, LIGHT_FLOW_CAP 3, AMBIGUOUS_PATH 1 |
| d-0x25a48f6197 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 33 | SERVICE_OR_SHARED 5, NO_FLOW_IN_WINDOW 2, NO_LATER_OUTFLOW 2 |
| d-0x2612496ab8 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 2 | NO_FLOW_IN_WINDOW 3, NO_LATER_OUTFLOW 3, SERVICE_OR_SHARED 2, AMBIGUOUS_PATH 1 |
| d-0x2707f2e693 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | False | 0 | AMBIGUOUS_PATH 11 |
| d-0x274c45994b | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 19 | NODE_BUDGET 11, HUB_AT_READ 4, NO_LATER_OUTFLOW 3, NO_FLOW_IN_WINDOW 1, LIGHT_FLOW_CAP 1 |
| d-0x2771622951 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 13 | SERVICE_OR_SHARED 3, NO_FLOW_IN_WINDOW 1 |
| d-0x2844da5da0 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 16 | SERVICE_OR_SHARED 14, AMBIGUOUS_PATH 5, NO_LATER_OUTFLOW 1 |
| d-0x29d337076f | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | False | 12 | SERVICE_OR_SHARED 9, BRIDGE_HOP_NOT_PROVEN 3, AMBIGUOUS_PATH 1 |
| d-0x29e46ce23a | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 61 | SERVICE_OR_SHARED 35, NODE_BUDGET 20, DUST_NOT_FOLLOWED 6, LIGHT_FLOW_CAP 3, NO_FLOW_IN_WINDOW 3, NO_LATER_OUTFLOW 3, HUB_AT_READ 2 |
| d-0x2bc53bbd26 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 35 | SERVICE_OR_SHARED 27, LIGHT_FLOW_CAP 4, NO_LATER_OUTFLOW 3, NO_FLOW_IN_WINDOW 2, DUST_NOT_FOLLOWED 1 |
| d-0x2c4ca29d33 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | False | 9 | AMBIGUOUS_PATH 8, SERVICE_OR_SHARED 8, NO_LATER_OUTFLOW 4, NO_FLOW_IN_WINDOW 2 |
| d-0x2db3aff0eb | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 32 | SERVICE_OR_SHARED 26, NO_FLOW_IN_WINDOW 2 |
| d-0x2e15d1f000 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 9 | SERVICE_OR_SHARED 9 |
| d-0x2e4ead1dd0 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 34 | SERVICE_OR_SHARED 26, DEPTH_BUDGET 3, NO_FLOW_IN_WINDOW 2, AMBIGUOUS_PATH 1 |
| d-0x2ed75fea1b | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 13 | SERVICE_OR_SHARED 13, NO_FLOW_IN_WINDOW 2, NO_LATER_OUTFLOW 2 |
| d-0x2ef7eb70cc | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 80 | SERVICE_OR_SHARED 44, NODE_BUDGET 18, LIGHT_FLOW_CAP 9, BRIDGE_HOP_NOT_PROVEN 7, DUST_NOT_FOLLOWED 5, NO_FLOW_IN_WINDOW 1, WINDOW_SCAN_NEEDED 1 |
| d-0x2f3360f700 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | False | 34 | SERVICE_OR_SHARED 29, AMBIGUOUS_PATH 10, NO_LATER_OUTFLOW 5, LIGHT_FLOW_CAP 2, DUST_NOT_FOLLOWED 1, NODE_BUDGET 1 |
| d-0x2f79e7b0d8 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | False | 71 | SERVICE_OR_SHARED 64, NODE_BUDGET 10, LIGHT_FLOW_CAP 6, DUST_NOT_FOLLOWED 2, NO_LATER_OUTFLOW 2 |
| d-0x3000b76297 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 1 | AMBIGUOUS_PATH 1, SERVICE_OR_SHARED 1 |
| d-0x30447f52f1 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 21 | SERVICE_OR_SHARED 13, NODE_BUDGET 11, NO_LATER_OUTFLOW 5, NO_FLOW_IN_WINDOW 3, AMBIGUOUS_PATH 2, DUST_NOT_FOLLOWED 2, LIGHT_FLOW_CAP 1 |
| d-0x31a56e9e69 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 13 | SERVICE_OR_SHARED 13, AMBIGUOUS_PATH 1 |
| d-0x31afe55718 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 3 | SERVICE_OR_SHARED 3, NO_FLOW_IN_WINDOW 3, NO_LATER_OUTFLOW 3 |
| d-0x321f2007fa | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 5 | SERVICE_OR_SHARED 4 |
| d-0x34b16f87b0 | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 74 | SERVICE_OR_SHARED 41, NODE_BUDGET 11, LIGHT_FLOW_CAP 5, NO_FLOW_IN_WINDOW 3, AMBIGUOUS_PATH 2, DUST_NOT_FOLLOWED 1 |
| d-0x35a20ffe3d | discovery | light: depth 2, 8 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows | True | 39 | SERVICE_OR_SHARED 29, NODE_BUDGET 7, LIGHT_FLOW_CAP 4, NO_FLOW_IN_WINDOW 3, NO_LATER_OUTFLOW 3, DUST_NOT_FOLLOWED 2 |
| iran-0x1caa6a7a | iran-bubblemaps | full | True | 13 | SERVICE_OR_SHARED 13 |
| kraben006 | ballon-dor-named | full | True | 112 | SERVICE_OR_SHARED 46, NO_FLOW_IN_WINDOW 27, NO_LATER_OUTFLOW 10, WINDOW_SCAN_NEEDED 3, DUST_NOT_FOLLOWED 2, DEPTH_BUDGET 2 |
| linkcs | maduro-iran-other | full | True | 67 | SERVICE_OR_SHARED 30, NO_FLOW_IN_WINDOW 4, BRIDGE_HOP_NOT_PROVEN 2, AMBIGUOUS_PATH 1 |
| mrs-joker | maduro-iran-network | full | True | 6 | SERVICE_OR_SHARED 6 |
| neodbs | maduro-iran-network | full | True | 2 | SERVICE_OR_SHARED 2 |
| nobel-6741 | nobel-2025 | full | True | 389 | NODE_BUDGET 689, SERVICE_OR_SHARED 120, NO_LATER_OUTFLOW 93, NO_FLOW_IN_WINDOW 24, WINDOW_SCAN_NEEDED 6, AMBIGUOUS_PATH 4, DUST_NOT_FOLLOWED 1 |
| nobel-dirtycup | nobel-2025 | full | True | 1 | NO_FLOW_IN_WINDOW 6, NO_LATER_OUTFLOW 6, AMBIGUOUS_PATH 2, SERVICE_OR_SHARED 1 |
| ouldlm3alem | ballon-dor-named | full | True | 19 | SERVICE_OR_SHARED 9, NO_FLOW_IN_WINDOW 8, NO_LATER_OUTFLOW 4, BRIDGE_HOP_NOT_PROVEN 2, WINDOW_SCAN_NEEDED 1 |
| planktonbets | maduro-iran-network | full | True | 4 | SERVICE_OR_SHARED 4 |
| strong-0x6baf05d1 | maduro-iran-other | full | True | 14 | SERVICE_OR_SHARED 11, BRIDGE_HOP_NOT_PROVEN 1 |
| strong-0xa72db174 | maduro-iran-other | full | True | 5 | SERVICE_OR_SHARED 5, AMBIGUOUS_PATH 1 |
| tacticalinsidernews | maduro-iran-network | full | True | 69 | SERVICE_OR_SHARED 53, NO_LATER_OUTFLOW 41, DUST_NOT_FOLLOWED 1 |
| thin | ballon-dor-named | full | True | 9 | NO_FLOW_IN_WINDOW 10, NO_LATER_OUTFLOW 8, WINDOW_SCAN_NEEDED 1, SERVICE_OR_SHARED 1 |
| unnamed-0xa8e64a3c | ballon-dor-linked | full | True | 72 | SERVICE_OR_SHARED 33, NO_FLOW_IN_WINDOW 17, NO_LATER_OUTFLOW 10, WINDOW_SCAN_NEEDED 3, DUST_NOT_FOLLOWED 2, DEPTH_BUDGET 2 |
| vidente | ballon-dor-named | full | True | 6 | NO_FLOW_IN_WINDOW 11, NO_LATER_OUTFLOW 6, SERVICE_OR_SHARED 2 |
| walletwallet8424 | ballon-dor-named | full | True | 18 | NO_FLOW_IN_WINDOW 8, SERVICE_OR_SHARED 6, NO_LATER_OUTFLOW 4, HUB_AT_READ 1, WINDOW_SCAN_NEEDED 1, DUST_NOT_FOLLOWED 1 |
| wen | ballon-dor-named | full | True | 6 | NO_FLOW_IN_WINDOW 11, NO_LATER_OUTFLOW 6, SERVICE_OR_SHARED 3 |
| x154x838hjd6 | maduro-iran-network | full | True | 12 | SERVICE_OR_SHARED 7, NO_LATER_OUTFLOW 5 |
| x34 | maduro-iran-network | full | True | 3 | SERVICE_OR_SHARED 3 |
| zoomman17 | ballon-dor-named | full | True | 57 | SERVICE_OR_SHARED 35, NO_LATER_OUTFLOW 10, NO_FLOW_IN_WINDOW 5 |

`complete` is about Polymarket activity only. It says nothing about funding on other chains: see each file in `results/wallets/` for chains read and stops.

## Addresses shared by files

The relation comes from the direction of the walks. A candidate, read from public money. Ownership is not established for any of them.

| Address | Files | Relation | Class | One proof per file |
|---|---|---|---|---|
| `0x0e9310b9a1bf61ff13d5a31e8ca6188abc8ddb0c` | d-0x0e9310b9a1, linkcs | COMMON_FUNDER_CANDIDATE | POLYMARKET_WALLET | d-0x0e9310b9a1: `0xa053181be4f837c0ba784ead6b5adcb24d6d0216de47e441a002e25ccf8a8017` chain 137, REVERIFIED; linkcs: `0xe9dc7b6aa7246ed8c6b67716b0686b2520ce99ef6179b84e6b1d31bfd2c3ca1e` chain 137, REVERIFIED |
| `0x101b5f4dc0886c32e2b75972101aeaf9f338fb65` | brace227, kraben006 | FUNDING_OF_ONE_EXIT_OF_ANOTHER | PERSONAL_SIZED | brace227: `0xd07bea20a22d9381e0ab364e7a7421776318c6f4aa7258799638472ad7092b98` chain 1, LISTED; kraben006: `0x4431828712a924d5845de5f1779ad98eabf3563d55f299f46dde35700129a5a4` chain 137, REVERIFIED |
| `0x2d507657ca4ebcc8f9a38f6764c07310b66dea54` | cn-0x09b831e67e, cn-0x3067fecf27 | COMMON_FUNDER_CANDIDATE | PERSONAL_SIZED | cn-0x09b831e67e: `0x319a391e54a4878efdf44eaee71f98a186b5bb7a41bc2e3a23466587aff96ed9` chain 137, LISTED; cn-0x3067fecf27: `0xde32bde6ad9dd5d0d334d4d48368ff6c9730e180b8e3f97011cdd0811788e558` chain 137, LISTED |
| `0x48ec106cf690edd58fcd6df1e8b6abfc16dab12d` | brace227, unnamed-0xa8e64a3c | FUNDING_OF_ONE_EXIT_OF_ANOTHER | PERSONAL_SIZED | brace227: `0xb07c3c53a713d98aea1d1bd5d6facf849b6edc675c0fe2cfd3df5b791db20add` chain 1, LISTED; unnamed-0xa8e64a3c: `0x3cd7757ad4fb02e4e30ffdd0ba75575a54c635ca6597bed2a9b6bc0be60cb53a` chain 137, REVERIFIED |
| `0x84212ee459d1edaf35983bbec342b0806282d8ec` | brace227, kraben006 | FUNDING_OF_ONE_EXIT_OF_ANOTHER | POLYMARKET_WALLET | brace227: `0xcccd118f51a843c5f8f01b7e9a31f4435eb55fa97c290e38a45f418ca76a5538` chain 1, LISTED; kraben006: `0x4431828712a924d5845de5f1779ad98eabf3563d55f299f46dde35700129a5a4` chain 137, REVERIFIED |
| `0x8db6758f477290b2530bfb6a5d5f11d3b39b822d` | d-0x0e9310b9a1, linkcs | COMMON_FUNDER_CANDIDATE | PERSONAL_SIZED | d-0x0e9310b9a1: `0xa053181be4f837c0ba784ead6b5adcb24d6d0216de47e441a002e25ccf8a8017` chain 137, REVERIFIED; linkcs: `0xe9dc7b6aa7246ed8c6b67716b0686b2520ce99ef6179b84e6b1d31bfd2c3ca1e` chain 137, REVERIFIED |
| `0x9d7f260b604fe71f4c6df11a1ca907a76520db6c` | cn-0x09b831e67e, cn-0x3067fecf27 | COMMON_FUNDER_CANDIDATE | PERSONAL_SIZED | cn-0x09b831e67e: `0xa25d4fd2b42009a90d433bc5cacedc3d4dd5cca654bf9235816b70846d7a6772` chain 137, LISTED; cn-0x3067fecf27: `0x373f69de2937ebd70deb81354bdbca1dea221bd50e2725a23c19cfac0eca17bd` chain 137, LISTED |
| `0xa254d507504180214898d9b9688455c43514b58a` | cn-0x814fd93538, cn-0xd55dad050d | COMMON_DESTINATION_CANDIDATE | PERSONAL_SIZED | cn-0x814fd93538: `0x5a1a0bc31eed1a3ed2d09c65494194392976d592f73e53984f0f7544704d83da` chain 1, LISTED; cn-0xd55dad050d: `0x9655e5a39d59abfb262a49ad1ecb14648be30843b9f86bd2fa55438c8262d9fe` chain 1, LISTED |
| `0xa8e64a3c08d1e2a4e9f25a2dd33b8ac3458f74a5` | brace227, unnamed-0xa8e64a3c | FUNDING_OF_ONE_EXIT_OF_ANOTHER | POLYMARKET_WALLET | brace227: `0x0f731478649569bce9a570694e2405a4621619d2f8ab7f80d028e51d7dcd90b3` chain 1, LISTED; unnamed-0xa8e64a3c: `0x3cd7757ad4fb02e4e30ffdd0ba75575a54c635ca6597bed2a9b6bc0be60cb53a` chain 137, REVERIFIED |
| `0xbf32f7a77ccea8bba647fea63d438ce1778b1762` | chiwawas, x154x838hjd6 | FUNDING_OF_ONE_EXIT_OF_ANOTHER | POLYMARKET_WALLET | chiwawas: `0xc9924068ead86bfd0eba0f1f72c79419397591d0bace37a3941a0ecb39629a9f` chain 1, LISTED; x154x838hjd6: `0x17039631eda3847bd0417a42e2603d42b3f90b682bf56e61092dbbe075e56a9a` chain 137, REVERIFIED |
| `0xc852b0938f5ad79b640d105ed11c14499454af26` | brace227, kraben006 | COMMON_FUNDER_CANDIDATE | PERSONAL_SIZED | brace227: `0x2a89597ebf1d83b5b76ceccab02924c28ca0ad8f6d208b2c42801a0925280a2c` chain 137, REVERIFIED; kraben006: `0xb17e1c4627ad8914f98f48a4fa7f5916953d3286e60cf3d80c6508257f46ce3c` chain 1, LISTED |
| `0xd4f7d8ac96ed3f467db31fd195faa10676775dab` | chiwawas, x154x838hjd6 | FUNDING_OF_ONE_EXIT_OF_ANOTHER | PERSONAL_SIZED | chiwawas: `0x2ea12eba69c099350383a72a97bba65d20bac110b2133fb95c21cfc080f56ec1` chain 1, LISTED; x154x838hjd6: `0x17039631eda3847bd0417a42e2603d42b3f90b682bf56e61092dbbe075e56a9a` chain 137, REVERIFIED |

## Reading the graph

- `results/graphs/flows.json`: for each file, in time order, who paid in, its markets, what left and where to, with chain, block, block hash, transaction, log index and level on each line.
- `results/graphs/edges.csv`, `edges.json`, `graph.graphml`: every relation with its proof.
- `results/graphs/viewer.html`: filter by layer and file, click a relation to read its proof.
- A bridge hop joins files only when the same id was read on both chains. `results/links/` holds links read hop by hop.
