from symbol import atom
from conductor.parameter import ConductorParameter
import os
import numpy as np
import h5py

# This class is used to read the tilt sensor through the labjack and store the data in a list
#to add a new tilt sensor, add a new element to the list in initialization and in the update function

class atom_position(ConductorParameter):
    priority=0
    autostart=True

    def initialize(self,config):
        self.value = {
            'x': 0,
            'y': 0,
            'error_x': 0,
            'error_y': 0,
            "sigma_x": 0,
            "sigma_y": 0,
            "sigma_x_error": 0,
            "sigma_y_error": 0,
            }

Parameter = atom_position

