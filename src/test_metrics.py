import subprocess
import time
from threading import Thread

import arrow
import pytest
import requests
import yaml
from prometheus_client import CollectorRegistry

from .http_server import start_http_server

http = requests.Session()
assert_status_hook = lambda response, *args, **kwargs: response.raise_for_status()
http.hooks["response"] = [assert_status_hook]


@pytest.fixture
def prepare(tmpdir, find_free_port):
    backups_dir = tmpdir.mkdir("backups")
    source_dir = tmpdir.mkdir("source_files")
    source_dir.join("hello.txt").write("content")

    config = dict(
        location=dict(
            source_directories=[str(source_dir)],
            repositories=[str(backups_dir)],
        ),
        storage=dict(
            archive_name_format="pytest-{now}",
            encryption_passphrase="password",
        ),
        retention=dict(
            prefix="prefix-",
            keep_daily=10,
        ),
    )
    config_file = tmpdir.join("borgmatic.yml")
    config_file.write(yaml.dump(config))

    subprocess.run(f"borgmatic -c {config_file} init -e repokey".split(" "), check=True)
    registry = CollectorRegistry(auto_describe=True)
    port = find_free_port()
    Thread(
        target=start_http_server,
        args=(config_file, registry, port),
        daemon=True,
    ).start()
    time.sleep(0.3)
    return registry, config_file, f"http://localhost:{port}/metrics"


def test_http_metrics(prepare):
    _, _, url = prepare
    res = perform_metric_collection(url)
    assert "borg_backups_total" in res.text
    assert "borg_last_backup_timestamp" in res.text


def test_backups_total(prepare):
    registry, config_file, url = prepare
    perform_backup(config_file)
    perform_metric_collection(url)
    assert (
        registry.get_sample_value(
            "borg_backups_total", labels=dict(repo=f"{config_file.dirname}/backups")
        )
        == 1.0
    )

    perform_backup(config_file)
    perform_metric_collection(url)
    assert (
        registry.get_sample_value(
            "borg_backups_total", labels=dict(repo=f"{config_file.dirname}/backups")
        )
        == 2.0
    )


def test_last_backup_timestamp(prepare):
    registry, config_file, url = prepare
    perform_backup(config_file)
    perform_metric_collection(url)
    now = arrow.utcnow().timestamp()
    last_backup_timestamp = registry.get_sample_value(
        "borg_last_backup_timestamp", labels=dict(repo=f"{config_file.dirname}/backups")
    )
    assert (now - last_backup_timestamp) < 10


def test_no_backups(prepare):
    registry, config_file, url = prepare
    perform_metric_collection(url)
    assert (
        registry.get_sample_value(
            "borg_backups_total", labels=dict(repo=f"{config_file.dirname}/backups")
        )
        == 0.0
    )


def perform_backup(borgmatic_config):
    subprocess.run(f"borgmatic -c {borgmatic_config}", shell=True, check=True)


def perform_metric_collection(exporter_url):
    return http.get(exporter_url)
