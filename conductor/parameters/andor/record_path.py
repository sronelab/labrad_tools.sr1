import json
import numpy as np
import time
import os
import h5py

from conductor.parameter import ConductorParameter

from andor_server.proxy import AndorProxy

class RecordPath(ConductorParameter):
    autostart = True
    priority = 1
    record_types = {
        "image": "absorption", # Sr2 legacy
        "readout_pmt":"fluorescence",
        "readout_pmt_2Dimg":"fluorescence2D"
        }
    record_sequences = [
        'readout_pmt',
        "readout_pmt_2Dimg"
        ]


    # data_filename = '{}.andor.txt'
    # nondata_filename = '{}/andor.txt'
    data_filename = '{}.andor.json'
    nondata_filename = '{}/andor.json'

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
        
        self._andor = andor
    
    @property
    def value(self):
        # Copying some of the blue_pmt.recorder.
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

        if record_type == 'fluorescence2D':
            self.take_fluorescence_image_2D()

        self.server._send_update({self.name: self.value})
        
    def take_fluorescence_image(self):
        """Sr1 
        Take 1D flourescence imaging. """
        andor = self._andor
        andor.AbortAcquisition()
        # Acquisition settings
        andor.SetOutputAmplifier(0)
        andor.SetEMGainMode(2) # Linear gain mode.
        andor.SetEMCCDGain(50)
        exposure_time = 0.001
        andor.SetExposureTime(exposure_time)
        andor.SetShutter(1, 1, 0, 0) # open shutter
        andor.SetHSSpeed(0, 0)
        andor.SetVSSpeed(1)
        andor.SetTriggerMode(1) #external
        andor.SetAcquisitionMode(3)
        andor.SetNumberKinetics(3)
        andor.SetBaselineClamp(0)
        preamp_gain = 2
        andor.SetPreAmpGain(preamp_gain)
        
        andor.SetReadMode(3) # single track mode
        andor.SetSingleTrack(290, 100) 


        # Start acquisition and get images
        andor.StartAcquisition()
        andor.WaitForAcquisition()
        temp_image_three = andor.GetAcquiredData(3*andor.GetDetector()[0])
        time_start_write = time.time()

        # Write data
        data_path = os.path.join(self.data_directory, self.value)
        data_directory = os.path.dirname(data_path)
        if not os.path.isdir(data_directory):
            os.makedirs(data_directory)

        imlen = np.int32(len(temp_image_three)/3)
        temp_image_g = temp_image_three[0:imlen]
        temp_image_e = temp_image_three[imlen:2*imlen]
        temp_image_bg = temp_image_three[2*imlen:3*imlen]

        #data dictionary, add here if you want more stored values
        data_string = {
            'time': time_start_write,
            'g': temp_image_g.tolist(),
            'e': temp_image_e.tolist(),
            'bg': temp_image_bg.tolist(),
            'camera_temp': str(andor.GetTemperature()),
            'emccd_gain': str(andor.GetEMCCDGain()),
            'preamp_gain': str(preamp_gain),
            'exposure_time': str(exposure_time),

            }

        with open(data_path, 'w') as file:
            json.dump(data_string,file)

        # with open(data_path, 'w') as file:
        #     file.write(str(time_start_write) + ' ' + np.array2string(temp_image_g,max_line_width = 5000)[1:-1] + ' \n')
        #     file.write(str(time_start_write) + ' ' + np.array2string(temp_image_e,max_line_width = 5000)[1:-1] + ' \n')
        #     file.write(str(time_start_write) + ' ' + np.array2string(temp_image_bg,max_line_width = 5000)[1:-1] + ' \n')

        # overwrite data for live plot
        dummy_data_path = os.path.join(os.getenv('PROJECT_DATA_PATH'),"data","andor_live.txt")
        with open(dummy_data_path, 'w') as file:
            file.write(str(time_start_write) + ' ' + np.array2string(temp_image_g,max_line_width = 5000)[1:-1] + ' \n')
            file.write(str(time_start_write) + ' ' + np.array2string(temp_image_e,max_line_width = 5000)[1:-1] + ' \n')
            file.write(str(time_start_write) + ' ' + np.array2string(temp_image_bg,max_line_width = 5000)[1:-1] + ' \n')

        print(data_path)
        print('Camera temp is (C): ' + str(andor.GetTemperature()))
        print('EMCCD gain: ' + str(andor.GetEMCCDGain()))
        print("PreAmp Gain: "+str(andor.GetNumberPreAmpGains()))

    def take_fluorescence_image_2D(self):
            # # Sr2 legacy
            andor = self._andor

            andor.AbortAcquisition()
            # Acquisition settings
            andor.SetOutputAmplifier(0)
            andor.SetEMGainMode(2) # Linear gain mode.
            andor.SetEMCCDGain(50)
            exposure_time = 0.001
            andor.SetExposureTime(exposure_time)
            andor.SetShutter(1, 1, 0, 0) # open shutter
            andor.SetHSSpeed(0, 0)
            andor.SetVSSpeed(1)
            andor.SetTriggerMode(1) #external
            andor.SetAcquisitionMode(3)
            andor.SetNumberKinetics(3)
            andor.SetBaselineClamp(0)
            preamp_gain = 2
            andor.SetPreAmpGain(preamp_gain)
            
            andor.SetReadMode(4) # image mode
            andor.SetImage(1, 1, 1, 512, 241, 340)

            andor.StartAcquisition()
            andor.WaitForAcquisition()

            data = andor.GetAcquiredData(3 * 512 * 100).reshape(3, 512, 100)
            images = {key: np.rot90(data[i], 2)
                      for i, key in enumerate(["g", "e", "bg"])}
            dummy_data_path = os.path.join(os.getenv('PROJECT_DATA_PATH'),"data","andor_2D_test.hdf5")
            # data_path = os.path.join(self.data_directory, self.value)
            # data_directory = os.path.dirname(data_path)
            # if not os.path.isdir(data_directory):
            #     os.makedirs(data_directory)

            with h5py.File(dummy_data_path, "w") as h5f:
                for image in images:
                    h5f.create_dataset(image, data=images[image], 
                            compression=self.compression, 
                            compression_opts=self.compression_level)
            print(dummy_data_path)
            print('Camera temp is (C): ' + str(andor.GetTemperature()))
            print('EMCCD gain: ' + str(andor.GetEMCCDGain()))
            print("PreAmp Gain: "+str(andor.GetNumberPreAmpGains()))

            
    def take_absorption_image(self):
        # # Sr2 legacy
        andor = self._andor
        
        andor.AbortAcquisition()
        # andor.SetAcquisitionMode(3)
        # andor.SetReadMode(4)
        # andor.SetNumberAccumulations(1)
        # andor.SetNumberKinetics(2)
        # andor.SetAccumulationCycleTime(0)
        # andor.SetKineticCycleTime(0)
        # andor.SetPreAmpGain(2)
        # andor.SetHSSpeed(0, 0)
        # andor.SetVSSpeed(1)
        # andor.SetShutter(1, 1, 0, 0)
        # andor.SetTriggerMode(1)
        # andor.SetExposureTime(500e-6)
        # andor.SetImage(1, 1, 1, 1024, 1, 1024)
        
        # for i in range(2):
        #     andor.StartAcquisition()
        #     andor.WaitForAcquisition()

        # data = andor.GetAcquiredData(2 * 1024 * 1024).reshape(2, 1024, 1024)
        # images = {key: np.rot90(data[i], 2)
        #           for i, key in enumerate(["image", "bright"])}
        
        # data_path = os.path.join(self.data_directory, self.value)
        # data_directory = os.path.dirname(data_path)
        # if not os.path.isdir(data_directory):
        #     os.makedirs(data_directory)

        # h5f = h5py.File(data_path, "w")
        # for image in images:
        #     h5f.create_dataset(image, data=images[image], 
        #             compression=self.compression, 
        #             compression_opts=self.compression_level)
        # h5f.close()

        # print(data_path)

Parameter = RecordPath
