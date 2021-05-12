# TODO: Rename file to metrics.py
import arrow
import subprocess
import json
from prometheus_client import CollectorRegistry, Gauge


def create_metrics(registry):
    Gauge(
        "borg_backups_total",
        "Total number of Borg backups",
        ["repo", "name"],
        registry=registry,
    )
    Gauge(
        "borg_last_backup_timestamp",
        "Timestamp of the last backup",
        ["repo", "name"],
        registry=registry,
    )
    return registry


def collect(borgmatic_config, registry):
    result = subprocess.run(
        f"borgmatic -c {borgmatic_config} list --json",
        shell=True,
        check=True,
        stdout=subprocess.PIPE,
    )
    output = result.stdout.decode("utf-8").strip()
    list_info = json.loads(output)
    archives = list_info[0]["archives"]
    latest_archive = archives[-1]
    labels = dict(
        name=latest_archive['name'],
        repo=list_info[0]['repository']['location'],
    )

    backups_total = registry._names_to_collectors["borg_backups_total"]
    backups_total.labels(**labels).set(len(archives))

    borg_last_backup_timestamp = registry._names_to_collectors["borg_last_backup_timestamp"]
    timestamp = arrow.get(latest_archive['time']).replace(tzinfo='local').timestamp()
    borg_last_backup_timestamp.labels(**labels).set(timestamp)
