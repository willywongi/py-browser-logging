## Overview
This is a collection of tools to handle logging messages from python WSGI applications to the browser's own console. It works with Chrome with the [http://chromelogger.com](ChromeLogger extension) and with Firefox Dev Tools (builtin since 44, see [https://hacks.mozilla.org/2015/10/firebug-devtools-integration/](this))

Chrome Logger, and the server libraries like this,  uses a [https://craig.is/writing/chromelogger/techspecs](open protocol). Chrome Logger author wrote a library to log message to the browser console, but uses a standalone logging facility; this tool lets you use python builtin logging utils giving just a Handler that collects log messages and flush them out to the response headers; it's also thread safe.

## Getting Started

1a. Install [Chrome Logger](https://chrome.google.com/extensions/detail/noaneddfkdjfnfdakjjmocngnfkfehhd) from the Chrome Web Store
1b. Use Firefox version 44 or up. If the latest Firefox version is smaller, use Firefox Developer Edition.

2. Copy``browser_logging.py´´ where needed

3. In your WSGI app, add the middleware
```python
from browser_logging import BrowserLoggingMiddleware
from yourpackage import YourWSGIApp

application = BrowserLoggingMiddleware(YourWSGIapp, logger_name='yourlogger')
```

4. In your application use the standard library's logging utility
```python
import logging
logger = logging.getLogger('yourlogger')

logger.debug("Hello world: %s", 42)
```

5. Enjoy server logging on the browser

## Using with Django, Tornado and stuff
TODO! I assume these framework are WSGI compliant, but I can't tell. 

## Warnings
Logging emitting is not configurable, so don't use this in production. In the future we will have ChromeLogger and Firefox Dev Tools to send along a request header, so the middleware will be able to decide wether to send the logging data.


