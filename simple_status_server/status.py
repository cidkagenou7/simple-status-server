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
from enum import Enum
from time import time
from typing import Any

CONFIG_DEFAULT = {
    "target_timeout": "10s",
    "interval": "5m",
    "checks_per_bar": 12,
    "bars_max": 48,
    "value_working": "Working",
    "value_problems": "Has problems",
    "value_not_working": "Not working",
}


def parse_time_cfg(time_cfg: str | int) -> int:
    """Parses time config (ex. interval) into seconds
    >>> parse_time_cfg("1")
    1
    >>> parse_time_cfg("1.2")
    1
    >>> parse_time_cfg("1s")
    1
    >>> parse_time_cfg("5m")
    300
    >>> parse_time_cfg("2h")
    7200
    >>> parse_time_cfg("5d")
    432000
    >>> parse_time_cfg("1d2h3m1.789s")
    93781
    >>> parse_time_cfg("1.5m")
    90
    >>> parse_time_cfg(300)
    300

    Args:
        time_cfg (str | int): ex. 5m

    Returns:
        int: parsed time interval in seconds
    """
    # Already in seconds
    if isinstance(time_cfg, int):
        return time_cfg

    units = {"s": 1, "m": 60, "h": 3600, "d": 86400}

    seconds = 0
    num_str_temp = ""
    for char in time_cfg.strip().lower().replace(" ", "").replace(",", "."):
        if char.isdigit() or char == ".":
            num_str_temp += char
        else:
            seconds += float(num_str_temp) * units.get(char, 1)
            num_str_temp = ""
    if num_str_temp:
        seconds += float(num_str_temp)

    return int(seconds)


class Type(Enum):
    constant = 0
    service = 1
    command = 2
    path = 3
    url = 4


class StatusValue(Enum):
    not_working = 0
    problems = 1
    working = 2


class CurrentBar:
    def __init__(self) -> None:
        self.time_start: int | None = None
        self.time_end: int | None = None
        self.data: list[bool] = []

    def from_dict(self, bar_: dict[str, Any]) -> None:
        """Parses dictionary into bar data

        Args:
            bar_ (dict[str, Any]): dictionary from database
        """
        self.time_start = bar_.get("time_start")
        if self.time_start == 0:
            self.time_start = None
        self.time_end = bar_.get("time_end")
        if self.time_end == 0:
            self.time_end = None
        self.data = bar_.get("data", [])

    def to_dict(self) -> dict[str, Any]:
        """
        Returns:
            dict[str, Any]: current bar_ as dictionary
        """
        bar_ = {}
        if self.time_start is not None:
            bar_["time_start"] = self.time_start
        if self.time_end is not None:
            bar_["time_end"] = self.time_end
        if self.data:
            bar_["data"] = self.data
        return bar_

    def avg_value(self) -> int:
        """
        Returns:
            float: average value (0-100, in %) of stored data
        """
        if not self.data:
            return 0
        return int(self.data.count(True) / len(self.data) * 100.0)

    def get_timestamps(self) -> tuple[int, int]:
        """
        Returns:
            tuple[int, int]: timestamps range of current data stored
        """
        timestamp_current = int(time())
        time_start = self.time_start if self.time_start else timestamp_current
        time_end = self.time_end if self.time_end else timestamp_current
        return time_start, time_end


class Status:
    def __init__(self, status_id: str, config: dict[str, Any]) -> None:
        if not status_id:
            raise Exception("Status ID cannot be empty")
        if "type" not in config:
            raise Exception(f"No type of status {status_id} specified")
        if "target" not in config:
            raise Exception(f"No target for status {status_id} specified")
        if not isinstance(config["target"], str) and not isinstance(config["target"], bool):
            raise Exception(f"Wrong target datatype for status {status_id} specified. Excepted str or bool")

        self.id = status_id
        self.type = Type[config["type"].lower()]
        self.target: str | bool = config["target"]

        self.label = config.get("label", status_id)
        self.target_timeout = parse_time_cfg(config.get("target_timeout", CONFIG_DEFAULT["target_timeout"]))
        self.interval = parse_time_cfg(config.get("interval", CONFIG_DEFAULT["interval"]))
        self.checks_per_bar = int(config.get("checks_per_bar", CONFIG_DEFAULT["checks_per_bar"]))
        self.bars_max = int(config.get("bars_max", CONFIG_DEFAULT["bars_max"]))
        self.value_working: str = config.get("value_working", CONFIG_DEFAULT["value_working"])
        self.value_problems: str = config.get("value_problems", CONFIG_DEFAULT["value_problems"])
        self.value_not_working: str = config.get("value_not_working", CONFIG_DEFAULT["value_not_working"])
        self.no_intermediate_value: bool = config.get("no_intermediate_value", False)

        self.status_values: list[bool] = []
        self.current_bar: CurrentBar = CurrentBar()
        self.timestamps: list[tuple[int, int]] = []
        self.data: list[int] = []

    @property
    def current_status(self) -> StatusValue:
        """
        Returns:
            StatusValue: Calculated status from status_values
        """
        # No values yet
        if not self.status_values:
            return StatusValue.not_working if self.no_intermediate_value else StatusValue.problems

        working_count = self.status_values.count(True)

        # All status values are true
        if working_count == len(self.status_values):
            return StatusValue.working

        # All status values are false
        elif working_count == 0:
            return StatusValue.not_working

        # Some of them are false some are true
        return StatusValue.not_working if self.no_intermediate_value else StatusValue.problems

    @property
    def current_status_text(self) -> str:
        """
        Returns:
            str: current status value (self.value_working / self.value_problems / self.value_not_working)
        """
        current_status = self.current_status
        if current_status == StatusValue.working:
            return self.value_working
        elif current_status == StatusValue.not_working or self.no_intermediate_value:
            return self.value_not_working
        return self.value_problems

    def get_data_dict(self) -> dict[str, Any]:
        """
        Returns:
            dict[str, Any]: current status instance as dictionary in server's format
        """
        timestamps = (
            self.timestamps + [self.current_bar.get_timestamps()] if self.current_bar.data else self.timestamps
        )
        data = self.data + [self.current_bar.avg_value()] if self.current_bar.data else self.data
        return {
            "status": self.current_status.value,
            "status_text": self.current_status_text,
            "label": self.label,
            "timestamps": timestamps,
            "data": data,
        }

    def push_new_status(self, status_value: bool) -> None:
        """Appends new status to the status_values and current_bar, removes old ones and updates timestamps and data

        Args:
            status_value (bool): current status
        """
        # New bar
        if len(self.current_bar.data) >= self.checks_per_bar:
            logging.debug(f"New bar completed for {self.id} status")
            self.timestamps.append(self.current_bar.get_timestamps())
            self.data.append(self.current_bar.avg_value())
            self.current_bar.data.clear()
            self.current_bar.time_start = None

        # Append data
        self.status_values.append(status_value)
        self.current_bar.data.append(status_value)

        # Update current bar timestamps
        timestamp_current = int(time())
        if not self.current_bar.time_start:
            self.current_bar.time_start = timestamp_current
        self.current_bar.time_end = timestamp_current

        # Trim data to size
        while len(self.status_values) > self.checks_per_bar:
            self.status_values.pop(0)
        while len(self.data) > self.bars_max:
            self.data.pop(0)
        while len(self.timestamps) > self.bars_max:
            self.timestamps.pop(0)
