# TASK: confirm POLYGON (chainid 137) addresses for CCTP and Stargate bridges, with sources

Use web search. I need the on-chain Polygon addresses that would appear as the SENDER /
deliverer of USDC when a bridge transfer is RECEIVED on Polygon. For each, cite a source
(Circle docs, Stargate/LayerZero docs, official GitHub, block-explorer name tag).

Specifically:
1. **Circle CCTP on Polygon (v1 AND v2 if both exist):**
   - MessageTransmitter address (the contract whose receiveMessage mints USDC) — Polygon.
   - TokenMessenger address — Polygon.
   - TokenMinter address — Polygon.
   - Note: on a CCTP receive, USDC is MINTED (ERC-20 Transfer from 0x0). So the "funder" of a
     CCTP-bridged wallet is 0x0; attribution to CCTP requires that the tx interacts with the
     MessageTransmitter. Confirm this mechanism and give the exact MessageTransmitter address(es).
2. **Stargate (LayerZero) on Polygon:**
   - The Stargate Router / RouterETH address on Polygon.
   - The Stargate USDC pool address(es) on Polygon (the address that holds liquidity and
     transfers USDC OUT to the recipient on a receive — this is the "funder" in tokentx).
   - Stargate V2 addresses on Polygon if applicable (pools / OFT).
   - Confirm which address appears as the ERC-20 `from` when a user RECEIVES USDC via Stargate
     on Polygon.

OUTPUT: a markdown table {bridge, version, role, polygon_address, appears_as_funder?(yes/no),
source_url}. Distinguish addresses CONFIRMED by an official source vs INFERRED. If you cannot
confirm an address, say so explicitly — do NOT invent. Concise.
