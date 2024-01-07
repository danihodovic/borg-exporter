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
def prepare_one(tmpdir, find_free_port):
    return prepare(tmpdir, find_free_port, 1)

@pytest.fixture
def prepare_two(tmpdir, find_free_port):
    return prepare(tmpdir, find_free_port, 2)

def prepare(tmpdir, find_free_port, num_config):
    source_dir = tmpdir.mkdir("source_files")
    source_dir.join("hello.txt").write("content")

    config_files = []
    str_configs = []

    for i in range(num_config):
        backups_dir = tmpdir.mkdir(f"backups-{i}")
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
        config_file = tmpdir.join(f"borgmatic-{i}.yml")
        config_file.write(yaml.dump(config))
        config_files.append(config_file)
        str_configs.append(str(config_file))
        subprocess.run(f"borgmatic -c {config_file} init -e repokey".split(" "), check=True)

    registry = CollectorRegistry(auto_describe=True)
    port = find_free_port()
    Thread(
        target=start_http_server,
        args=(" ".join(str_configs), registry, port),
        daemon=True,
    ).start()
    time.sleep(0.3)
    return registry, config_files, f"http://localhost:{port}/metrics"


def test_http_metrics(prepare_one):
    _, _, url = prepare_one
    res = perform_metric_collection(url)
    assert "borg_backups_total" in res.text
    assert "borg_last_backup_timestamp" in res.text


def test_backups_total(prepare_one):
    registry, config_files, url = prepare_one
    perform_backup(config_files[0])
    perform_metric_collection(url)
    assert (
        registry.get_sample_value(
            "borg_backups_total", labels=dict(repo=f"{config_files[0].dirname}/backups-0")
        )
        == 1.0
    )

    perform_backup(config_files[0])
    perform_metric_collection(url)
    assert (
        registry.get_sample_value(
            "borg_backups_total", labels=dict(repo=f"{config_files[0].dirname}/backups-0")
        )
        == 2.0
    )


def test_last_backup_timestamp(prepare_one):
    registry, config_files, url = prepare_one
    perform_backup(config_files[0])
    perform_metric_collection(url)
    now = arrow.utcnow().timestamp()
    last_backup_timestamp = registry.get_sample_value(
        "borg_last_backup_timestamp", labels=dict(repo=f"{config_files[0].dirname}/backups-0")
    )
    assert (now - last_backup_timestamp) < 10


def test_no_backups(prepare_one):
    registry, config_files, url = prepare_one
    perform_metric_collection(url)
    assert (
        registry.get_sample_value(
            "borg_backups_total", labels=dict(repo=f"{config_files[0].dirname}/backups-0")
        )
        == 0.0
    )


def test_unique_size(prepare_one):
    registry, config_files, url = prepare_one
    perform_backup(str(config_files[0]))
    perform_metric_collection(url)
    assert (
        registry.get_sample_value(
            "borg_unique_size", labels=dict(repo=f"{config_files[0].dirname}/backups-0")
        )
        == 7580.0
    )


def test_multiple_backups(prepare_two):
    registry, config_files, url = prepare_two
    str_configs = []
    for config in config_files:
        str_configs.append(str(config))
    perform_backup(" ".join(str_configs))
    perform_metric_collection(url)

    for i in range(len(config_files)):
        assert (
            registry.get_sample_value(
                "borg_backups_total", labels=dict(repo=f"{config_files[i].dirname}/backups-{i}")
            )
            == 1.0
        )


def perform_backup(borgmatic_config):
    subprocess.run(f"borgmatic -c {borgmatic_config}", shell=True, check=True)


def perform_metric_collection(exporter_url):
    return http.get(exporter_url)
