from rf.devices.dg4000 import DG4000
from conductor.parameter import ConductorParameter

#test class for top clock mF
class Parameter(ConductorParameter,DG4000):

#Normally must initialize for first shot
#    def initialize(self,config):

    autostart = False 
    priority = 1


    _vxi11_address = '192.168.1.37'
    _source = 1


    def update(self):
    
        if self.value is not None:
            self.frequency = self.value
            print('Testing new rigol: ' + str(self.frequency))




