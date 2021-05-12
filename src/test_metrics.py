import requests
import time
from threading import Thread
from prometheus_client import CollectorRegistry
from .http_server import start_http_server
import subprocess



def test_backups_total(tmpdir, find_free_port):
    config = prepare(tmpdir)
    subprocess.run(f"borgmatic -c {config} init -e repokey", shell=True, check=True)
    subprocess.run(f"borgmatic -c {config}", shell=True, check=True)


    registry = CollectorRegistry(auto_describe=True)
    port = find_free_port()
    start_http_server(config, registry, port)
    time.sleep(1)
    res = requests.get(f"http://localhost:{port}/metrics")
    res.raise_for_status()

    # Increase backup
    # Get new value == 2
    breakpoint()


def prepare(tmpdir):
    backups_dir = tmpdir.mkdir("backups")
    source_dir = tmpdir.mkdir("source_files")
    source_dir.join("hello.txt").write("content")

    config = f"""
location:
  one_file_system: true
  source_directories:
    - {source_dir}
  repositories:
    - {backups_dir}

storage:
  archive_name_format: 'pytest'
  encryption_passphrase: password

retention:
  prefix: 'prefix-'
  keep_daily: 1

consistency:
  checks:
    - repository
    - archives
hooks:
  before_backup:
    - echo "`date` - Starting backup"
  after_backup:
    - echo "`date` - Finished backup"

  postgresql_databases: []
"""
    config_file = tmpdir.join("borgmatic.yml")
    config_file.write(config)
    return config_file
