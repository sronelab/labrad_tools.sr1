from twisted.internet.defer import inlineCallbacks
from labrad.wrappers import connectAsync
import json
from conductor.parameter import ConductorParameter
from rf.devices.sg380.device import SG380

class HrDemodFrequencyMF(ConductorParameter,SG380):

    autostart = True
    priority = 4

    vxi11_address = '192.168.1.36'

    def update(self):

        if self.value is not None:
            self.frequency = self.value


Parameter = HrDemodFrequencyMF
