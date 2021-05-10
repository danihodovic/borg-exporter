# pylint: disable=protected-access
import json
import subprocess

import arrow
import timy
from prometheus_client import Gauge


def create_metrics(registry):
    Gauge(
        "borg_backups_total",
        "Total number of Borg backups",
        ["repo"],
        registry=registry,
    )
    Gauge(
        "borg_last_backup_timestamp",
        "Timestamp of the last backup",
        ["repo"],
        registry=registry,
    )
    return registry


def collect(borgmatic_config, registry):
    list_info = run_borgmatic_cmd(f"borgmatic -c {borgmatic_config} list --json")[0]
    repo_info = run_borgmatic_cmd(f"borgmatic -c {borgmatic_config} info --json")[0]

    archives = list_info["archives"]
    labels = dict(repo=repo_info["repository"]["location"])

    backups_total = registry._names_to_collectors["borg_backups_total"]
    backups_total.labels(**labels).set(len(archives))

    if len(archives) == 0:
        return

    latest_archive = archives[-1]
    borg_last_backup_timestamp = registry._names_to_collectors[
        "borg_last_backup_timestamp"
    ]
    timestamp = arrow.get(latest_archive["time"]).replace(tzinfo="local").timestamp()
    borg_last_backup_timestamp.labels(**labels).set(timestamp)


def run_borgmatic_cmd(cmd):
    with timy.Timer(cmd):
        result = subprocess.run(
            cmd.split(" "),
            check=True,
            stdout=subprocess.PIPE,
        )
    output = result.stdout.decode("utf-8").strip()
    return json.loads(output)
