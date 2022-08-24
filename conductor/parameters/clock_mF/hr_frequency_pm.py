from twisted.internet.defer import inlineCallbacks
from labrad.wrappers import connectAsync
import json
from conductor.parameter import ConductorParameter
from rf.devices.dg4000.device import DG4000

class HrFrequencyPM(ConductorParameter,DG4000):

    autostart = True
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
                self.mod_type = 'PM'
                self.pm_source = 'EXT'
                self.pm_dev = self.value


Parameter = HrFrequencyPM
