import time

from conductor.parameter import ConductorParameter

class Timestamp(ConductorParameter):
    autostart = True
    priority = 100

    def update(self):
        pass

Parameter = Timestamp
