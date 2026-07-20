"""Hash-chained audit ledger for recommendation experiments."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any


def _canonical(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def append_record(path: str | Path, payload: dict[str, Any]) -> dict[str, Any]:
    """Append one hash-chained audit record."""
    audit_path = Path(path)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    previous_hash = "GENESIS"
    if audit_path.exists() and audit_path.read_text(encoding="utf-8").strip():
        previous_hash = json.loads(audit_path.read_text(encoding="utf-8").strip().splitlines()[-1])["record_hash"]
    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "previous_hash": previous_hash,
        "payload": payload,
    }
    record["record_hash"] = hashlib.sha256(_canonical(record).encode("utf-8")).hexdigest()
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    return record


def verify_log(path: str | Path) -> dict[str, Any]:
    """Verify the local audit log chain."""
    audit_path = Path(path)
    if not audit_path.exists():
        return {"valid": True, "records": 0, "last_hash": "GENESIS"}
    previous = "GENESIS"
    count = 0
    last_hash = "GENESIS"
    for line in audit_path.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        claimed = record.pop("record_hash")
        actual = hashlib.sha256(_canonical(record).encode("utf-8")).hexdigest()
        if claimed != actual or record["previous_hash"] != previous:
            return {"valid": False, "records": count, "last_hash": last_hash}
        previous = claimed
        last_hash = claimed
        count += 1
    return {"valid": True, "records": count, "last_hash": last_hash}
