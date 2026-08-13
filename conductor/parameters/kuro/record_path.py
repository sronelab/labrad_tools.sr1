import json
import numpy as np
import time
import os
import h5py
import pickle
from scipy.optimize import curve_fit
from collections import deque
from twisted.internet.reactor import callInThread

from conductor.parameter import ConductorParameter

from Kuro.proxy import KuroProxy
# from Kuro.Picam import PicamCameraID, PicamModel, PicamComputerInterface
from update.proxy import UpdateProxy

class RecordPath(ConductorParameter):
    name = "Kuro"
    autostart = False
    priority = 2
    call_in_thread = True

    data_filename = '{}.kuro.json'
    nondata_filename = '{}/kuro.hdf5'
    data_directory = os.path.join(os.getenv('PROJECT_DATA_PATH'), 'data')
    _update_proxy = None

    # camera_id = PicamCameraID()
    # camera_id.model = PicamModel.Kuro1200B.value
    # camera_id.computer_interface = PicamComputerInterface.Usb3.value
    # camera_id.sensor_name = 'PI 1200 x 1200 CMOS (B)'.encode('utf-8') 
    # camera_id.serial_number = 'K23F203001'.encode('utf-8')

    ini_param = {
        "exposure_time": 3.,
        "ROI_x": 260,
        "ROI_y": 20,
        "ROI_width": 512,
        "ROI_height": 60,
    }

    def initialize(self, config):
        super(RecordPath, self).initialize(config)
        self.connect_to_labrad()
        try:
            kuro = KuroProxy(self.cxn.yesrh_kuro)
            # kuro.Initialize()
            self.kuro = kuro
        except:
            print("WARNING: Cannot connect to KuroProxy. Camera might not work")
            self.kuro = None

        # default setting
        # self.kuro.Connect()
        # self.kuro.SetReadoutCount(3)
        # self.kuro.SetTriggerResponse(2)
        # self.kuro.SetDisableCoolingFan()
        # self.kuro.SetParameters(self.ini_param)

        # Setup update server proxy for real-time notifications
        try:
            self._update_proxy = UpdateProxy('kuro_data')
            print("Connected to update server for real-time notifications")
        except:
            print("WARNING: Cannot connect to update server. Real-time notifications disabled")
            self._update_proxy = None

    @property
    def value(self):
        """
        Returns file name to write.
        """
        experiment_name = self.server.experiment.get('name')
        shot_number = self.server.experiment.get('shot_number')
        sequence = self.server.parameters.get('sequencer.sequence')

        value = None
        if (experiment_name is not None) and (sequence is not None):
            point_filename = self.data_filename.format(shot_number)
            rel_point_path = os.path.join(experiment_name, point_filename)
        elif sequence is not None:
            rel_point_path = self.nondata_filename.format(time.strftime('%Y%m%d'))

        return rel_point_path


    @value.setter
    def value(self, x):
        pass

    def update(self):
        value = self.value
        if value is not None:
            tot, frac = self.take_fluorescence_image_2D(value)

            # send data to the proxy instance.
            shotnumber = self.server.experiment.get('shot_number')
            experiment_name = self.server.experiment.get('name')
            point_filename = "{}_{}".format(experiment_name, shotnumber)
            self.kuro.update_records(point_filename, frac, tot)


    def take_fluorescence_image_2D(self, value):
        self.kuro.StopAcquisition()

        dummy_data_path = os.path.join(os.getenv('PROJECT_DATA_PATH'),"data","kuro_2D_test.hdf5")
        data_path = os.path.join(self.data_directory, value)
        data_directory = os.path.dirname(data_path)
        if not os.path.isdir(data_directory):
            os.makedirs(data_directory)

        time_acquire = time.time()
        count, image = self.kuro.Acquire(readout_count = 3, timeout = 60000)
        image = np.array(image).reshape((count,self.ini_param["ROI_height"],self.ini_param["ROI_width"]))
        if count == 3:
            images = {key: image[i] for i, key in enumerate(["g", "e", "bg"])}
        else:
            images = {str(i): image[i] for i in range(count)}

        self.SaveData_1d(images, data_path, time_acquire)
        self.SaveData_2d(images, dummy_data_path, time_acquire)
        self.Fit_Position(images)

        if count == 3:
            g = np.sum(images["g"]-images["bg"])
            e = np.sum(images["e"]-images["bg"])
            tot = e + g
            if tot == 0:
                frac = 0
            else:
                frac = e / tot
            return tot, frac
        else:
            return 0, 0
    
    def SaveData_1d(self, images, save_path, time_acquire):
        # image_1d = {key: np.sum(value,axis=0) for key, value in images.items()}
        # with h5py.File(save_path, "w") as h5f:
        #     for key, value in image_1d.items():
        #         h5f.create_dataset(key, data=value, compression='lzf')
        #     h5f.create_dataset("time",data=time_acquire)
        image_1d = {key: np.sum(value,axis=0).tolist() for key, value in images.items()}
        image_1d["time"] = time_acquire
        with open(save_path, "w") as file:
            json.dump(image_1d, file)

        print("Saved data to {}".format(save_path))

    def SaveData_2d(self, images, save_path, time_acquire):
        with h5py.File(save_path, "w") as h5f:
            for key, value in images.items():
                h5f.create_dataset(key, data=value, compression='lzf')
            h5f.create_dataset("time",data=time_acquire)
        print("Saved data to {}".format(save_path))

    def Fit_Position(self, image):
        tot = image["e"]+image["g"]-2*image["bg"]
        fit_result = perform_fit(tot)
        value = {
            'x': fit_result['x0'],
            'y': fit_result['y0'],
            'error_x': fit_result['x0_error'],
            'error_y': fit_result['y0_error'],
            "sigma_x": fit_result['sigma_x'],
            "sigma_y": fit_result['sigma_y'],
            "sigma_x_error": fit_result['sigma_x_error'],
            "sigma_y_error": fit_result['sigma_y_error'],
        }
        parameter = self.server.parameters["atom_position"]
        parameter.value.update(value)


Parameter = RecordPath

def perform_fit(imag):
        try:
            proj_x = np.sum(imag, axis=0)
            proj_y = np.sum(imag, axis=1)
            x_axis = np.arange(len(proj_x))
            y_axis = np.arange(len(proj_y))
            
            guess_x = get_initial_guess(x_axis, proj_x)
            popt_x, pcov_x = curve_fit(gaussian_1d, x_axis, proj_x, p0=guess_x, maxfev=2000)
            perr_x = np.sqrt(np.diag(pcov_x))
            _, mu_x, sigma_x, _ = popt_x
            err_mu_x = perr_x[1]
            err_sigma_x = perr_x[2]

            guess_y = get_initial_guess(y_axis, proj_y)
            popt_y, pcov_y = curve_fit(gaussian_1d, y_axis, proj_y, p0=guess_y, maxfev=2000)
            perr_y = np.sqrt(np.diag(pcov_y))
            _, mu_y, sigma_y, _ = popt_y
            err_mu_y = perr_y[1]
            err_sigma_y = perr_y[2]

            return {
                "x0": mu_x,
                "y0": mu_y,
                "sigma_x": np.abs(sigma_x),
                "sigma_y": np.abs(sigma_y),
                "x0_error": err_mu_x,
                "y0_error": err_mu_y,
                "sigma_x_error": err_sigma_x,
                "sigma_y_error": err_sigma_y,
            }
        except Exception as e:
            print("Atom Position Fit Error: {}".format(e))
            return get_empty_fit()

def get_empty_fit():
    keys = ["x0", "y0", "sigma_x", "sigma_y", 
            "x0_error", "y0_error", "sigma_x_error", "sigma_y_error"]
    return {k: 0.0 for k in keys}

def gaussian_1d(x, amp, mu, sigma, offset):
    return amp * np.exp(-((x - mu) ** 2) / (2 * sigma ** 2)) + offset

def get_initial_guess(x, data):
    margin = max(1, int(len(data) * 0.1))
    offset_guess = np.mean(np.concatenate((data[:margin], data[-margin:])))
    amp_guess = np.max(data) - offset_guess
    clean_data = np.maximum(data - offset_guess, 0)
    total_mass = np.sum(clean_data)
    if total_mass == 0:
        mu_guess = np.mean(x)
    else:
        mu_guess = np.sum(x * clean_data) / total_mass
    if total_mass == 0:
        sigma_guess = len(data) / 2.0
    else:
        sigma_guess = np.sqrt(np.sum(clean_data * (x - mu_guess)**2) / total_mass)
        
    return [amp_guess, mu_guess, sigma_guess, offset_guess]