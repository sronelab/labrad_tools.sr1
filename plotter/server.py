"""
### BEGIN NODE INFO
[info]
name = plotter
version = 1.0
description =
instancename = plotter

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

import imp
import json
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import os
import gc
import sys
import weakref
# import StringIO
import io
from time import time
from collections import OrderedDict, deque

from autobahn.twisted.websocket import WebSocketServerProtocol
from autobahn.twisted.websocket import WebSocketServerFactory
from labrad.server import setting
from twisted.internet import reactor


from server_tools.threaded_server import ThreadedServer

WEBSOCKET_PORT = 9000
MAX_CONNECTIONS = 50
MODULE_CACHE_SIZE = 10

class MyServerProtocol(WebSocketServerProtocol):
    connections = set()  # Use set instead of list for O(1) removal

    def onConnect(self, request):
        # Limit maximum connections to prevent memory issues
        if len(self.connections) >= MAX_CONNECTIONS:
            print("Max connections reached, rejecting: {0}".format(request.peer))
            self.dropConnection()
            return
        self.connections.add(self)
        print("Client connecting: {0}".format(request.peer))

    def onOpen(self):
        print("WebSocket connection open.")

    @classmethod
    def send_figure(cls, figure):
        print('num connections', len(cls.connections))
        # Create copy of connections to avoid modification during iteration
        active_connections = list(cls.connections)
        failed_connections = []

        for c in active_connections:
            try:
                reactor.callFromThread(cls.sendMessage, c, figure, True)
            except Exception as e:
                print("Failed to send to connection: {0}".format(e))
                failed_connections.append(c)

        # Remove failed connections
        for c in failed_connections:
            cls.connections.discard(c)

    @classmethod
    def close_all_connections(cls):
        active_connections = list(cls.connections)
        for c in active_connections:
            try:
                reactor.callFromThread(cls.sendClose, c)
            except Exception as e:
                print("Failed to close connection: {0}".format(e))
        cls.connections.clear()

    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            print("Text message received: {0}".format(payload.decode('utf8')))

        # echo back message verbatim
        self.sendMessage(payload, isBinary)

    def onClose(self, wasClean, code, reason):
        # Use discard instead of remove to avoid KeyError if connection already removed
        self.connections.discard(self)
        print("WebSocket connection closed: {0}".format(reason))

class PlotterServer(ThreadedServer):
    name = 'plotter'
    is_plotting = False

    # a field for silicon frequency. Clock comparision live update purpose.
    frequency_si3 = None

    # Module cache to prevent memory leaks from repeated imports
    _module_cache = OrderedDict()

    # Request queue to handle plot requests during busy periods
    _plot_queue = None

    def initServer(self):
        """ socket server """
        url = u"ws://0.0.0.0:{}".format(WEBSOCKET_PORT)
        factory = WebSocketServerFactory()
        factory.protocol = MyServerProtocol
        reactor.listenTCP(WEBSOCKET_PORT, factory)

        # Initialize plot request queue (maxlen=1 keeps only latest request)
        self._plot_queue = deque(maxlen=1)

    def stopServer(self):
        """ socket server """
        MyServerProtocol.close_all_connections()
        # Clear module cache on shutdown
        self._module_cache.clear()

    def _get_cached_module(self, path, function_name):
        """Get module from cache or load and cache it."""
        cache_key = (path, function_name)

        # Check if module is in cache
        if cache_key in self._module_cache:
            # Move to end (most recently used)
            module = self._module_cache.pop(cache_key)
            self._module_cache[cache_key] = module
            return module

        # Load new module
        try:
            module_name = os.path.split(path)[-1].strip('.py')
            module = imp.load_source(module_name, path)

            # Add to cache
            self._module_cache[cache_key] = module

            # Remove oldest if cache is full
            if len(self._module_cache) > MODULE_CACHE_SIZE:
                oldest_key = next(iter(self._module_cache))
                old_module = self._module_cache.pop(oldest_key)
                # Clean up old module references
                if hasattr(old_module, '__name__') and old_module.__name__ in sys.modules:
                    try:
                        del sys.modules[old_module.__name__]
                    except KeyError:
                        pass
                del old_module
                gc.collect()

            return module

        except Exception as e:
            print("Failed to load module {0}: {1}".format(path, e))
            raise

    @setting(0)
    def plot(self, c, settings_json='{}'):
        settings = json.loads(settings_json)

        # Add request to queue (replaces any existing queued request)
        self._plot_queue.append(settings)

        # Start processing queue if not currently plotting
        if not self.is_plotting:
            reactor.callInThread(self._plot_with_queue)

    def _plot_with_queue(self):
        """Process queued plot requests until queue is empty."""
        while self._plot_queue and not self.is_plotting:
            try:
                settings = self._plot_queue.popleft()
                self._plot(settings)
            except IndexError:
                # Queue became empty between check and popleft
                break
            except Exception as e:
                print('Error processing queued plot: {0}'.format(e))
                # Continue processing remaining items in queue
                continue

    def _plot(self, settings):
        fig = None
        buf = None
        figure_data = None

        try:
            self.is_plotting = True
            print('plotting')
            path = settings['plotter_path']
            function_name = settings['plotter_function'] # name of function that will process data

            # Use cached module instead of loading fresh each time
            module = self._get_cached_module(path, function_name)
            function = getattr(module, function_name)
            fig = function(settings)
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=200)
            buf.seek(0)
            figure_data = buf.read()
            MyServerProtocol.send_figure(figure_data)
            print('done plotting')

        except Exception as e:
            print('failed plotting: {0}'.format(e))
            raise e
        finally:
            self.is_plotting = False

            # Comprehensive cleanup to prevent memory leaks
            try:
                if fig is not None:
                    plt.close(fig)
                    # Clear matplotlib's internal figure manager
                    if hasattr(fig, 'number'):
                        plt.close(fig.number)
            except Exception as e:
                print("Error closing figure: {0}".format(e))

            try:
                if buf is not None:
                    buf.close()
            except Exception as e:
                print("Error closing buffer: {0}".format(e))

            # Clear references
            fig = None
            buf = None
            figure_data = None

            # Force garbage collection
            gc.collect()

    # @setting(1)
    # def retrieve_frquency_si3(self, c):
    #     if self.frequency_si3 is not None:
    #         return str(self.frequency_si3)


Server = PlotterServer

if __name__ == "__main__":
    from labrad import util
    util.runServer(Server())
