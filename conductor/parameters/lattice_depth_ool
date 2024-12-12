# lattice_depth_ool.py
import os
import json
import copy
import time
from twisted.internet import reactor
import numpy as np

from conductor.parameter import ConductorParameter

class Lattice_depth_ool(ConductorParameter):
    priority = 2
    autostart = True
    data_directory = os.path.join(os.getenv('PROJECT_DATA_PATH'), 'data')
    data_filename = '{}.lattice_depth'

    def initialize(self, c):
        self.connect_to_labrad()

    @property
    def value(self):
        experiment_name = self.server.experiment.get('name')
        shot_number = self.server.experiment.get('shot_number')
        sequence = self.server.parameters.get('sequencer.sequence')
        previous_sequence = self.server.parameters.get('sequencer.previous_sequence')

        value = None
        if (experiment_name is not None) and (sequence is not None):
            point_filename = self.data_filename.format(shot_number)
            rel_point_path = os.path.join(experiment_name, point_filename)
        elif sequence is not None:
            rel_point_path = self.nondata_filename.format(time.strftime('%Y%m%d'))
            
        # if sequence.loop:
        #     if np.intersect1d(previous_sequence.value, self.record_sequences):
        #         value = rel_point_path
        # elif np.intersect1d(sequence.value, self.record_sequences):
        #     value = rel_point_path
        value = rel_point_path
        return value
    
    @value.setter
    def value(self, x):
        pass
    
    def update(self):
        if self.value is not None:
            self.cxn.yeelmo_keysight34470a.record(self.value)
    
Parameter = Lattice_depth_ool
