from twisted.internet.defer import inlineCallbacks
from labrad.wrappers import connectAsync
import json
from conductor.parameter import ConductorParameter
from rf.devices.dg4000.device import DG4000

class HrShake(ConductorParameter,DG4000):

    autostart = False
    priority = 3

    _vxi11_address = '192.168.1.37'
    _source = 2


    def update(self):
        pass
        # request = {'f_7_5': {}}
        # f_7_5 = self.server._get_parameter_values(request, all=False)['f_7_5']
        # request = {'clock_fiber_aom.hr_demod_frequency': {}}
        # f_lo = self.server._get_parameter_values(request, all=False)['clock_fiber_aom.hr_demod_frequency']

        # self.mod_type = 'FSK'
        # self.fsk_source = 'EXT'
        # self.amplitude = 1.4159
        # self.frequency = f_lo+f_7_5
        # self.fsk_frequency = f_lo-f_7_5

        # request = {
        #             'clock_mF.hr_shake': float(f_lo+f_7_5),
        #             }
        # self.server._set_parameter_values(request)  


Parameter = HrShake
