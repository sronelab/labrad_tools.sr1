from twisted.internet.defer import inlineCallbacks
from labrad.wrappers import connectAsync
import json
from conductor.parameter import ConductorParameter
from rf.devices.dg4000.device import DG4000


#writing the MOT waveplate amplitude to the RIGOL that controls it
#sets the waveform parameters as well
class MOT_waveplate_rigol(ConductorParameter,DG4000):

    autostart = True
    priority = 2

    _vxi11_address = '192.168.1.111'
    _source = 1



    def update(self):
        
        if self.value is not None:
            #parameter for driving the waveplate
            self.wave_type = 'SQUare'  #square wave
            self.frequency = 2.0e3 #use 2kHz 
            self.duty_cycle = 50 #50% duty cycle
            self.offset = 0 #0V offset


            self.amplitude = self.value


Parameter = MOT_waveplate_rigol
