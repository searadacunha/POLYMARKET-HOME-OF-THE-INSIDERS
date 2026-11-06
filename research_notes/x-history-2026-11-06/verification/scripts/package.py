"""Copy the on-chain and API records the report cites into evidence/, and hash every raw file kept outside git.

Copied: Polygon receipts from both nodes, Relay records, Etherscan reads of the key addresses, Blockscout labels,
owner() reads, the positive-control log queries. Not copied (kept outside git, listed with sha256 in
SHA256SUMS_RAW.txt): X embed objects and images (third-party content), Polymarket profiles (profile fields), the
event tapes and activity pages (size). Usage: python3 -I package.py
"""
import hashlib, os, shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
RAW = Path(os.environ.get("XLEADS_RAW", Path.home() / "Projects/Polymarket-x-leads-raw-20261106/raw"))
EV = HERE / "evidence"

KEEP_RELAY = ["0xfddfd657996c214d4dd2fd0fff4589c0daeaf33d", "0xab05ffa436861ebb59e16f407703e009fe78e30f", "0x51633638f2f26deab4a9b2264ea4563406722b55",
              "0x2a1a80e795b6ed6325e3934b6a27d57111e72ffe", "0x6baf05d193692bb208d616709e27442c910a94c5", "0x858d551d073e9c647c17079ad9021de830201047",
              "0x5e0b017aef88af84fb3897fecce7413c6754981a", "0xb390ae2cc3fd8cb2670a62129faeb775faee106c", "0x95bd107886bd48d6737029603e3db242fb781652",
              "0x4ec2f11d2893eb1bc3bab7449910540c93adf7ec", "0xc07356e19774c236c52ddb613528581609afab63"]
KEEP_ES = ["0xd12623958b81d71e8be3fa936aed6d8c2528e992", "0xc5bb1be0407db7312911ec765d399d02461e411a", "0xab05ffa436861ebb59e16f407703e009fe78e30f",
           "0xfddfd657996c214d4dd2fd0fff4589c0daeaf33d", "0x2a1a80e795b6ed6325e3934b6a27d57111e72ffe", "0x6baf05d193692bb208d616709e27442c910a94c5",
           "0x4fe1567fee57ca473e287c0d3c0084bc42a45074", "0xb53640a8370bbac65dda4759b47b73a7b829d0f7", "0x72bf08860e18a46ee020e3a475f8491461903f48",
           "0x86b9bac992b18acd35408f1033f16d464be5c990", "0x13aad1943d6d5bf13cd9f212d3b5bee267988033", "0xb9841c57e16f7ebe2d15d7b205a6a34dd8a66167",
           "0x8db6758f477290b2530bfb6a5d5f11d3b39b822d", "0x3d74567dbc86ed8f5a7957eb54089e68063c0112", "0x7bc863e110ba59545151cfa38323c5300738d8e9",
           "0x5756bddb45817786ece4b3b6d1d71a291dc02006"]


def copy_tree(src, dst):
    if src.exists():
        shutil.copytree(src, dst, dirs_exist_ok=True)


def main():
    if EV.exists():
        shutil.rmtree(EV)
    copy_tree(RAW / "polygon2", EV / "polygon_receipts")
    for a in KEEP_RELAY:
        copy_tree(RAW / "relay" / a, EV / "relay" / a)
    for p in (RAW / "http").glob("relay_hash_*"):
        (EV / "relay_by_hash").mkdir(parents=True, exist_ok=True); shutil.copy2(p, EV / "relay_by_hash" / p.name)
    for a in KEEP_ES:
        copy_tree(RAW / "etherscan" / a, EV / "etherscan" / a)
    copy_tree(RAW / "blockscout", EV / "labels")
    copy_tree(RAW / "owner", EV / "owner_reads")
    for p in (RAW / "q5_logs").glob("POSCTRL*"):
        (EV / "q5_positive_control").mkdir(parents=True, exist_ok=True); shutil.copy2(p, EV / "q5_positive_control" / p.name)
    rows = []
    for p in sorted(EV.rglob("*")):
        if p.is_file():
            rows.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(HERE)}")
    (HERE / "SHA256SUMS.txt").write_text("\n".join(rows) + "\n")
    raw = []
    for p in sorted(RAW.rglob("*")):
        if p.is_file() and not p.name.endswith(".meta.json"):
            raw.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(RAW)}")
    (HERE / "SHA256SUMS_RAW.txt").write_text("\n".join(raw) + "\n")
    print(len(rows), "evidence files,", len(raw), "raw files hashed")


if __name__ == "__main__":
    main()
