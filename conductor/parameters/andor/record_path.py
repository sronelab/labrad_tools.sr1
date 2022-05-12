import json
import numpy as np
import time
import os
import h5py

from conductor.parameter import ConductorParameter

from andor_server.proxy import AndorProxy

class RecordPath(ConductorParameter):
    autostart = False
    priority = 1
    record_types = {
        "image": "absorption", # Sr2 legacy
        "readout_pmt":"fluorescence"
        }

    data_filename = '{}.ikon.hdf5'
    nondata_filename = '{}/ikon.hdf5'

    data_directory = os.path.join(os.getenv('PROJECT_DATA_PATH'), 'data')
    compression = 'gzip'
    compression_level = 4

    def initialize(self, config):
        super(RecordPath, self).initialize(config)
        self.connect_to_labrad()
        andor = AndorProxy(self.cxn.yecookiemonster_andor)
        andor.verbose=False

        andor.Initialize()
        andor.SetFanMode(2) # 2 for off
        andor.SetTemperature(-70)
        andor.SetCoolerMode(1) #1 Temperature is maintained on ShutDown
        andor.CoolerON()

        # Acquisition settings
        andor.SetPreAmpGain(2)
        andor.SetEMGainMode(0)
        andor.SetEMCCDGain(50)
        andor.SetOutputAmplifier(0)
        andor.SetExposureTime(0.001)
        andor.SetShutter(1, 1, 0, 0) # open shutter
        andor.SetReadMode(3) # single track mode
        andor.SetSingleTrack(290, 100) 
        andor.SetHSSpeed(0, 0)
        andor.SetVSSpeed(1)
        andor.SetTriggerMode(1) #external
        andor.SetAcquisitionMode(3)
        andor.SetNumberKinetics(3)
        andor.SetBaselineClamp(0)
        
        # Print settings
        print('Camera temp is (C): ' + str(andor.GetTemperature()))
        print('EMCCD gain: ' + str(andor.GetEMCCDGain()))
        print('PreAmp gain: ' + str(andor.GetPreAmpGain()))
        print('PreAmp gain: ' + str(andor.GetVSSpeed()))

        self._andor = andor
    
    @property
    def value(self):
        experiment_name = self.server.experiment.get('name')
        shot_number = self.server.experiment.get('shot_number')

        rel_point_path = None
        if (experiment_name is not None):
            point_filename = self.data_filename.format(shot_number)
            return os.path.join(experiment_name, point_filename)
        else:
            return self.nondata_filename.format(time.strftime('%Y%m%d'))

    def update(self):
        sequence = self.server.parameters.get('sequencer.sequence')
        previous_sequence = self.server.parameters.get('sequencer.previous_sequence')
        record_type = None
        sequence_value = None

        if sequence.loop:
            sequence_value = previous_sequence.value
        else:
            sequence_value = sequence.value
        intersection = np.intersect1d(sequence_value, self.record_types.keys())
        if intersection:
            record_type = self.record_types.get(intersection[-1])
    
        if record_type == 'absorption':
            self.take_absorption_image()

        if record_type == 'fluorescence':
            self.take_fluorescence_image()

        self.server._send_update({self.name: self.value})
        
    def take_fluorescence_image(self):
        """Sr1 
        Take flourescence imaging. """
        andor = self._andor
        andor.AbortAcquisition()
        # Start acquisition and get images
        andor.StartAcquisition()
        andor.WaitForAcquisition()
        temp_image_three = andor.GetAcquiredData(3*andor.GetDetector()[0])

        # Write data
        data_path = os.path.join(self.data_directory, self.value)
        data_directory = os.path.dirname(data_path)
        if not os.path.isdir(data_directory):
            os.makedirs(data_directory)

        imlen = np.int32(len(temp_image_three)/3)
        temp_image_g = temp_image_three[0:imlen]
        temp_image_e = temp_image_three[imlen:2*imlen]
        temp_image_bg = temp_image_three[2*imlen:3*imlen]

        time_start_write = time.time()

        with open(data_path, 'w') as file:
            file.write(str(time_start_write) + ' ' + np.array2string(temp_image_g,max_line_width = 5000)[1:-1] + ' \n')
            file.write(str(time_start_write) + ' ' + np.array2string(temp_image_e,max_line_width = 5000)[1:-1] + ' \n')
            file.write(str(time_start_write) + ' ' + np.array2string(temp_image_bg,max_line_width = 5000)[1:-1] + ' \n')

        print(data_path)


    def take_absorption_image(self):
        # Sr2 legacy
        andor = self._andor
        
        andor.AbortAcquisition()
        andor.SetAcquisitionMode(3)
        andor.SetReadMode(4)
        andor.SetNumberAccumulations(1)
        andor.SetNumberKinetics(2)
        andor.SetAccumulationCycleTime(0)
        andor.SetKineticCycleTime(0)
        andor.SetPreAmpGain(0)
        andor.SetHSSpeed(0, 0)
        andor.SetVSSpeed(1)
        andor.SetShutter(1, 1, 0, 0)
        andor.SetTriggerMode(1)
        andor.SetExposureTime(500e-6)
        andor.SetImage(1, 1, 1, 1024, 1, 1024)
        
        for i in range(2):
            andor.StartAcquisition()
            andor.WaitForAcquisition()

        data = andor.GetAcquiredData(2 * 1024 * 1024).reshape(2, 1024, 1024)
        images = {key: np.rot90(data[i], 2)
                  for i, key in enumerate(["image", "bright"])}
        
        data_path = os.path.join(self.data_directory, self.value)
        data_directory = os.path.dirname(data_path)
        if not os.path.isdir(data_directory):
            os.makedirs(data_directory)

        h5f = h5py.File(data_path, "w")
        for image in images:
            h5f.create_dataset(image, data=images[image], 
                    compression=self.compression, 
                    compression_opts=self.compression_level)
        h5f.close()

        print(data_path)

Parameter = RecordPath
