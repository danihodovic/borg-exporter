import os
import subprocess
import sys

import click
import pretty_errors  # pylint: disable=unused-import
from prometheus_client import CollectorRegistry
from timy.settings import timy_config

from src.http_server import start_http_server

# https://github.com/pallets/click/issues/448#issuecomment-246029304
click.core._verify_python3_env = lambda: None  # pylint: disable=protected-access


def config_opt(func):
    return click.option(
        "-c",
        "--config",
        default=["/etc/borgmatic/config.yaml"],
        help="The path to the borgmatic config file",
        multiple=True,
        type=click.Path(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    )(func)


@click.group()
def cli():
    pass


@cli.command()
@config_opt
@click.option(
    "--port",
    type=int,
    default=9996,
    show_default=True,
    help="The port the exporter will listen on",
)
@click.option(
    "--time-borgmatic/--no-time-borgmatic",
    default=False,
    show_default=True,
    help="Show the time each Borgmatic call takes",
)
def run(config, port, time_borgmatic):
    registry = CollectorRegistry(auto_describe=True)
    timy_config.tracking = time_borgmatic
    start_http_server(config, registry, port)


@cli.command()
@click.option(
    "-u",
    "--user",
    default="root",
)
@config_opt
@click.option(
    "-o",
    "--out",
    type=click.File(mode="w"),
    default="/etc/systemd/system/borg-exporter.service",
)
def enable_systemd(user, config, out):
    systemd_template = f"""
[Unit]
Description=Borg Prometheus exporter
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=1
User={user}
ExecStart={sys.executable} run --config {config}

[Install]
WantedBy=multi-user.target
"""
    systemd_template = "\n".join(systemd_template.split("\n")[1:-1])
    out.write(systemd_template)
    out.close()
    click.secho(f"Wrote systemd service file to {out.name}", fg="green", bold=True)

    run_abort("systemctl daemon-reload")
    service = os.path.basename(out.name)

    run_abort(f"systemctl start {service}")
    click.secho(f"Started {service}", fg="green", bold=True)

    # run_abort(f"systemctl unmask {service}")
    run_abort(f"systemctl enable {service}")
    click.secho(f"Enabled {service}", fg="green", bold=True)


def run_abort(cmd):
    try:
        subprocess.run(cmd.split(), check=True)
    except subprocess.CalledProcessError as ex:
        raise click.Abort() from ex
