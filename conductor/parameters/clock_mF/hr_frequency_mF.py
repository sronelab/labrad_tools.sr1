from twisted.internet.defer import inlineCallbacks
from labrad.wrappers import connectAsync
import json
from conductor.parameter import ConductorParameter
from rf.devices.dg4000.device import DG4000

class HrFrequencyMF(ConductorParameter,DG4000):

    autostart = False
    priority = 2

    _vxi11_address = '192.168.1.37'
    _source = 2


    def update(self):

        if self.value is not None:
            self.frequency = self.value


Parameter = HrFrequencyMF
