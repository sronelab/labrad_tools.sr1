import json
import time
import os
import traceback

from twisted.internet.defer import inlineCallbacks

from conductor.parameter import ConductorParameter

class Plot(ConductorParameter):
    autostart = False
    data_directory = "/media/j/data/"
    priority = 1

    def initialize(self, config):
        self.connect_to_labrad()

    def update(self):
        experiment_name = self.server.experiment.get('name')
        if self.value and (experiment_name is not None):
            try:
                settings = json.loads(self.value)
                experiment_directory = os.path.join(self.data_directory, experiment_name)
                settings['data_path'] = experiment_directory

                # Call plotter with timeout
                self._plot_with_timeout(settings)

            except:
                traceback.print_exc()

    def _plot_with_timeout(self, settings):
        """Call plotter with 0.1 second timeout"""
        try:
            from twisted.internet import defer, reactor

            # Call plotter server
            d = self.cxn.plotter.plot(json.dumps(settings))

            # Add 0.1 second timeout
            timeout_call = reactor.callLater(0.1, d.cancel)

            def plot_done(result):
                if timeout_call.active():
                    timeout_call.cancel()
                print('Plot request completed')
                return result

            def plot_failed_or_timeout(failure):
                if timeout_call.active():
                    timeout_call.cancel()
                print('Plot request failed or timed out after 0.1s')
                return None

            d.addCallback(plot_done)
            d.addErrback(plot_failed_or_timeout)

        except Exception as e:
            print('Plot call failed: {}'.format(e))

Parameter = Plot


# import json
# import time
# import os
# import traceback

# from twisted.internet.defer import inlineCallbacks

# from conductor.parameter import ConductorParameter

# class Plot(ConductorParameter):
#     autostart = False
#     data_directory = "/media/j/data/"
#     priority = 1
#     call_in_thread = True


#     def initialize(self,config):
#         self.connect_to_labrad()

#     def update(self):
#         experiment_name = self.server.experiment.get('name')
#         if self.value and (experiment_name is not None):
# 	    try:
#                 settings = json.loads(self.value)
#                 experiment_directory = os.path.join(self.data_directory,experiment_name)
#                 settings['data_path'] = experiment_directory
#             	self.cxn.plotter.plot(json.dumps(settings))
#             except:
#                 traceback.print_exc()

# Parameter = Plot
