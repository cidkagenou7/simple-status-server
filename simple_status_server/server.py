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

import logging
from os import path
from typing import Any

from flask import Flask, Response, jsonify, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


class Server:
    def __init__(
        self,
        limits: list[str],
        api_key: str | None,
        page_title: str,
        page_description: str | None,
        api_data: dict[str, dict[str, Any]],
    ) -> None:
        self._app = Flask(
            __name__,
            static_folder=path.abspath(path.join(path.dirname(__file__), "static")),
            template_folder=path.abspath(path.join(path.dirname(__file__), "templates")),
        )
        self._app.config["JSON_SORT_KEYS"] = False
        self._app.json.sort_keys = False  # pyright: ignore
        self._app.config["JSON_AS_ASCII"] = False
        self._app.json.ensure_ascii = False  # pyright: ignore
        self._limiter = Limiter(
            get_remote_address,
            app=self._app,
            default_limits=limits,  # pyright: ignore
            storage_uri="memory://",
            strategy="fixed-window",
        )

        @self._app.route("/", methods=["GET"])
        def _index() -> Response | str:
            """Main page

            Returns:
                Response | str: status page or 403
            """
            # Check API key
            request_api_key = request.args.get("apiKey")
            if api_key and (not request_api_key or request_api_key != api_key):
                logging.warning(f"User {request.remote_addr} provided wrong api key: {request_api_key}")
                return Response(response="No or wrong API key provided", status=403)

            return render_template(
                "index.html",
                page_title=page_title,
                page_description=page_description if page_description else "",
            )

        @self._app.route("/", methods=["POST"])
        def _data() -> Response:
            """Data request (POST)
            NOTE: if API_KEY is set, request must have a JSON body with "apiKey" key and API_KEY value

            Returns:
                Response: JSON data or 400 or 403
                data format: {"id": {"status": 0/1/2, "status_text": "", "label": "", "timestamps": [], "data": []},}
            """
            # Check request and API key
            if api_key:
                if not request.json:
                    logging.warning(f"User {request.remote_addr} provided no POST data")
                    return Response(response="No API key provided", status=400)
                request_api_key = request.json.get("apiKey")
                if not request_api_key or request_api_key != api_key:
                    logging.warning(f"User {request.remote_addr} provided wrong api key: {request_api_key}")
                    return Response(response="Wrong API key provided", status=403)

            return jsonify(api_data)

    def start(self, host: str, port: int) -> None:
        """Starts Flask server (blocking)

        Args:
            host (str): server's host (IP)
            port (int): server's port
        """
        logging.info(f"Starting server on {host}:{port}")
        self._app.run(host, port, debug=False, load_dotenv=False)
