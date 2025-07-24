from twisted.internet.defer import inlineCallbacks
from labrad.wrappers import connectAsync
import json
from conductor.parameter import ConductorParameter


##TEMPORARILY COPYING FOR TOP CLOCK DDS CONTROL

class HrFrequency_7_5(ConductorParameter):
    autostart = True
    priority = 3
    dark_frequency = 105e6
    output_p=2 #register 4
    output_m=3 #register 5
    current_value = 0

    def initialize(self,config):
        self.connect_to_labrad()
        initial_request =  {'top_ad9956_0': {'frequency': self.dark_frequency, 'output':self.output_p} }
        self.cxn.rf.dicfrequencies(json.dumps(initial_request))
        initial_request =  {'top_ad9956_0': {'frequency': self.dark_frequency, 'output':self.output_m} }
        self.cxn.rf.dicfrequencies(json.dumps(initial_request))
        print('hr_7_5_frequency init\'d with freq: ', self.dark_frequency)

    def update(self):
        if self.value is self.current_value:
            pass
        else:
            if self.value is not None:
                request = {'clock_mF.hr_frequency_top_dds':{}}
                f_steer= self.server._get_parameter_values(request, all=False)['clock_mF.hr_frequency_top_dds']
                f_7_5=self.value
                freq_p=f_steer+f_7_5
                freq_m=f_steer-f_7_5
                # print('clock_aom.hr_7_5_frequency detuning', f_steer-freq_m, f_steer-freq_p)
                # print('f_7_5' , f_7_5)
#            min_freq = min([self.value, self.dark_frequency])
#            max_freq = max([self.value, self.dark_frequency])
#            yield self.cxn.rf.linear_ramp(min_freq, max_freq, self.ramp_rate)
            #freq=self.value
                request_p = {'top_ad9956_0': {'frequency': freq_p, 'output':self.output_p} }
                self.cxn.rf.dicfrequencies(json.dumps(request_p))
                request_m = {'top_ad9956_0': {'frequency': freq_m, 'output':self.output_m} }
                self.cxn.rf.dicfrequencies(json.dumps(request_m))
                self.current_value = self.value
Parameter = HrFrequency_7_5
