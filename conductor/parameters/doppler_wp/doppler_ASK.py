from twisted.internet.defer import inlineCallbacks
from labrad.wrappers import connectAsync
import json
from conductor.parameter import ConductorParameter
from rf.devices.dg4000.device import DG4000

class waveplate_ASK(ConductorParameter,DG4000):

    autostart = True
    priority = 2

    _vxi11_address =  '192.168.1.111'
    _source = 1


    def update(self):
        if self.value is None:
            pass

        elif self.value is not None:
            #use 0 to not update
            if self.value == 0:
                pass
            else:
                self.mod_type = 'ASK'
                self.ask_source = 'EXT'
                self.ask_polarity = 'NEG'
                self.ask_amplitude = self.value


Parameter = waveplate_ASK
