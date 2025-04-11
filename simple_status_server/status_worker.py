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
import subprocess
from os import path
from threading import Timer
from typing import Callable

import requests

from .status import Status, Type


class StatusWorker:
    def __init__(self, status: Status, update_callback: Callable[[], None]) -> None:
        self._status = status
        self._update_callback = update_callback

        self._exit_flag = False
        self._timer = Timer(status.interval if len(status.status_values) > 0 else 0, self._timer_callback)

        logging.info(f"Status {status.id} ({status.label}) registered. Interval: {status.interval:.2f}s")

    def start(self) -> None:
        """Starts updates"""
        if self._timer.is_alive():
            return
        logging.debug(f"Starting {self._status.id} updates")
        self._timer.start()

    def stop(self) -> None:
        """Stops updates"""
        logging.debug(f"Stopping {self._status.id} updates")
        self._exit_flag = True
        if self._timer.is_alive():
            self._timer.cancel()

    def _timer_callback(self) -> None:
        """Performs check"""
        if self._exit_flag:
            return

        logging.info(f"Checking {self._status.id} ({self._status.target})...")

        result = False
        try:
            # Constant
            if self._status.type == Type.constant:
                result = bool(self._status.target)

            # Service / command
            elif self._status.type == Type.service or self._status.type == Type.command:
                if self._status.type == Type.service:
                    cmd = ["/usr/bin/systemctl", "is-active", "--quiet", str(self._status.target)]
                else:
                    cmd = str(self._status.target)
                try:
                    return_code = subprocess.check_call(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        shell=self._status.type == Type.command,
                        timeout=self._status.target_timeout,
                    )
                    result = return_code == 0
                except subprocess.CalledProcessError:
                    result = False
            # Path
            elif self._status.type == Type.path:
                result = path.exists(str(self._status.target))

            # URL
            elif self._status.type == Type.url:
                try:
                    resp = requests.get(
                        str(self._status.target),
                        timeout=self._status.target_timeout,
                        allow_redirects=True,
                    )
                    result = resp.status_code == 200 and len(resp.text) > 0
                except:
                    pass

        # Just in case
        except Exception as e:
            logging.error(f"{self._status.id} error: {e}", exc_info=e)

        # Push new status and save into database
        logging.info(f"{self._status.id}: {result}")
        self._status.push_new_status(result)
        self._update_callback()

        # Restart timer
        if not self._exit_flag:
            self._timer = Timer(self._status.interval, self._timer_callback)
            self._timer.start()
