"""Small wrapper around the bq CLI (installed with the Google Cloud CLI).

Needs `gcloud auth login` and `gcloud config set project northwind-measurement`.
"""

import json
import subprocess

PROJECT = "northwind-measurement"


def run(sql):
    # The SQL goes in on stdin: as an argument, a leading "--" comment would be read as a flag.
    out = subprocess.run(
        ["bq", f"--project_id={PROJECT}", "query", "--use_legacy_sql=false",
         "--format=json", "--max_rows=1000"],
        input=sql, capture_output=True, text=True,
    )
    if out.returncode != 0:
        raise RuntimeError((out.stderr or out.stdout).strip())
    return json.loads(out.stdout or "[]")


def export_dataset():
    """The GA4 export dataset is named analytics_<property id>."""
    out = subprocess.run(["bq", "ls", "--format=json", f"{PROJECT}:"], capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError((out.stderr or out.stdout).strip())
    names = [d["datasetReference"]["datasetId"] for d in json.loads(out.stdout or "[]")]
    ga4 = [n for n in names if n.startswith("analytics_")]
    if not ga4:
        raise RuntimeError(f"No analytics_* dataset in {PROJECT} yet; the first daily export may not have run.")
    return f"{PROJECT}.{ga4[0]}"
