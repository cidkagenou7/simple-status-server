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

import json
import logging
from os import path
from threading import Lock

from simple_status_server.status import Status


class Database:
    def __init__(self, statuses: list[Status], database_path: str) -> None:
        self._statuses = statuses
        self._database_path = database_path

        self._lock = Lock()

    def load(self) -> None:
        """Loads database and updates self._statuses"""
        if not path.exists(self._database_path):
            logging.debug(f"Skipping loading database. File {self._database_path} doesn't exist")
            return

        logging.info(f"Loading database from {self._database_path}")
        with open(self._database_path, "r", encoding="utf-8") as database_io:
            database = json.load(database_io)
        if not isinstance(database, dict):
            logging.warning("Unable to load database. Invalid data type")
            database = {}

        # Load only configured statuses
        for status in self._statuses:
            if status.id not in database:
                logging.debug(f"Status {status.id} doesn't exist in database. Skipping")
                continue

            db_data = database[status.id]
            if "status_values" in db_data:
                status.status_values = db_data["status_values"]
            if "current_bar" in db_data:
                status.current_bar.from_dict(db_data["current_bar"])
            if "timestamps" in db_data and "data" in db_data:
                status.timestamps = db_data["timestamps"]
                status.data = db_data["data"]

            logging.debug(f"Loaded status {status.id} from database: {status.get_data_dict()}")

    def save(self) -> None:
        """Updates database with statuses in non-destructive way (will not update non-configured IDs)"""
        with self._lock:
            # Try to load existing database
            database = {}
            if path.exists(self._database_path):
                try:
                    logging.debug(f"Reading database from {self._database_path}")
                    with open(self._database_path, "r", encoding="utf-8") as database_io:
                        database = json.load(database_io)
                    if not isinstance(database, dict):
                        logging.warning("Unable to load database. Invalid data type")
                        database = {}
                except Exception as e:
                    logging.warning(f"Unable to load database from {self._database_path}: {e}")

            # Update
            for status in self._statuses:
                if status.id not in database:
                    database[status.id] = {}
                database[status.id]["status_values"] = status.status_values
                database[status.id]["current_bar"] = status.current_bar.to_dict()
                database[status.id]["timestamps"] = status.timestamps
                database[status.id]["data"] = status.data

            # Save
            logging.info(f"Saving database to {self._database_path}")
            with open(self._database_path, "w+", encoding="utf-8") as database_io:
                json.dump(database, database_io, ensure_ascii=False, indent=4)
