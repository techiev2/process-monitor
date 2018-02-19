var app = {
    urls: {
        api: 'http://localhost:9999',
        ws: 'ws://localhost:9999'
    },
    container: document.querySelector('#app-container'),
    xhr: new XMLHttpRequest(),
    ws: null
};

// Helper method to fetch the status over an XMLHttpRequest and update
// the container with the status.
function getStatusAndUpdate() {
    console.info('Fetching status');
    var errorMsg = 'Error fetching status from monitor app';
    app.xhr.open('get', app.urls.api + '/status/', true);
    app.xhr.onreadystatechange = function () {
        if (app.xhr.readyState !== 4) return;
        if (app.xhr.status === 200) {
            app.container.innerHTML = app.xhr.responseText;
            return;
        }
        app.container.innerHTML = errorMsg;
        return;
    };
    app.xhr.send();
}

function fetchOverWebSocket() {
    app.ws = new WebSocket(app.urls.ws + '/socket-status');
    app.ws.onopen = function() {
       app.ws.send('status');
    };
    app.ws.onmessage = function (evt) {
        if (evt.data.indexOf('down') !== -1) {
            app.container.classList.remove('success');
            app.container.classList.add('error');
            document.body.classList.add('error');
        } else {
            app.container.classList.remove('error');
            app.container.classList.add('success');
            document.body.classList.remove('error');
        }
        app.container.innerHTML = '<span>' + evt.data + '</span>';
    };
}

// If the browser environment does not support Websockets,
// use long polling to fetch status via an XHR call every 5 seconds.
if (!window.WebSocket) {
    console.info('Fetching via XHR');
    getStatusAndUpdate();
    setInterval(getStatusAndUpdate, 5000);
} else {
    // If the browser supports WebSocket, use a WebSocket connection to
    // listen to the status from the app
    fetchOverWebSocket();
}