/**
 * Copyright (C) 2025 Fern Lane, simple-status-server

 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at

 *     http://www.apache.org/licenses/LICENSE-2.0

 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * See the License for the specific language governing permissions and
 * limitations under the License.

 * IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR
 * OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
 * ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
 * OTHER DEALINGS IN THE SOFTWARE.
 */

/**
 * Converts UTC time into client's time string
 * @param {Number} timestamp time from server
 * @returns {Number} formatted time string
 */
function _timestampToString(timestamp) {
    // Convert to milliseconds
    const date = new Date(timestamp * 1000);

    // Get individual components
    const day = String(date.getDate()).padStart(2, "0");
    const month = String(date.getMonth() + 1).padStart(2, "0"); // Month is 0-based
    const year = String(date.getFullYear());

    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");
    const seconds = String(date.getSeconds()).padStart(2, "0");

    // Format as DD.MM.YYYY HH:MM:SS
    return `${day}.${month}.${year} ${hours}:${minutes}:${seconds}`;
}

/**
 * Creates new status and chart
 * @param {Object} charts Chart's data
 * @param {String} id New status ID
 */
function _createStatus(charts, id) {
    const statusesContainer = document.getElementById("statuses");

    // Create container
    const container = document.createElement("div");
    container.className = "status";
    container.id = `${id}-container`;

    // Append title
    const title = document.createElement("h2");
    title.className = "status-title";
    title.id = `${id}-title`;
    container.appendChild(title);

    // Append status
    const status = document.createElement("a");
    status.className = "status-current";
    status.id = `${id}-status`;
    container.appendChild(status);

    // Append last update time
    const updateTime = document.createElement("p");
    updateTime.className = "status-update-time";
    updateTime.id = `${id}-update-time`;
    container.appendChild(updateTime);

    // Append canvas
    // const canvasContainer = document.createElement("div");
    // canvasContainer.className = "canvas-container";
    const canvas = document.createElement("canvas");
    canvas.id = `${id}-canvas`;
    // canvasContainer.appendChild(canvas);
    // container.appendChild(canvasContainer);
    container.appendChild(canvas);

    // Create new chart instance
    const chartData = charts[id].data;
    charts[id].chart = new Chart(canvas, {
        type: "bar",
        data: chartData,
        options: {
            responsive: true,
            scales: { y: { display: false, stacked: true, min: 0, max: 1 }, x: { display: false, stacked: true } },
            legend: { display: false },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (item) => {
                            const uptime = item.dataset.dataRaw[item.dataIndex];
                            return uptime >= 0 ? ` ${uptime} %` : null;
                        },
                    },
                },
            },
        },
    });

    // Append generated status
    statusesContainer.appendChild(container);
}

/**
 * Updates status's data and generates new status if needed
 * @param {Object} responseRaw Response from server
 * {id1: {status: true, status_text: "", label: "", bars_max: 48, labels: [], data: []}, id2: ...,}
 * @param {Object} charts Chart's data to update
 */
function _parseUpdateData(responseRaw, charts) {
    // Remove non-existing ones
    const idsToDelete = [];
    Object.keys(charts).forEach((statusID) => {
        if (!(statusID in responseRaw)) idsToDelete.push(statusID);
    });
    idsToDelete.forEach((statusID) => {
        console.log(`Removing status ${statusID}`);
        charts[statusID].chart.destroy();
        const container = document.getElementById(`${statusID}-container`);
        while (container.firstChild) container.removeChild(container.lastChild);
        container.remove();
        delete charts[statusID];
    });

    Object.keys(responseRaw).forEach((statusID) => {
        // Create data for new status
        let create = false;
        if (!(statusID in charts)) {
            create = true;
            console.log(`New status: ${statusID}`);
            charts[statusID] = {};
        }

        if (!("data" in charts[statusID])) charts[statusID].data = { labels: [], datasets: [{ data: [] }] };

        const statusRaw = responseRaw[statusID];

        // Convert timestamps into labels and update chart data
        charts[statusID].data.labels = [];
        (statusRaw.timestamps || []).forEach((startEndTime) => {
            const labelStart = _timestampToString(startEndTime[0] || 0);
            const labelEnd = _timestampToString(startEndTime[1] || 0);
            //charts[statusID].data.labels.push([labelStart, labelEnd]);
            charts[statusID].data.labels.push(`${labelStart} - ${labelEnd}`);
        });
        charts[statusID].data.datasets[0].dataRaw = statusRaw.data || [];
        charts[statusID].data.datasets[0].data = new Array(charts[statusID].data.datasets[0].dataRaw.length).fill(1);

        // Append empty bars to the start if needed
        while (charts[statusID].data.datasets[0].data.length < statusRaw.bars_max) {
            charts[statusID].data.labels.unshift("");
            charts[statusID].data.datasets[0].dataRaw.unshift(-1);
            charts[statusID].data.datasets[0].data.unshift(1);
        }

        // Create new status and chart if not exists
        if (create) _createStatus(charts, statusID);

        // Update title
        document.getElementById(`${statusID}-title`).innerText = statusRaw.label || statusID;

        // Update current status
        const statusElement = document.getElementById(`${statusID}-status`);
        statusElement.innerText = statusRaw.status_text || "-";
        if ("status" in statusRaw)
            statusElement.className =
                statusRaw.status <= 0 ? "not-working" : statusRaw.status == 1 ? "problems" : "working";
        else statusElement.className = "problems";

        // Update time of the last check
        if (statusRaw.timestamps.length != 0) {
            const updateTime = document.getElementById(`${statusID}-update-time`);
            const timeFormatted = _timestampToString(statusRaw.timestamps[statusRaw.timestamps.length - 1][1]);
            updateTime.innerText = `${LAST_CHECK_TEXT} ${timeFormatted}`;
        }

        // Format palette
        let palette = COLOR_PALETTE;
        const paletteReversed = COLOR_PALETTE.endsWith("_r");
        if (paletteReversed) palette = palette.slice(0, -2);

        // Calculate colors based on value (0-100)
        charts[statusID].data.datasets[0].backgroundColor = [];
        charts[statusID].data.datasets[0].dataRaw.forEach((value) => {
            if (value >= 0) {
                const rgb = evaluate_cmap(Math.min(Math.max(value, 0), 100) / 100, palette, !paletteReversed);
                charts[statusID].data.datasets[0].backgroundColor.push(`rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, 0.7)`);
            } else charts[statusID].data.datasets[0].backgroundColor.push("rgba(0, 0, 0, 0.2)");
        });

        // Refresh chart
        charts[statusID].chart.update();
    });
}

/**
 * Requests data from server and updates charts
 * @param {Object} charts Charts data {id1: {chart: chartInstance, data: {labels: [], ...}}, id2: ..., ...}
 */
function requestAndRender(charts) {
    // Get API key from URL
    const apiKey = new URL(window.location.href).searchParams.get("apiKey");

    const xhr = new XMLHttpRequest();
    const url = "/";
    xhr.open("POST", url, true);
    xhr.timeout = 5000;
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onload = function () {
        // Check status
        if (xhr.status !== 200) {
            console.error(`Error: ${xhr.status}`);
            return;
        }

        // Process data
        console.log("Data received");
        _parseUpdateData(JSON.parse(xhr.responseText), charts);
    };
    xhr.ontimeout = (e) => {
        console.error(`Timeout requesting data: ${e}`);
    };

    // Send request
    console.log("Requesting data update...");
    xhr.send(apiKey ? JSON.stringify({ apiKey: apiKey }) : null);
}
