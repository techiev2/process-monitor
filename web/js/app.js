var api = "http://localhost:9999";
var statusURL = api + "/status/";
var container = document.querySelector("#app-container");
var xhr = new XMLHttpRequest();

function getStatusAndUpdate() {
    console.info("Fetching status");
    xhr.open("get", statusURL, true);
    xhr.onreadystatechange = function () {
        if (xhr.readyState !== 4) return;
        if (xhr.status === 200) {
            container.innerHTML = xhr.responseText;
            return;
        }
        container.innerHTML = "Error fetching status from monitor app";
        return;
    };
    xhr.send();
}


if (!window.WebSocket) {
    // Use long polling to fetch status via an XHR call every 30 seconds
    console.info("Fetching via XHR");
    getStatusAndUpdate();
    setInterval(getStatusAndUpdate, 5000);
} else {
    var ws = new WebSocket("ws://localhost:9999/socket-status");
    ws.onopen = function() {
       ws.send("status");
    };
    ws.onmessage = function (evt) {
        container.innerHTML = evt.data;
    };
}