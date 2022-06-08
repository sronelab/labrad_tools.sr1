from twisted.internet.defer import inlineCallbacks
from labrad.wrappers import connectAsync
import json
from conductor.parameter import ConductorParameter
from rf.devices.dg4000.device import DG4000

class HrFrequencyBSB(ConductorParameter,DG4000):

    autostart = True
    priority = 2

    _vxi11_address = '192.168.1.37'
    _source = 2


    def update(self):

        if self.value is not None:
            self.mod_type = 'FSK'
            self.fsk_source = 'EXT'
            self.fsk_frequency = self.value


Parameter = HrFrequencyBSB
