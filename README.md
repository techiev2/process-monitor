## Monitor app

A minimal IOLoop PeriodicCallback based application for monitoring database connection status. Runs a Tornado application on port 9999 and periodically checks for the global database object's status every 500ms.

On success/failure, initiates a specific notifier action as specified in one of the helper methods.

From a python shell,
```
from app import run_api
run_api()
```

From the terminal, using a virtual environment for the app.
```
PY_VERSION=3.6 ./scripts/setup
PY_VERSION=3.6 ./scripts/run
```

##### Trigger methods

```
# Update this method to trigger a custom notification/processing flow
# on a monitored process' downtime.
def notify_monitor_error(monitor_error):
    """."""
    pass
```

```
# Update this method to trigger a custom notification/processing flow
# when the monitored process is back up
def notify_monitor_success():
    """."""
    pass
```

```
# Update this method to trigger a custom check for any specific process.
def run_periodic():
    """."""
    pass
```
