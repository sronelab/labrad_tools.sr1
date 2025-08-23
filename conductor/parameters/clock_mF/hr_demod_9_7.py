from twisted.internet.defer import inlineCallbacks
from labrad.wrappers import connectAsync
import json
from conductor.parameter import ConductorParameter


##TEMPORARILY COPYING FOR TOP CLOCK DDS CONTROL

class HrDemodFrequency_9_7(ConductorParameter):
    autostart = True
    priority = 4
    dark_frequency = 73e6
    output_p=0 #ftw 2
    output_m=1
    current_value = 0

    def initialize(self,config):
        self.connect_to_labrad()
        initial_request =  {'top_ad9956_1': {'frequency': self.dark_frequency, 'output':self.output_p} }
        self.cxn.rf.dicfrequencies(json.dumps(initial_request))
        initial_request =  {'top_ad9956_1': {'frequency': self.dark_frequency, 'output':self.output_m} }
        self.cxn.rf.dicfrequencies(json.dumps(initial_request))
        print('hr_demod_9_7_frequency init\'d with rr:' , self.dark_frequency)

    def update(self):
        # if self.value is self.current_value:
        #     pass
        # else:
        if self.value is not None:
                # print('[hr_demod_9_7.py] clock_aom.hr_demod_9_7_frequency', self.value)
#            min_freq = min([self.value, self.dark_frequency])
#            max_freq = max([self.value, self.dark_frequency])
#            yield self.cxn.rf.linear_ramp(min_freq, max_freq, self.ramp_rate)
            freq=self.value
            request_p = {'top_ad9956_1': {'frequency': freq, 'output':self.output_p} }
            self.cxn.rf.dicfrequencies(json.dumps(request_p))
            request_m = {'top_ad9956_1': {'frequency': freq, 'output':self.output_m} }
            self.cxn.rf.dicfrequencies(json.dumps(request_m))
            # self.current_value = self.value
Parameter = HrDemodFrequency_9_7
