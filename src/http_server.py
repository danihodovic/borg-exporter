from threading import Thread
from .exporter import collect, create_metrics

import kombu.exceptions
from flask import Blueprint, Flask, current_app, request
from loguru import logger
from prometheus_client.exposition import choose_encoder
from waitress import serve

blueprint = Blueprint("celery_exporter", __name__)


@blueprint.route("/")
def index():
    return """
<!doctype html>
<html lang="en">
  <head>
    <!-- Required meta tags -->
    <meta charset="utf-8">
    <title>borg-exporter</title>
  </head>
  <body>
    <h1>Borg Exporter</h1>
    <p><a href="/metrics">Metrics</a></p>
  </body>
</html>
"""


@blueprint.route("/metrics")
def metrics():
    borgmatic_config = current_app.config["borgmatic_config"]
    registry = current_app.config["registry"]
    collect(borgmatic_config, registry)
    encoder, content_type = choose_encoder(request.headers.get("accept"))
    output = encoder(current_app.config["registry"])
    return output, 200, {"Content-Type": content_type}


@blueprint.route("/health")
def health():
    conn = current_app.config["celery_connection"]
    uri = conn.as_uri()

    try:
        conn.ensure_connection(max_retries=3)
    except kombu.exceptions.OperationalError:
        logger.error("Failed to connect to broker='{}'", uri)
        return (f"Failed to connect to broker: '{uri}'", 500)
    except Exception:  # pylint: disable=broad-except
        logger.exception("Unrecognized error")
        return ("Unknown exception", 500)
    return f"Connected to the broker {conn.as_uri()}"


def start_http_server(borgmatic_config, registry, port):
    app = Flask(__name__)
    app.config["registry"] = create_metrics(registry)
    app.config["borgmatic_config"] = borgmatic_config
    app.register_blueprint(blueprint)
    Thread(
        target=serve,
        args=(app,),
        kwargs=dict(host="0.0.0.0", port=port, _quiet=True),
        daemon=True,
    ).start()
    logger.info("Started celery-exporter at port='{}'", port)
