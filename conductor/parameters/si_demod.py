import json
import time
import os
import traceback

from twisted.internet.defer import inlineCallbacks

from conductor.parameter import ConductorParameter


import sys
sys.path.append('/home/srgang/Password/')
from srq_password import password as srqPassword

class SiDemod(ConductorParameter):
    priority = 6
    autostart = False
    def initialize(self,config):
 
       #Connect to stable lasers demod server on Sr2 network
        self.connect_to_labrad(host =  'yesr10.colorado.edu', password = srqPassword)


        #We create an attribute for settings used in demod. This will enable us to toggle on/off make believe dedrifter
        self.settings = [] #json.loads(value)

    def update(self):

        #Case ensures that if self.value is a unicode string (our json dict),
        #it will then save those values to settings 
        if isinstance(self.value, unicode):
            self.settings = json.loads(self.value)


        #if loop for dedrifting
        if self.settings['drift_boolean'] == True:
            time_now = time.time()
            time_initial = self.settings['drift_time_initial']
            correction = self.settings['drift_rate']*(time_now-time_initial)
            self.value = self.settings['drift_dummy_freq']+correction


        else: #If we aren't dedriting (normal comb operation), then just grab demod value!
            self.value = self.cxn.si_demod.get_frequency()

        print('Demod freq: ' + str(self.value))




Parameter = SiDemod
