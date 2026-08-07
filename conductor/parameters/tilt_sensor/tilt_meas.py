# from twisted.internet.defer import inlineCallbacks
from labrad.wrappers import connectAsync
import json
from conductor.parameter import ConductorParameter


# This class is used to read the tilt sensor through the labjack and store the data in a list
#to add a new tilt sensor, add a new element to the list in initialization and in the update function

class tilt_meas(ConductorParameter):
    priority=2
    autostart=True

# Initialize the list with the tilt sensors
    def initialize(self,config):
        self.connect_to_labrad()
        self.value= [-100, -100, -100]
        self.registers=["AIN0", "AIN1", "AIN2", "AIN3"]
        print(self.registers)

    def update(self):
        if self.value is not None:
            self.value = self.cxn.yezoe_labjack.read_names(self.registers).tolist()
            # print(self.value)

Parameter = tilt_meas