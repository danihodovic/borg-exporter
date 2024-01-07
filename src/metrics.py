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
    Gauge(
        "borg_unique_size",
        "Uncompressed unique size of the Borg Repo",
        ["repo"],
        registry=registry,
    )
    return registry


def collect(borgmatic_configs, registry):
    borgmatic_configs = " ".join(borgmatic_configs)
    list_infos = run_borgmatic_cmd(f"borgmatic list -c {borgmatic_configs} --json")
    repo_infos = run_borgmatic_cmd(f"borgmatic info -c {borgmatic_configs} --json")

    for i in range(len(list_infos)):
        archives = list_infos[i]["archives"]
        labels = dict(repo=repo_infos[i]["repository"]["location"])

        backups_total = registry._names_to_collectors["borg_backups_total"]
        backups_total.labels(**labels).set(len(archives))

        unique_size = registry._names_to_collectors["borg_unique_size"]
        unique_size.labels(**labels).set(repo_infos[i]["cache"]["stats"]["unique_size"])

        if len(archives) == 0:
            continue

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
