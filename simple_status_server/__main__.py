"""
Copyright (C) 2025 Fern Lane, simple-status-server

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
See the License for the specific language governing permissions and
limitations under the License.

IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
"""

import argparse
import logging
import sys
from os import environ, path
from typing import Any

from yaml import load

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from simple_status_server._version import __version__
from simple_status_server.database import Database
from simple_status_server.server import Server
from simple_status_server.status import Status
from simple_status_server.status_worker import StatusWorker

CONFIG_PATH_DEFAULT = environ.get("CONFIG_PATH", "config.yaml")

# Environment variables / default config
CONFIG_DEFAULT = {
    "logging": {
        "level": "info",
        "format": "[%(asctime)s] [%(levelname).1s] %(message)s",
        "date_fmt": "%Y-%m-%d %H:%M:%S",
    },
    "server": {
        "host": environ.get("HOST", "127.0.0.1"),
        "port": int(environ.get("PORT", 8080)),
        "api_key": environ.get("API_KEY"),
        "request_limits": ["5 per minute", "1 per second"],
    },
    "page": {
        "title": "Status",
        "description": None,
        "last_check_text": "Last check:",
        "color_palette": "RdPu",
        "extra_css": None,
    },
    "database_path": environ.get("DATABASE_PATH", "database.json"),
    "statuses": {},
}


def _get_config(config: dict[str, Any], category: str, key: str | None = None):
    """Retrieves value from config

    Args:
        config (dict[str, Any]): parsed config dictionary provided by user
        category (str): config main key
        key (str | None, optional): config sub key. Defaults to None.

    Returns:
        Any: provided / default value
    """
    if key:
        return config.get(category, CONFIG_DEFAULT[category]).get(key, CONFIG_DEFAULT[category][key])
    return config.get(category, CONFIG_DEFAULT[category])


def _parse_args() -> argparse.Namespace:
    """Parses cli arguments

    Returns:
        argparse.Namespace: parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Simple service / command / file / url status web server with logger, graphs and API"
    )

    parser.add_argument(
        "-c",
        "--config",
        default=CONFIG_PATH_DEFAULT,
        type=str,
        required=False,
        help=f"path to config file (CONFIG_PATH env variable, default: {CONFIG_PATH_DEFAULT})",
        metavar="path/to/config.yaml",
    )
    parser.add_argument(
        "--host",
        default=None,
        type=str,
        required=False,
        help=f'server\'s host (HOST env variable, default: {CONFIG_DEFAULT["server"]["host"]})',
        metavar="HOST",
    )
    parser.add_argument(
        "--port",
        default=None,
        type=int,
        required=False,
        help=f'server\'s port (PORT env variable, default: {CONFIG_DEFAULT["server"]["port"]})',
        metavar="PORT",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        type=str,
        required=False,
        help="API key to restrict access to web page and API "
        f'(API_KEY env variable, default: {CONFIG_DEFAULT["server"]["api_key"]})',
        metavar="API_KEY",
    )
    parser.add_argument(
        "--database",
        default=None,
        type=str,
        required=False,
        help="path to database file that stores collected statuses "
        f'(DATABASE_PATH env variable, default: {CONFIG_DEFAULT["database_path"]})',
        metavar="path/to/database.json",
    )
    parser.add_argument("-v", "--version", action="version", version=__version__)

    return parser.parse_args()


def main() -> None:
    """Main entrypoint"""

    # Parse CLI args
    args = _parse_args()

    # Parse config file
    if path.exists(args.config):
        with open(args.config, "r", encoding="utf-8") as config_io:
            config = load(config_io, Loader=Loader)
        if config is None:
            print("WARNING: Config file is empty", file=sys.stderr)
            config = {}
        if not isinstance(config, dict):
            raise Exception(f"Unable to load config! Wrong data type: {type(config)}")
    else:
        print(
            f"WARNING: File {args.config} doesn't exist! Provide path to it via -c arg or CONFIG_PATH env variable",
            file=sys.stderr,
        )
        config = {}

    # Initialize logging
    logging_level_str = _get_config(config, "logging", "level").lower()
    if logging_level_str[0] == "d":
        logging_level = logging.DEBUG
    elif logging_level_str[0] == "w":
        logging_level = logging.WARNING
    elif logging_level_str[0] == "e":
        logging_level = logging.ERROR
    elif logging_level_str[0] == "i":
        logging_level = logging.INFO
    else:
        raise Exception(f"Unknown logging level: {logging_level_str}")
    logging.basicConfig(
        format=_get_config(config, "logging", "format"),
        datefmt=_get_config(config, "logging", "date_fmt"),
        level=logging_level,
    )
    logging.debug(f"Logging level: {logging_level_str}")
    logging.debug(f"Parsed config: {config}")

    # Print program version
    logging.info(f"simple-status-server version {__version__}")

    # Parse CLI args and config
    host: str = args.host if args.host else _get_config(config, "server", "host")
    port: int = int(args.port if args.port is not None else _get_config(config, "server", "port"))
    api_key: str | None = args.api_key if args.api_key else _get_config(config, "server", "api_key")
    request_limits: list[str] = _get_config(config, "server", "request_limits")
    page_title: str = _get_config(config, "page", "title")
    page_description: str | None = _get_config(config, "page", "description")
    last_check_text: str = _get_config(config, "page", "last_check_text")
    color_palette: str = _get_config(config, "page", "color_palette")
    extra_css: str | None = _get_config(config, "page", "extra_css")
    database_path: str = args.database if args.database else _get_config(config, "database_path")

    # Parse statuses
    statuses_dict = config.get("statuses", {})
    statuses: list[Status] = []
    for status_id, status_config in statuses_dict.items():
        statuses.append(Status(status_id, status_config))

    api_data: dict[str, dict[str, Any]] = {}

    def _update_data(status: Status) -> None:
        """Updates data for server and saves database (called from workers)

        Args:
            status (Status): updated status
        """
        api_data[status.id] = status.get_data_dict()
        logging.debug(f"Updated API data for {status.id}: {api_data[status.id]}")
        database.save()

    # Initialize server, database instances and load database
    if api_key:
        logging.warning("API key specified. Make sure server is accessible only via localhost or secured via SSL")
    server = Server(
        request_limits,
        api_key,
        page_title,
        page_description,
        last_check_text,
        color_palette,
        extra_css,
        api_data,
    )
    database = Database(statuses, database_path)
    database.load()

    # Pre-load API data
    for status in statuses:
        api_data[status.id] = status.get_data_dict()

    # Initialize workers
    workers: list[StatusWorker] = []
    for status in statuses:
        workers.append(StatusWorker(status, _update_data))

    # Start workers
    if workers:
        logging.info("Starting workers")
        for worker in workers:
            worker.start()
    else:
        logging.warning("No statuses specified")

    # Start server (blocking)
    server.start(host, port)

    # Stop workers after server stop
    if workers:
        logging.info("Stopping workers")
        for worker in workers:
            worker.stop()


if __name__ == "__main__":
    main()
