from twisted.internet.defer import inlineCallbacks
from labrad.wrappers import connectAsync
import json
from conductor.parameter import ConductorParameter


##TEMPORARILY COPYING FOR TOP CLOCK DDS CONTROL

class HrDemodFrequencyDDS(ConductorParameter):
    autostart = True
    priority = 2
    dark_frequency = 73e6
    dark_offset = 0.0 # keep zero while top clock path uses zeroth order reference.
    ramp_rate = -8.0
    current_value = 0
    def initialize(self,config):
        self.connect_to_labrad()
        #initial_request =  {'top_ad9956_0': {'start': self.dark_frequency, 'stop': self.dark_frequency+self.dark_offset, 'rate': self.ramp_rate} }
        #self.cxn.rf.linear_ramps(json.dumps(initial_request))
        initial_request_low =  {'top_ad9956_1': {'frequency': self.dark_frequency, 'output':'low'} }
        self.cxn.rf.dicfrequencies(json.dumps(initial_request_low))
        initial_request_high =  {'top_ad9956_1': {'frequency': self.dark_frequency+self.dark_offset, 'output':'high'} }
        self.cxn.rf.dicfrequencies(json.dumps(initial_request_high))
        initial_request_ramp = {'top_ad9956_1': self.ramp_rate }
        self.cxn.rf.ramprates(json.dumps(initial_request_ramp))
        print('hr_demod_frequency init\'d with rr: ', self.ramp_rate)

    def update(self):
        if self.value == self.current_value:
            pass
        else:
            if self.value is not None:
                print('[hr_demod_top_dds.py]: clock_aom.hr_demod_frequency', self.value)
    #            min_freq = min([self.value, self.dark_frequency])
    #            max_freq = max([self.value, self.dark_frequency])
#                yield self.cxn.rf.linear_ramp(min_freq, max_freq, self.ramp_rate)
                min_freq = min([self.value, self.value + self.dark_offset])
                max_freq = max([self.value, self.value + self.dark_offset])
                #request =  {'top_ad9956_0': {'start': min_freq, 'stop': max_freq, 'rate': self.ramp_rate} }
                #self.cxn.rf.linear_ramps(json.dumps(request))
                request_low =  {'top_ad9956_1': {'frequency':min_freq, 'output':'low'} }
                self.cxn.rf.dicfrequencies(json.dumps(request_low))
                request_high =  {'top_ad9956_1': {'frequency': max_freq, 'output':'high'} }
                self.cxn.rf.dicfrequencies(json.dumps(request_high))
                #not sutre if it is best to rewrite every time?
                initial_request_ramp = {'top_ad9956_1': self.ramp_rate }
                self.cxn.rf.ramprates(json.dumps(initial_request_ramp))
                self.current_value = self.value
            else:
                pass


Parameter = HrDemodFrequencyDDS
