# pylint: disable=C0413,E0401
"""Tenreads database monitor API
Runs a minimal Tornado API that notifies on a database connection drop.
Uses periodic callback to plug a listener that sends out an incoming
webhook notification to a specified Slack channel/other receivers.

TODO: Ways to configure notifications

"""

__all__ = ("run_api",)
__author__ = "Sriram Velamur<sriram.velamur@gmail.com>"

import sys
sys.dont_write_bytecode = True
from os import getenv, path, pardir
from datetime import datetime, timedelta

from tornado.web import Application, RequestHandler, StaticFileHandler
from tornado.websocket import WebSocketHandler, WebSocketClosedError
from tornado.ioloop import IOLoop, PeriodicCallback
from pymongo.mongo_client import MongoClient

try:
    DATABASE = MongoClient()["testdb"]
except BaseException:
    print("Unable to connect to database. Cannot proceed")
    sys.exit(1)

LAST_NOTIFIED = None
DATABASE_STATE_CHANGED = False
DATABASE_AVAILABLE = True

ROOT = path.abspath(path.join(path.abspath(__file__), pardir))
WEB_ROOT = path.join(ROOT, "web")
JS_ROOT = path.join(WEB_ROOT, "js")
STYLES_ROOT = path.join(WEB_ROOT, "css")

CHANNELS = {}


def run_periodic():
    """
    Periodic runner method that is called by the IOLoop every specified
    duration.

    Attempts to get the collection names in the database and handles
    the exception as a case when the database is unavailable.

    On unavailable database state, triggers the notifier to send out
    a notification to registered subscribers.

    If database is available and has a previous database state change
    global boolean, sets it to false for allowing further triggers.
    """
    global DATABASE_STATE_CHANGED, LAST_NOTIFIED, DATABASE, DATABASE_AVAILABLE
    try:
        DATABASE.collection_names()
        DATABASE_AVAILABLE = True
        if DATABASE_STATE_CHANGED:
            DATABASE_STATE_CHANGED = False
            LAST_NOTIFIED = None
            notify_db_return()
    except BaseException as db_error:
        DATABASE_STATE_CHANGED = True
        DATABASE_AVAILABLE = False
        notify_error(db_error)


def notify_db_return():
    """
    Helper to notify the consumers of the database returning to an
    available state.

    TODO: Plug in a proper notification backend
    """
    global CHANNELS
    message = "Database back up.."
    status_subscribers = CHANNELS.get("status")
    for subscriber in status_subscribers:
        try:
            subscriber.write_message(get_status_message())
        except WebSocketClosedError:
            pass
    print(message)


def notify_error(db_error):
    """
    Helper to notify the targets on database failure. Triggered when
    the database connectivity is lost, from the periodic callback
    handler.

    :param db_error: Database error encountered
    :type  db_error: Exception

    TODO: Plug in a proper notification backend
    """
    global LAST_NOTIFIED
    current_time_stamp = datetime.utcnow()
    if LAST_NOTIFIED is not None:
        cutoff = LAST_NOTIFIED + timedelta(minutes=5)
        valid = current_time_stamp >= cutoff
    else:
        valid = True

    failure_msg = "Database connection failed. Attempting to notify {}"

    if valid:
        LAST_NOTIFIED = current_time_stamp
        print(failure_msg.format(db_error))

        global CHANNELS
        message = "Database back up.."
        status_subscribers = CHANNELS.get("status", [])
        for subscriber in status_subscribers:
            try:
                subscriber.write_message(get_status_message())
            except WebSocketClosedError:
                pass


class MonitorApplication(Application):
    """Application class for database monitor"""

    def __init__(self, *args, **kwargs):
        """Database monitor application class init"""
        kwargs.update({"debug": getenv("debug") == "True"})
        super(MonitorApplication, self).__init__(*args, **kwargs)
        self.database = DATABASE
        PeriodicCallback(run_periodic, 500).start()
        self.loop = IOLoop.instance()

    def run(self, port=9999):
        """
        Helper to start the app and listen on the specified port.

        :param port: Port to listen on
        :type  port: int
        """
        if not isinstance(port, int):
            port = 9999
        print("Listening on http://0.0.0.0:{}".format(port))
        try:
            self.listen(port)
            self.loop.start()
        except KeyboardInterrupt:
            print("Exiting monitoring app")


def get_status_message():
    """Helper to get a status message based on database connectivity"""
    if not DATABASE_AVAILABLE:
        current_time_stamp = datetime.utcnow()
        time_diff = (current_time_stamp - LAST_NOTIFIED).seconds

        if time_diff < 60:
            delta = "{} seconds ago".format(time_diff)
        else:
            minutes = time_diff // 60
            if minutes > 59:
                delta = "{} hours ago".format(minutes // 60)
            else:
                delta = "{} minutes ago".format(minutes)

        error_html = "Database down. Last reported {}"
        return error_html.format(delta)

    return "All systems up and running"


class StatusSocketController(WebSocketHandler):

    def open(self):
        print("WebSocket opened")

    def on_message(self, message):
        if message != "status":
            return self.write_message("Invalid channel")
        global CHANNELS
        channels = CHANNELS
        status_subscribers = channels.get("status", [])
        status_subscribers.append(self)
        channels["status"] = status_subscribers
        self.write_message(get_status_message())

    def on_close(self):
        print("WebSocket closed")


class RootViewController(RequestHandler):
    """Controller to render the root view for the monitor app"""

    data_chunks = []

    def data_received(self, chunk):
        """Overridden method from abstract RequestHandler class"""
        self.data_chunks.append(chunk)
        super(RootViewController, self).data_received(chunk)

    def get(self, *args, **kwargs):
        """
        HTTP GET request handler method. Renders a template based on
        the database availability status.
        """
        template = path.join(WEB_ROOT, "index.html")
        return self.render(template)


class StatusViewController(RequestHandler):
    """Controller for getting the status of the database"""

    def get(self, *args, **kwargs):
        """
        HTTP GET request handler method. Renders a template based on
        the database availability status.
        """
        return self.write(get_status_message())


def run_api():
    """Main runner for monitor API"""
    MonitorApplication([
        ("^/?$", RootViewController),
        ("^/status/?$", StatusViewController),
        ("^/socket-status/?$", StatusSocketController),
        (r".*/js/(.*)$", StaticFileHandler, {"path": JS_ROOT}),
        (r".*/css/(.*)$", StaticFileHandler, {"path": STYLES_ROOT}),
    ]).run()


if __name__ == '__main__':
    run_api()
