import json
import numpy as np
import os
import time

from twisted.internet.defer import inlineCallbacks

from conductor.parameter import ConductorParameter

class Recorder(ConductorParameter):
    autostart = False
    priority = 8
    data_filename = '{}.blue_pmt'
    nondata_filename = '{}/blue_pmt'
    pmt_name = 'blue_pmt'
    record_sequences = [
        'lattice_pol_p_linescan',
        'lattice_pol_m_linescan',
        'lattice_pol_m_noClock',
	'vacuum_lifetime',
	'sideband_scan',
	'lattice_unpolarized',
	'readout_pmt',
	'readout_pmt_HV1',
	'readout_pmt_HV2',
	'readout_pmtTRIG',
	'coherent_readout_pmt',
	'readout_pmt_comparison',
	'readout_pmt_2Dimg',
	'readout_pmt_MOT',
    "readout_nz0",
        ]

    def initialize(self, config):
        super(Recorder, self).initialize(config)
        self.connect_to_labrad()
        request = {self.pmt_name: {}}
        self.cxn.pmt.initialize_devices(json.dumps(request))

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
            
        if sequence.loop:
            if np.intersect1d(previous_sequence.value, self.record_sequences):
                value = rel_point_path
        elif np.intersect1d(sequence.value, self.record_sequences):
            value = rel_point_path

        return value
    
    @value.setter
    def value(self, x):
        pass
    
    def update(self):
        if self.value is not None:
            request = {self.pmt_name: self.value}
            self.cxn.pmt.record(json.dumps(request))

Parameter = Recorder

