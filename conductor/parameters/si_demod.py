
import json
import time
import os
import traceback

from conductor.parameter import ConductorParameter
import vxi11

class SiDemod(ConductorParameter):
    priority = 6
    autostart = False
    def initialize(self, config):
        self.inst = vxi11.Instrument('128.138.107.33')

    def update(self):

        #Case ensures that if self.value is a unicode string (our json dict),
        #it will then save those values to settings 
#        if isinstance(self.value, unicode):
#            self.settings = json.loads(self.value)


        #if loop for dedrifting
#        if self.settings['drift_boolean'] == True:
#            time_now = time.time()
#            time_initial = self.settings['drift_time_initial']
#            correction = self.settings['drift_rate']*(time_now-time_initial)
#            self.value = self.settings['drift_dummy_freq']+correction


#        else: #If we aren't dedriting (normal comb operation), then just grab demod value!
        response = self.inst.ask('SOUR1:FREQ?')
        self.inst.local()
        self.value = 8 * float(response)

        print('Demod freq: ' + str(self.value))




Parameter = SiDemod
