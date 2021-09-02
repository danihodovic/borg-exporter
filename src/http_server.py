from py._path.local import LocalPath
from flask import Blueprint, Flask, current_app, request
from loguru import logger
from prometheus_client.exposition import choose_encoder
from waitress import serve

from .metrics import collect, create_metrics

blueprint = Blueprint("borg_exporter", __name__)


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


def start_http_server(borgmatic_configs, registry, port):
    if isinstance(borgmatic_configs, str):
        borgmatic_configs = (borgmatic_configs,)
    app = Flask(__name__)
    app.config["registry"] = create_metrics(registry)
    app.config["borgmatic_config"] = borgmatic_configs
    app.register_blueprint(blueprint)
    logger.info("Started borg-exporter at port='{}'", port)
    serve(app, host="0.0.0.0", port=port, _quiet=True)
