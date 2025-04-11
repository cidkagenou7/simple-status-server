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

    // Append canvas
    // const canvas_container = document.createElement("div");
    // canvas_container.className = "canvas-container";
    const canvas = document.createElement("canvas");
    canvas.id = `${id}-canvas`;
    // canvas_container.appendChild(canvas);
    // container.appendChild(canvas_container);
    container.appendChild(canvas);

    // Create new chart instance
    const chartData = charts[id].data;
    charts[id].chart = new Chart(canvas, {
        type: "bar",
        data: chartData,
        options: {
            scales: {
                y: { beginAtZero: true, min: 0, max: 100, grid: { color: "#555" } },
                x: { display: false, ticks: { color: "#eee" }, grid: { color: "#555" } },
            },
            legend: { display: false },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (item) => ` ${item.formattedValue} %`,
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
 * {id1: {status: true, status_text: "", label: "", labels: [], data: []}, id2: ...,}
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
        (statusRaw.timestamps || []).forEach((start_end_time) => {
            const label_start = _timestampToString(start_end_time[0] || 0);
            const label_end = _timestampToString(start_end_time[1] || 0);
            //charts[statusID].data.labels.push([label_start, label_end]);
            charts[statusID].data.labels.push(`${label_start} - ${label_end}`);
        });
        charts[statusID].data.datasets[0].data = statusRaw.data || [];

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

        // Calculate colors based on value (0-100)
        charts[statusID].data.datasets[0].backgroundColor = [];
        charts[statusID].data.datasets[0].data.forEach((value) => {
            value = Math.min(Math.max(value, 0), 100);
            charts[statusID].data.datasets[0].backgroundColor.push(`hsla(${value * 1.2}, 80%, 70%, 0.7)`);
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
