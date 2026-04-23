from twisted.internet.defer import inlineCallbacks
from labrad.wrappers import connectAsync
import json
from conductor.parameter import ConductorParameter
from rf.devices.dg4000.device import DG4000

class Hr_bottom_lo_fsk(ConductorParameter,DG4000):

    autostart = False
    priority = 3

    _vxi11_address = '192.168.1.37'
    _source = 1


    def update(self):
        if self.value is None:
            pass

        elif self.value is not None:
            #use 0 to not update
            if self.value == 0:
                pass
            else:
                self.mod_type = 'FSK'
                self.psk_source = 'EXT'
                self.psk_phase = self.value


Parameter = Hr_bottom_lo_fsk
