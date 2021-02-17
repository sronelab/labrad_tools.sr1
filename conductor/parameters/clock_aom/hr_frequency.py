from twisted.internet.defer import inlineCallbacks
from labrad.wrappers import connectAsync
import json
from conductor.parameter import ConductorParameter

class HrFrequency(ConductorParameter):
    autostart = True
    priority = 2
    dark_frequency = 57.622e6
    dark_offset = 1e6
    ramp_rate = -8

    def initialize(self, config):
        self.connect_to_labrad()
        initial_request =  {'ad9956_1': {'start': self.dark_frequency, 'stop': self.dark_frequency+self.dark_offset, 'rate': self.ramp_rate} }
        self.cxn.rf.linear_ramps(json.dumps(initial_request))
        print 'hr_frequency init\'d with rr: {}'.format(self.ramp_rate)
    
    def update(self):
        if self.value is not None:
            print 'clock_aom.hr_frequency', self.value
#            min_freq = min([self.value, self.dark_frequency])
#            max_freq = max([self.value, self.dark_frequency])
#            yield self.cxn.rf.linear_ramp(min_freq, max_freq, self.ramp_rate)
            min_freq = min([self.value, self.value + self.dark_offset])
            max_freq = max([self.value, self.value + self.dark_offset])
            request =  {'ad9956_1': {'start': min_freq, 'stop': max_freq, 'rate': self.ramp_rate} }
            self.cxn.rf.linear_ramps(json.dumps(request))

Parameter = HrFrequency    
