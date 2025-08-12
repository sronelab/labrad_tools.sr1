import json
import time
import os
import traceback

from twisted.internet.defer import inlineCallbacks
from twisted.internet import reactor

from conductor.parameter import ConductorParameter

class Plot(ConductorParameter):
    autostart = False
    data_directory = "/media/j/data/"
    priority = 1
    call_in_thread = True  # Keep using conductor's threading mechanism

    def initialize(self, config):
        self.connect_to_labrad()

    def update(self):
        experiment_name = self.server.experiment.get('name')
        if self.value and (experiment_name is not None):
            try:
                settings = json.loads(self.value)
                experiment_directory = os.path.join(self.data_directory, experiment_name)
                settings['data_path'] = experiment_directory

                # Fire-and-forget approach - don't wait for response at all
                reactor.callInThread(self._plot_fire_and_forget, settings)

            except:
                traceback.print_exc()

    def _plot_fire_and_forget(self, settings):
        """Call plotter without waiting for response - completely non-blocking"""
        try:
            self.cxn.plotter.plot(json.dumps(settings))
        except:
            # Silently ignore all failures to prevent any interference
            pass

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
