"""Independent decoder of Privacy Cash `transact` (SOL pool) from a raw Solana transaction, stdlib only.

Layout read in Privacy-Cash/privacy-cash f79b82f, anchor/programs/zkcash/src/lib.rs:
  transact(proof: Proof, ext_data_minified: ExtDataMinified, encrypted_output1: Vec<u8>, encrypted_output2: Vec<u8>)
  Proof = proof_a[64] proof_b[128] proof_c[64] root[32] public_amount[32] ext_data_hash[32] input_nullifiers[2][32] output_commitments[2][32]
  ExtDataMinified = ext_amount i64, fee u64       -> ext_amount at byte 488 of the instruction data
  event CommitmentData { index u64, commitment [32], encrypted_output Vec<u8> }, emitted twice per transact (lib.rs:346-364)
The decoder refuses any instruction whose bytes are not consumed exactly, so a layout change fails closed.
What it cannot do: link a withdrawal to a deposit. The proof hides which note is spent; `root` only bounds the candidate set
to notes inserted before that root, and computing which insertion produced a root needs the whole Poseidon tree.
"""
import base64, hashlib, json, struct, sys
from pathlib import Path

PROGRAM = "9fhQBbumKEFuXtMBDw8AaQyAjCorLGJQiS3skWZdQyQD"
IX_TRANSACT = hashlib.sha256(b"global:transact").digest()[:8]
EV_COMMITMENT = hashlib.sha256(b"event:CommitmentData").digest()[:8]
_B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58decode(s: str) -> bytes:
    n = 0
    for c in s:
        n = n * 58 + _B58.index(c)
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    return b"\0" * (len(s) - len(s.lstrip("1"))) + raw


def decode_transact(data: bytes) -> dict:
    if data[:8] != IX_TRANSACT:
        raise ValueError("not a transact instruction")
    o = 8
    proof = {}
    for name, size in (("proof_a", 64), ("proof_b", 128), ("proof_c", 64), ("root", 32), ("public_amount", 32), ("ext_data_hash", 32)):
        proof[name] = data[o:o + size].hex(); o += size
    proof["input_nullifiers"] = [data[o:o + 32].hex(), data[o + 32:o + 64].hex()]; o += 64
    proof["output_commitments"] = [data[o:o + 32].hex(), data[o + 32:o + 64].hex()]; o += 64
    ext_amount, fee = struct.unpack_from("<qQ", data, o); o += 16
    enc = []
    for _ in range(2):
        (n,) = struct.unpack_from("<I", data, o); o += 4
        enc.append(n); o += n
    if o != len(data):
        raise ValueError(f"layout mismatch: consumed {o} of {len(data)} bytes")
    return {"root": proof["root"], "input_nullifiers": proof["input_nullifiers"], "output_commitments": proof["output_commitments"],
            "public_amount": proof["public_amount"], "ext_amount": ext_amount, "fee": fee, "encrypted_output_lengths": enc}


def commitment_events(log_messages):
    out = []
    for line in log_messages or []:
        if line.startswith("Program data: "):
            b = base64.b64decode(line[len("Program data: "):])
            if b[:8] == EV_COMMITMENT:
                (idx,) = struct.unpack_from("<Q", b, 8)
                (n,) = struct.unpack_from("<I", b, 48)
                if 52 + n != len(b):
                    raise ValueError("CommitmentData layout mismatch")
                out.append({"index": idx, "commitment": b[16:48].hex()})
    return out


def decode_tx(tx: dict) -> list:
    """Every Privacy Cash SOL transact in a jsonParsed transaction, with its leaf indices and the accounts it names."""
    res = []
    for ins in tx["transaction"]["message"]["instructions"]:
        if ins.get("programId") != PROGRAM:
            continue
        d = decode_transact(b58decode(ins["data"]))
        ev = commitment_events(tx["meta"].get("logMessages"))
        if [e["commitment"] for e in ev] != d["output_commitments"]:
            raise ValueError("events do not echo the proof's output commitments")
        res.append({**d, "signature": tx["transaction"]["signatures"][0], "slot": tx["slot"], "block_time": tx["blockTime"],
                    "leaf_indices": [e["index"] for e in ev], "accounts": ins["accounts"], "err": tx["meta"]["err"]})
    return res


if __name__ == "__main__":
    # python3 -I privacy_cash.py <gtfa_dir>...   prints every Privacy Cash transact found in archived pages
    seen = set()
    for d in sys.argv[1:]:
        for f in sorted(Path(d).glob("gtfa_*_p*.json")):
            if f.name.endswith(".meta.json"):
                continue
            for tx in json.loads(f.read_text())["result"]["data"]:
                s = tx["transaction"]["signatures"][0]
                if s in seen:
                    continue
                seen.add(s)
                for r in decode_tx(tx):
                    print(json.dumps({k: r[k] for k in ("signature", "block_time", "ext_amount", "fee", "leaf_indices", "root")}))
