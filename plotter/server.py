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
import StringIO
from time import time

from autobahn.twisted.websocket import WebSocketServerProtocol
from autobahn.twisted.websocket import WebSocketServerFactory
from labrad.server import setting
from twisted.internet import reactor


from server_tools.threaded_server import ThreadedServer

WEBSOCKET_PORT = 9000

class MyServerProtocol(WebSocketServerProtocol):
    connections = list()

    def onConnect(self, request):
        self.connections.append(self)
        print("Client connecting: {0}".format(request.peer))

    def onOpen(self):
        print("WebSocket connection open.")
    
    @classmethod
    def send_figure(cls, figure):
        print 'num connections', len(cls.connections)
        for c in set(cls.connections):
            reactor.callFromThread(cls.sendMessage, c, figure, False)
    
    @classmethod
    def close_all_connections(cls):
        for c in set(cls.connections):
            reactor.callFromThread(cls.sendClose, c)
    
    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            print("Text message received: {0}".format(payload.decode('utf8')))

        # echo back message verbatim
        self.sendMessage(payload, isBinary)

    def onClose(self, wasClean, code, reason):
        self.connections.remove(self)
        print("WebSocket connection closed: {0}".format(reason))

class PlotterServer(ThreadedServer):
    name = 'plotter'
    is_plotting = False

    # a field for silicon frequency. Clock comparision live update purpose.
    frequency_si3 = None

    def initServer(self):
        """ socket server """
        url = u"ws://0.0.0.0:{}".format(WEBSOCKET_PORT)
        factory = WebSocketServerFactory()
        factory.protocol = MyServerProtocol
        reactor.listenTCP(WEBSOCKET_PORT, factory)
    
    def stopServer(self):
        """ socket server """
        MyServerProtocol.close_all_connections()

    @setting(0)
    def plot(self, c, settings_json='{}'):
        settings = json.loads(settings_json)
        if not self.is_plotting:
            reactor.callInThread(self._plot, settings)
            #self._plot(settings)
        else:
            print 'still making previous plot'

    def _plot(self, settings):
        try:
            self.is_plotting = True
            print 'plotting'
            path = settings['plotter_path']                 
            function_name = settings['plotter_function'] # name of function that will process data
            module_name = os.path.split(path)[-1].strip('.py')
            module = imp.load_source(module_name, path)
            function = getattr(module, function_name)
            fig = function(settings)
            # retrieve silicon frequency data for the clock lock
            if function_name == "plot_clock_lock":
                all_axes = fig.get_axes()
                silicon_axes = all_axes[1, 0]
                # x_data = []
                y_data = []
                for line in silicon_axes.get_lines():
                    x, y = line.get_data()
                    # x_data.append(x)
                    y_data.append(y)
                self.frequency_si3 = y_data[0][-1]
                print("Si frequency: ",  self.frequency_si3)

            sio = StringIO.StringIO()
            fig.savefig(sio, format='svg')
            sio.seek(0)
            figure_data = sio.read()
            MyServerProtocol.send_figure(figure_data)
            print 'done plotting'
        except Exception as e:
            raise e
            print 'failed plotting'
        finally:
            self.is_plotting = False
            try:
                plt.close(fig)
                del fig
                del sio
                del figure_data
            except:
                pass

    @setting(1)
    def retrieve_frquency_si3(self, c):
        if self.frequency_si3 is not None:
            return str(self.frequency_si3)


Server = PlotterServer

if __name__ == "__main__":
    from labrad import util
    util.runServer(Server())
