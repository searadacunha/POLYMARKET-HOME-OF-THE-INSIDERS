"""Build the importable copy of the V2 template: same nodes and links, plus credential references and a stable id.

  python3 prepare_workflow.py TEMPLATE.json OUT_DIR SECRETS_ENV

Writes OUT_DIR/workflow.json (no secret) and OUT_DIR/credentials.json (mode 600, the two header tokens; the
installer deletes it right after `n8n import:credentials`). The template in the repository is never modified.
"""
import json
import os
import sys
from pathlib import Path

WORKFLOW_ID = "TriAgentV2Wake01"
WAKE = {"id": "triagentWakeHdr1", "name": "TriAgent wake header (webhook)"}
BROKER = {"id": "triagentBrokerH1", "name": "TriAgent broker header (HTTP)"}


def read_env(path: Path) -> dict:
    out = {}
    for line in path.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def prepare(template: dict, secrets: dict, wake_header="X-TriAgent-Wake", broker_header="X-TriAgent-Key"):
    for name in ("N8N_WAKE_TOKEN", "BROKER_TOKEN"):
        if len(secrets.get(name, "")) < 24:
            raise SystemExit(f"{name} missing or too short in secrets.env (run install.sh)")
    wf = json.loads(json.dumps(template))
    wf["id"], wf["active"] = WORKFLOW_ID, False  # activation is a separate, explicit step
    for node in wf["nodes"]:
        if node["type"] == "n8n-nodes-base.webhook":
            node["credentials"] = {"httpHeaderAuth": WAKE}
            node["webhookId"] = "5f0c5e2e-7d1a-4c1e-9a55-0b1f2a3c4d5e"  # stable across re-imports
        elif node["type"] == "n8n-nodes-base.httpRequest":
            node["credentials"] = {"httpHeaderAuth": BROKER}
    creds = [{**WAKE, "type": "httpHeaderAuth", "data": {"name": wake_header, "value": secrets["N8N_WAKE_TOKEN"]}},
             {**BROKER, "type": "httpHeaderAuth", "data": {"name": broker_header, "value": secrets["BROKER_TOKEN"]}}]
    return wf, creds


def main():
    template, out, secrets = Path(sys.argv[1]), Path(sys.argv[2]), read_env(Path(sys.argv[3]))
    wf, creds = prepare(json.loads(template.read_text()), secrets)
    out.mkdir(parents=True, exist_ok=True)
    (out / "workflow.json").write_text(json.dumps([wf], indent=1))
    fd = os.open(out / "credentials.json", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(creds, f)
    print(json.dumps({"workflow_id": WORKFLOW_ID, "nodes": len(wf["nodes"]),
                      "with_credentials": sum("credentials" in n for n in wf["nodes"])}))


if __name__ == "__main__":
    main()
