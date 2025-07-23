from twisted.internet.defer import inlineCallbacks
from labrad.wrappers import connectAsync
import json
from conductor.parameter import ConductorParameter
from rf.devices.dg4000.device import DG4000

class HrFrequencyPSK(ConductorParameter,DG4000):

    autostart = False
    priority = 2

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
                self.mod_type = 'PSK'
                self.psk_source = 'EXT'
                self.psk_phase = self.value


Parameter = HrFrequencyPSK
