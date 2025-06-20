from twisted.internet.defer import inlineCallbacks
from labrad.wrappers import connectAsync
import json
from conductor.parameter import ConductorParameter


##TEMPORARILY COPYING FOR TOP CLOCK DDS CONTROL

class HrFrequency_bsb_p(ConductorParameter):
    autostart = True
    priority = 2
    dark_frequency = 105e6
    output_p='high' # reg 6
    # output_m=5 #reg 7
    current_value = None    

    def initialize(self,config):
        self.connect_to_labrad()
        initial_request =  {'top_ad9956_0': {'frequency': self.dark_frequency, 'output':self.output_p} }
        self.cxn.rf.dicfrequencies(json.dumps(initial_request))
        # initial_request =  {'top_ad9956_0': {'frequency': self.dark_frequency, 'output':self.output_m} }
        # self.cxn.rf.dicfrequencies(json.dumps(initial_request))
        print('hr_bsb_p_frequency init\'d with freq: ', self.dark_frequency)
    
    def update(self):
        if self.current_value is self.value:
            pass
        else:
            if self.value is not None:
                request = {'clock_mF.hr_frequency_top_dds':{}}
                f_steer= self.server._get_parameter_values(request, all=False)['clock_mF.hr_frequency_top_dds']
                f_bsb_p=self.value
                freq_p=f_steer+f_bsb_p
                print('clock_aom.hr_bsb_p_frequency detuning',  freq_p)
                print('f_bsb_p' , f_bsb_p)
    #            min_freq = min([self.value, self.dark_frequency])
    #            max_freq = max([self.value, self.dark_frequency])
    #            yield self.cxn.rf.linear_ramp(min_freq, max_freq, self.ramp_rate)
                #freq=self.value
                request_p = {'top_ad9956_0': {'frequency': freq_p, 'output':self.output_p} }
                self.cxn.rf.dicfrequencies(json.dumps(request_p))
                # request_m = {'top_ad9956_0': {'frequency': freq_m, 'output':self.output_m} }
                # self.cxn.rf.dicfrequencies(json.dumps(request_m))
                self.current_value = self.value

Parameter = HrFrequency_bsb_p
