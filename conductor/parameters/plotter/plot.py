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
    call_in_thread = True

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
        """Call plotter with 0.1 second timeout including connection setup"""
        from twisted.internet import defer, reactor

        def do_plot():
            try:
                # Call plotter server
                return self.cxn.plotter.plot(json.dumps(settings))
            except Exception as e:
                print('Plot call failed: {}'.format(e))
                return defer.fail(e)

        def plot_done(result):
            print('Plot request completed')
            return result

        def plot_timeout():
            print('Plot request timed out after 0.1s')
            return None

        # Create timeout deferred that fires after 0.1 seconds
        timeout_d = defer.Deferred()
        timeout_call = reactor.callLater(0.1, timeout_d.callback, None)

        # Create plot deferred
        plot_d = defer.maybeDeferred(do_plot)
        plot_d.addCallback(plot_done)

        # Race between plot completion and timeout
        d = defer.DeferredList([plot_d, timeout_d], fireOnOneCallback=True, fireOnOneErrback=True)

        def handle_result(result):
            if timeout_call.active():
                timeout_call.cancel()

            # Check which deferred fired first
            if result[0][0] == 0:  # plot_d finished first
                return result[0][1]
            else:  # timeout_d finished first
                return plot_timeout()

        def handle_error(failure):
            if timeout_call.active():
                timeout_call.cancel()
            print('Plot request failed or timed out after 0.1s')
            return None

        d.addCallback(handle_result)
        d.addErrback(handle_error)

Parameter = Plot
