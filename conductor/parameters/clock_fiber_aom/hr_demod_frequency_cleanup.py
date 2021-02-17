from twisted.internet.defer import inlineCallbacks
from labrad.wrappers import connectAsync
import json
from conductor.parameter import ConductorParameter

class HrDemodFrequencyCleanup(ConductorParameter):
    autostart = False
    priority = 1
    dark_frequency = 2.0*135.374e6

    def initialize(self,config):
        self.connect_to_labrad()
        request =  {'cu_pulse': self.dark_frequency }
        self.cxn.rf.frequencies(json.dumps(request))

        print 'hr_demod_frequency_cleanup init\'d with freq: {}'.format(self.dark_frequency)
    
    def update(self):
        if self.value is not None:
            request =  {'cu_pulse': self.value } 
            self.cxn.rf.frequencies(json.dumps(request))

Parameter = HrDemodFrequencyCleanup
