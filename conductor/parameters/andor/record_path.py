import json
import numpy as np
import time
import os
import h5py
import pickle

from conductor.parameter import ConductorParameter

from andor_server.proxy import AndorProxy

class RecordPath(ConductorParameter):
    autostart = True
    priority = 1
    # call_in_thread = True
    record_types = {
        "readout_pmt":"fluorescence",
        "readout_pmtTRIG":"fluorescence",
        "readout_pmt_2Dimg":"fluorescence2D",
	    "readout_pmt_MOT": "fluorescence",
        "readout_pmt_double":"fluorescence_double",
        }
    record_sequences = [
        'readout_pmt',
        "readout_pmt_2Dimg",
        "readout_pmtTRIG",
	    "readout_pmt_MOT",
        "readout_pmt_double"
        ]

    data_filename = '{}.andor.json'
    data2D_filename = '{}.andor.json'
    nondata_filename = '{}/andor.json'
    data_directory = os.path.join(os.getenv('PROJECT_DATA_PATH'), 'data')

    num_kinetic_shots = None

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
        """
        Returns file name to write.
        """
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
        
        # Count the number of imaging requests.
        if intersection != None:
            record_type = self.record_types.get(intersection[-1])

        print("Camera record_type: {}".format(record_type))

        if record_type == 'fluorescence':
            self.num_kinetic_shots = 3
            self.take_fluorescence_image()
        elif record_type == 'fluorescence2D':
            self.num_kinetic_shots = 3
            self.take_fluorescence_image_2D()
        elif record_type == 'fluorescence_double':
            self.num_kinetic_shots = 3
            self.take_fluorescence_image_double()
        else:
            print("Warning: record_type invalid.")

        self.server._send_update({self.name: self.value})
        
    def take_fluorescence_image(self):
        """
        Take 1D image.
        """
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
        andor.SetNumberAccumulations(1)
        andor.SetNumberKinetics(3)
        andor.SetBaselineClamp(0)
        preamp_gain = 2
        andor.SetPreAmpGain(preamp_gain)
        
        andor.SetReadMode(3) # single track mode
        andor.SetSingleTrack(290, 100) 

        
        # Restart the cooler if the temperature of the camera is too high.
        if float(andor.GetTemperature()) > 0:
            print("Cooler restart.")
            andor.SetFanMode(2) # 2 for off
            andor.SetTemperature(-70)
            andor.SetCoolerMode(1) #1 Temperature is maintained on ShutDown
            andor.CoolerON()

        # Start acquisition and get images
        andor.StartAcquisition()
        timeout_ms = 60000
        andor.WaitForAcquisitionTimeOut(timeout_ms)
        temp_image_three = andor.GetAcquiredData(self.num_kinetic_shots*andor.GetDetector()[0])
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

        dummy_data_path = os.path.join(os.getenv('PROJECT_DATA_PATH'),"data","andor_live.pickle")
        with open(dummy_data_path, 'wb') as file:
            pickle.dump(data_string, file, pickle.HIGHEST_PROTOCOL)


        # outputing the status
        print("Image saved to {}".format(data_path))
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
            # andor.SetImage(1, 1, 1, 512, 241, 340)
            andor.SetImage(1, 1, 1, 512, 251, 330)

            andor.StartAcquisition()
            timeout_ms = 60000
            andor.WaitForAcquisitionTimeOut(timeout_ms)

            data = andor.GetAcquiredData(3*80*512).reshape(3, 80, 512)
            images = {key: data[i]
                      for i, key in enumerate(["g", "e", "bg"])}

            dummy_data_path = os.path.join(os.getenv('PROJECT_DATA_PATH'),"data","andor_2D_test.hdf5")

            data_path = os.path.join(self.data_directory, self.value[:-5]+'.hdf5') # convert .json to .hdf5
            data_directory = os.path.dirname(data_path)
            if not os.path.isdir(data_directory):
                os.makedirs(data_directory)

            #Save data

            cam_infos = {
            'time': time.time(),
            'camera_temp': andor.GetTemperature(),
            'emccd_gain': andor.GetEMCCDGain(),
            'preamp_gain': preamp_gain,
            'exposure_time': exposure_time,
            }

            with h5py.File(data_path, "w") as h5f:
                for image in images:
                    h5f.create_dataset(image, data=images[image], 
                            compression=self.compression, 
                            compression_opts=self.compression_level)
                # save camera info
                for cam_info in cam_infos:
                    h5f.create_dataset(cam_info, data=cam_infos[cam_info])

            #Save dummy data for live plotting
            with h5py.File(dummy_data_path, "w") as h5f:
                for image in images:
                    h5f.create_dataset(image, data=images[image], 
                            compression=self.compression, 
                            compression_opts=self.compression_level)

            print("Camera save error: writing dummy file failed.")
            print(data_path)
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
   
    def take_fluorescence_image_double(self):
        """
        Take two 1D flourescence images.
        """
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
        andor.SetNumberAccumulations(1)
        andor.SetNumberKinetics(self.num_kinetic_shots) # Camera will wait for self.num_kinetic_shots triggers.
        print("Number of kinetic shots: {}".format(self.num_kinetic_shots))
        andor.SetBaselineClamp(0)
        preamp_gain = 2
        andor.SetPreAmpGain(preamp_gain)
        
        andor.SetReadMode(3) # single track mode
        andor.SetSingleTrack(290, 100) 

        
        # Restart the cooler if the temperature of the camera is too high.
        if float(andor.GetTemperature()) > 0:
            print("Cooler restart.")
            andor.SetFanMode(2) # 2 for off
            andor.SetTemperature(-70)
            andor.SetCoolerMode(1) #1 Temperature is maintained on ShutDown
            andor.CoolerON()

        # Start acquisition and get images
        # First shot
        ti = time.time()
        andor.StartAcquisition()
        timeout_ms = 60000
        andor.WaitForAcquisitionTimeOut(timeout_ms)
        temp_image_three_num = andor.GetAcquiredData(self.num_kinetic_shots*andor.GetDetector()[0])
        time_start_write = time.time()
        # Process data
        imlen = np.int32(len(temp_image_three_num)/self.num_kinetic_shots)
        temp_image_g_num = temp_image_three_num[0:imlen]
        temp_image_e_num = temp_image_three_num[imlen:2*imlen]
        temp_image_bg_num = temp_image_three_num[2*imlen:3*imlen]
        t1 = time.time()
        print("Frist shot in {} s".format(t1-ti))
        # Second shot
        andor.StartAcquisition()
        andor.WaitForAcquisitionTimeOut(timeout_ms)
        temp_image_three_final = andor.GetAcquiredData(self.num_kinetic_shots*andor.GetDetector()[0])

        # Process data
        imlen = np.int32(len(temp_image_three_final)/self.num_kinetic_shots)
        temp_image_g_final = temp_image_three_final[0:imlen]
        temp_image_e_final = temp_image_three_final[imlen:2*imlen]
        temp_image_bg_final = temp_image_three_final[2*imlen:3*imlen]
        print("Second shot in {} s".format(time.time() - t1))


        # Data dictionary for the first shot.
        data_string_num = {
            'time': time_start_write,
            'g': temp_image_g_num.tolist(),
            'e': temp_image_e_num.tolist(),
            'bg': temp_image_bg_num.tolist(),
            'camera_temp': str(andor.GetTemperature()),
            'emccd_gain': str(andor.GetEMCCDGain()),
            'preamp_gain': str(preamp_gain),
            'exposure_time': str(exposure_time),
            }
        
        # Write data
        data_path = os.path.join(self.data_directory, self.value)
        data_directory = os.path.dirname(data_path)
        if not os.path.isdir(data_directory):
            os.makedirs(data_directory)

        _data_path = data_path.split('.json')[0]
        data_path_num = data_path#_data_path + "_num.json"
        data_path_final = _data_path + "_final.json"

        with open(data_path_num, 'w') as file:
            json.dump(data_string_num,file)
        

        # Data dictionary for the second shot. 
        data_string_final = {
            'time': time_start_write,
            'g': temp_image_g_final.tolist(),
            'e': temp_image_e_final.tolist(),
            'bg': temp_image_bg_final.tolist(),
            'camera_temp': str(andor.GetTemperature()),
            'emccd_gain': str(andor.GetEMCCDGain()),
            'preamp_gain': str(preamp_gain),
            'exposure_time': str(exposure_time),
            }

        # Write data

        with open(data_path_final, 'w') as file:
            json.dump(data_string_final,file)


        # Save image for the live plotter
        dummy_data_path = os.path.join(os.getenv('PROJECT_DATA_PATH'),"data","andor_live.pickle")
        with open(dummy_data_path, 'wb') as file:
            pickle.dump(data_string_num, file, pickle.HIGHEST_PROTOCOL)

        dummy_data_path = os.path.join(os.getenv('PROJECT_DATA_PATH'),"data","andor_final_live.pickle")
        with open(dummy_data_path, 'wb') as file:
            pickle.dump(data_string_final, file, pickle.HIGHEST_PROTOCOL)

        # outputing status of the camera
        print("First shot saved to : {}".format(data_path_num))
        print("Second shot saved to : {}".format(data_path_final))
        print('Camera temp is (C): ' + str(andor.GetTemperature()))
        print('EMCCD gain: ' + str(andor.GetEMCCDGain()))
        print("PreAmp Gain: "+str(andor.GetNumberPreAmpGains()))


Parameter = RecordPath
