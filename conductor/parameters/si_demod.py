
import json
import time
import os
import traceback

from conductor.parameter import ConductorParameter
# import vxi11
import urllib2 # for python 2 compatibility

class SiDemod(ConductorParameter):
    priority = 6
    autostart = False
    current_freq = 21.0e6
    timeout = 0.1
    url="http://128.138.107.123:8080" # YeDemod in comb setup.
    def initialize(self, config):
        #self.inst = vxi11.Instrument('128.138.107.33')
        self.value = 8*21.0e6

    def update(self):

        try:
            _freq = float(urllib2.urlopen(self.url, timeout=self.timeout).read().strip())
            self.current_freq = _freq
        except:
            _freq = self.current_freq
            print("[Warning] issues on reading demod frequency.")



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
        #response = self.inst.ask('SOUR1:FREQ?')
        #self.inst.local()
        self.value = 8.0 * _freq# float(8.0 * 21.885e6) # 8 * float(response)

        # print('Demod freq: ' + str(self.value))




Parameter = SiDemod
