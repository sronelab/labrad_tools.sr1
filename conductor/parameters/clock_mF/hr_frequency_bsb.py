from twisted.internet.defer import inlineCallbacks
from labrad.wrappers import connectAsync
import json
from conductor.parameter import ConductorParameter
from rf.devices.dg4000.device import DG4000

class HrFrequencyBSB(ConductorParameter,DG4000):

    autostart = False
    priority = 3

    _vxi11_address = '192.168.1.37'
    _source = 2


    def update(self):
        if self.value is None:
            pass
        elif self.value is not None:
            #use 0 to not update
            if self.value == 0:
                pass

            else:
                #get the current aom value
                request = {'clock_mF.hr_frequency_mF':{}}
                request_data = self.server._get_parameter_values(request, all=False)
                f_steer = request_data['clock_mF.hr_frequency_mF']
                #sum to give the correct fsk value
                #minus sign because -1 order of aom
                f_fsk = f_steer - float(self.value)

                self.mod_type = 'FSK'
                self.fsk_source = 'EXT'
                self.fsk_frequency = f_fsk


Parameter = HrFrequencyBSB
