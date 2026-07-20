import json
import subprocess
import sys
from pathlib import Path


def test_synthetic_pipeline_smoke(tmp_path):
    output_dir = tmp_path / "outputs"
    cmd = [
        sys.executable,
        "scripts/run_synthetic_recommender_lab.py",
        "--users",
        "30",
        "--items",
        "60",
        "--interactions-per-user",
        "7",
        "--top-k",
        "6",
        "--seed",
        "11",
        "--output-dir",
        str(output_dir),
    ]
    subprocess.run(cmd, check=True)
    summary_path = output_dir / "results" / "synthetic_recommender_summary.json"
    assert summary_path.exists()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["user_count"] == 30
    assert summary["item_count"] == 60
    assert summary["recommendation_count"] > 0
    assert summary["audit_log"]["valid"] is True
