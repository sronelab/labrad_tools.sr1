import numpy as np
import sys
from collections import deque
import json

ERROR_CODE = {
    20001: "DRV_ERROR_CODES",
    20002: "DRV_SUCCESS",
    20003: "DRV_VXNOTINSTALLED",
    20006: "DRV_ERROR_FILELOAD",
    20007: "DRV_ERROR_VXD_INIT",
    20010: "DRV_ERROR_PAGELOCK",
    20011: "DRV_ERROR_PAGE_UNLOCK",
    20013: "DRV_ERROR_ACK",
    20024: "DRV_NO_NEW_DATA",
    20026: "DRV_SPOOLERROR",
    20034: "DRV_TEMP_OFF",
    20035: "DRV_TEMP_NOT_STABILIZED",
    20036: "DRV_TEMP_STABILIZED",
    20037: "DRV_TEMP_NOT_REACHED",
    20038: "DRV_TEMP_OUT_RANGE",
    20039: "DRV_TEMP_NOT_SUPPORTED",
    20040: "DRV_TEMP_DRIFT",
    20050: "DRV_COF_NOTLOADED",
    20053: "DRV_FLEXERROR",
    20066: "DRV_P1INVALID",
    20067: "DRV_P2INVALID",
    20068: "DRV_P3INVALID",
    20069: "DRV_P4INVALID",
    20070: "DRV_INIERROR",
    20071: "DRV_COERROR",
    20072: "DRV_ACQUIRING",
    20073: "DRV_IDLE",
    20074: "DRV_TEMPCYCLE",
    20075: "DRV_NOT_INITIALIZED",
    20076: "DRV_P5INVALID",
    20077: "DRV_P6INVALID",
    20083: "P7_INVALID",
    20089: "DRV_USBERROR",
    20091: "DRV_NOT_SUPPORTED",
    20095: "DRV_INVALID_TRIGGER_MODE",
    20099: "DRV_BINNING_ERROR",
    20990: "DRV_NOCAMERA",
    20991: "DRV_NOT_SUPPORTED",
    20992: "DRV_NOT_AVAILABLE"
}


class AndorProxy(object):
    """ proxy for controlling Andor cameras on remote computer through labrad
    
    example usage:
        import labrad
        from andor_server.proxy import AndorProxy
    
        cxn = labrad.connect()
        andor = AndorProxy(cxn.yesr10_andor)
    
        # ``andor'' now acts like the local Andor C SDK python wrapper 
        andor.SetTemperature(-60)
        andor.CoolerON()
        andor.StartAcquisition()
    """
    serial_number = 0
    verbose = True
    error = {}

    def __init__(self, andor_server):
        self.andor_server = andor_server
    
    def _log(self, function, error):
        self.error[function] = error
        if self.verbose:
            print "{}: {}".format(function, ERROR_CODE[error])

    def update_records(self, point_filename, frac, tot):
        """ Send data to andor server"""
        data = {point_filename:{"frac":frac, "tot":tot}}
        self.andor_server.update_records(json.dumps(data))
    
    def AbortAcquisition(self):
        """ This function aborts the current acquisition if one is active. """
        error = self.andor_server.abort_acquisition(self.serial_number)
        self._log(sys._getframe().f_code.co_name, error)
        return

    def CancelWait(self):
        """ This function restarts a thread which is sleeping within the 
        WaitForAcquisition function. The sleeping thread will return from 
        WaitForAcquisition with a value not equal to DRV_SUCCESS.
        """
        error = self.andor_server.cancel_wait(self.serial_number)
        self._log(sys._getframe().f_code.co_name, error)
        return 

    def CoolerOFF(self):
        """ Switches OFF the cooling. The rate of temperature change is 
        controlled in some models until the temperature reaches 0o. Control is 
        returned immediately to the calling application.
        """
        error = self.andor_server.cooler_off(self.serial_number)
        self._log(sys._getframe().f_code.co_name, error)
        return

    def CoolerON(self):
        """ Switches ON the cooling. On some systems the rate of temperature 
        change is controlled until the temperature is within 3o of the set 
        value. Control is returned immediately to the calling application.
        """
        error = self.andor_server.cooler_on(self.serial_number)
        self._log(sys._getframe().f_code.co_name, error)
        return

    def GetAcquiredData(self, size):
        """ This function will return the data from the last acquisition. The 
        data are returned as long integers (32-bit signed integers). The "array" 
        must be large enough to hold the complete data set.

        Args:
            size (int): total number of pixels.
        Returns:
            (array) image.
        """
        error, arr = self.andor_server.get_acquired_data(self.serial_number, 
                                                         size)
        self._log(sys._getframe().f_code.co_name, error)
        return np.array(arr, dtype=np.uint32)
    
    def GetAcquiredData16(self, size):
        """ 16-bit version of the GetAcquiredData function. The "array" must 
        be large enough to hold the complete data set.

        Args:
            size (int): total number of pixels.
        Returns:
            (array) image.
        """
        error, arr = self.andor_server.get_acquired_data_16(self.serial_number, 
                                                            size)
        self._log(sys._getframe().f_code.co_name, error)
        return np.array(arr, dtype=np.uint16)

    def GetAcquisitionProgress(self):
        """ This function will return information on the progress of the 
        current acquisition. It can be called at any time but is best used in 
        conjunction with SetDriverEvent. The values returned show the number 
        of completed scans in the current acquisition.

        If 0 is returned for both accum and series then either:
            1 No acquisition is currently running
            2 The acquisition has just completed
            3 The very first scan of an acquisition has just started and not 
                yet completed
        GetStatus can be used to confirm if the first scan has just started, 
        returning DRV_ACQUIRING, otherwise it will return DRV_IDLE.

        For example, if accum=2 and series=3 then the acquisition has completed 
        3 in the series and 2 accumulations in the 4th scan of the series.

        Returns:
            (int) number of accumulations completed in the current kinetic scan.
            (int) number of kinetic scans completed.
        """
        error, acc, series = self.andor_server.get_acquisition_progress(
                self.serial_number)
        self._log(sys._getframe().f_code.co_name, error)
        return acc, series
        
    def GetAcquisitionTimings(self):
        """ This function will return the current "valid" acquisition timing 
        information. This function should be used after all the acquisitions 
        settings have been set, e.g. SetExposureTime, SetKineticCycleTime and 
        SetReadMode etc. The values returned are the actual times used in 
        subsequent acquisitions. This function is required as it is possible 
        to set the exposure time to 20ms, accumulate cycle time to 30ms and 
        then set the readout mode to full image. As it can take 250ms to read 
        out an image it is not possible to have a cycle time of 30ms.

        Returns:
            exposure (float): valid exposure time in seconds
            accumulate (float): valid accumulate cycle time in seconds
            kinetic (float): valid kinetic cycle time in seconds
        """
        error, exposure, accumulate, kinetic = self.andor_server.get_acquisition_timings(
                self.serial_number)
        self._log(sys._getframe().f_code.co_name, error)
        return exposure, accumulate, kinetic

    def GetAvailableCameras(self):
        """ Returns the total number of Andor cameras currently installed. 
        
        It is possible to call this function before any of the cameras are 
        initialized.

        Returns:
            (int) total number of cameras currently installed
        """
        error, totalCameras = self.andor_server.get_available_cameras(
                self.serial_number)
        self._log(sys._getframe().f_code.co_name, error)
        return totalCameras

    def GetBitDepth(self, channel):
        """ This function will retrieve the size in bits of the dynamic range 
        for any available AD channel.

        Args:
            channel (int): the AD channel.
        Returns:
            (int) dynamic range in bits
        """
        error, depth = self.andor_server.get_bit_depth(self.serial_number, channel)
        self._log(sys._getframe().f_code.co_name, error)
        return depth

    def GetCameraHandle(self, cameraIndex):
        """ Returns the handle for the camera specified. 
        
        When multiple Andor cameras are installed the handle of 
        each camera must be retrieved in order to select a camera using the 
        SetCurrentCamera function.

        Args:
            cameraIndex (int): index of any of the installed cameras.
                valid values are 0 to NumberCameras-1 where NumberCameras is the value
                returned by the GetAvailableCameras function.
        Returns:
            (int) handle of the camera.
        """ 
        error, cameraHandle = self.andor_server.get_camera_handle(
                self.serial_number, cameraIndex)
        self._log(sys._getframe().f_code.co_name, error)
        return cameraHandle
    
    def GetCameraSerialNumber(self):
        """ this function will retrieve camera's serial number. """
        error, number = self.andor_server.get_camera_serial_number(
                self.serial_number)
        self._log(sys._getframe().f_code.co_name, error)
        return number

    def GetCurrentCamera(self):
        """ Return the handle of thecurrently selected camera.
        
        When multiple Andor cameras are installed this function returns the 
        handle of the currently selected one.
    
        Returns:
            (int) handle of the currently selected camera
        """
        error, cameraHandle = self.andor_server.get_current_camera(
                self.serial_number)
        self._log(sys._getframe().f_code.co_name, error)
        return cameraHandle

    def GetDetector(self):
        """ This function returns the size of the detector in pixels. The 
        horizontal axis is taken to be the axis parallel to the readout 
        register.

        Returns:
            (int) number of horizontal pixels.
            (int) number of vertical pixels.
        """
        error, xpixels, ypixels = self.andor_server.get_detector(
                self.serial_number)
        self._log(sys._getframe().f_code.co_name, error)
        return xpixels, ypixels

    def GetEMCCDGain(self):
        """ Returns the current gain setting. The meaning of the value returned
        depends on the EM Gain mode.

        Returns:
            (int) current EM gain setting.
        """
        error, gain = self.andor_server.get_emccd_gain(self.serial_number)
        self._log(sys._getframe().f_code.co_name, error)
        return gain
     
    def GetEMGainRange(self):
        """ Returns the minimum and maximum values of the current selected EM 
        Gain mode and temperature of the sensor.

        Returns:
            (int) lowest gain setting
            (int) highest gain setting
        """
        error, low, high = self.andor_server.get_em_gain_range(
                self.serial_number)
        self._log(sys._getframe().f_code.co_name, error)
        return low, high
      
    def GetFastestRecommendedVSSpeed(self):
        """ As your Andor SDK system may be capable of operating at more than 
        one vertical shift speed this function will return the fastest 
        recommended speed available. The very high readout speeds, may require 
        an increase in the amplitude of the Vertical Clock Voltage using 
        SetVSAmplitude. This function returns the fastest speed which does not 
        require the Vertical Clock Voltage to be adjusted. The values returned 
        are the vertical shift speed index and the actual speed in microseconds 
        per pixel shift.

        Returns:
            (int) index of the fastest recommended vertical shift speed.
            (float) speed in microseconds per pixel shift.
        """
        error, index, speed = self.andor_server.get_fastest_recommended_vs_speed(
                self.serial_number)
        self._log(sys._getframe().f_code.co_name, error)
        return index, speed

    def GetHSSpeed(self, channel, typ, index):
        """ As your Andor system is capable of operating at more than one 
        horizontal shift speed this function will return the actual speeds 
        available. The value returned is in MHz.

        Args:
            channel (int): the AD channel.
            typ (int): output amplification.
                0 electron multiplication/Conventional(clara).
                1 conventional/Extended NIR Mode(clara).
            index (int): speed required. 0 to NumberSpeeds-1 where NumberSpeeds 
                is value returned in first parameter after a call to 
                GetNumberHSSpeeds().
        Returns:
            (float) speed in in MHz.
        """
        error, speed = self.andor_server.get_hs_speed(self.serial_number, 
                                                      channel, typ, index)
        self._log(sys._getframe().f_code.co_name, error)
        return speed
            
    def GetNumberADChannels(self):
        """ As your Andor SDK system may be capable of operating with more than 
        one A-D converter, this function will tell you the number available.

        Returns:
            (int) number of allowed channels
        """
        error, channels = self.andor_server.get_number_ad_channels(
                self.serial_number)
        self._log(sys._getframe().f_code.co_name, error)
        return channels

    def GetNumberHSSpeeds(self, channel, typ):
        """ As your Andor SDK system is capable of operating at more than one 
        horizontal shift speed this function will return the actual number of 
        speeds available.

        Args:
            channel (int): the AD channel.
            typ (int): output amplification
                0 electron multiplication.
                1 conventional.
        Returns:
            (int) number of allowed horizontal speeds
        """
        error, speeds = self.andor_server.GetNumberHSSpeeds(self.serial_number, 
                                                            channel, typ)
        self._log(sys._getframe().f_code.co_name, error)
        return speeds

    def GetNumberPreAmpGains(self):
        """ Available in some systems are a number of pre amp gains that can be 
        applied to the data as it is read out. This function gets the number of 
        these pre amp gains available. The functions GetPreAmpGain and 
        SetPreAmpGain can be used to specify which of these gains is to be used.

        Returns:
            (int) number of allowed pre amp gains
        """ 
        error, noGains = self.andor_server.get_number_pre_amp_gains(
                self.serial_number)
        self._log(sys._getframe().f_code.co_name, error)
        return noGains

    def GetNumberVSSpeeds(self):
        """ As your Andor system may be capable of operating at more than one 
        vertical shift speed this function will return the actual number of 
        speeds available.

        Returns:
            (int) number of allowed vertical speeds
        """
        error, speeds = self.andor_server.get_number_vs_speeds(
                self.serial_number)
        self._log(sys._getframe().f_code.co_name, error)
        return speeds

    def GetPreAmpGain(self, index):
        """ For those systems that provide a number of pre amp gains to apply to 
        the data as it is read out; this function retrieves the amount of gain 
        that is stored for a particular index. The number of gains available can 
        be obtained by calling the GetNumberPreAmpGains function and a specific 
        Gain can be selected using the function SetPreAmpGain.

        Args: 
            index (int): gain index. 0 to GetNumberPreAmpGains()-1
        Returns:
            (float) gain factor for this index.
        """
        error, gain = self.andor_server.get_pre_amp_gain(self.serial_number, 
                                                         index)
        self._log(sys._getframe().f_code.co_name, error)
        return gain

    def GetStatus(self):
        """ This function will return the current status of the Andor SDK 
        system. This function should be called before an acquisition is started 
        to ensure that it is IDLE and during an acquisition to monitor the 
        process.

        Returns:
            (str) current status
        """
        error, status = self.andor_server.get_status(self.serial_number)
        self._log(sys._getframe().f_code.co_name, error)
        return ERROR_CODE[status]

    def GetTemperature(self):
        """ This function returns the temperature of the detector to the nearest 
        degree. It also gives the status of cooling process.

        Returns:
            (int) temperature of the detector
        """
        error, temperature = self.andor_server.get_temperature(
                self.serial_number)
        self._log(sys._getframe().f_code.co_name, error)
        return temperature

    def GetVSSpeed(self, index):
        """ As your Andor SDK system may be capable of operating at more than 
        one vertical shift speed this function will return the actual speeds 
        available. The value returned is in microseconds.
        
        Args:
            index (int): speed required. 0 to GetNumberVSSpeeds()-1
        Returns:
            (float) speed in microseconds per pixel shift.
        """
        error, speed = self.andor_server.get_vs_speed(self.serial_number, index)
        self._log(sys._getframe().f_code.co_name, error)
        return speed

    def Initialize(self):
        """ This function will initialize the Andor SDK system. 
        
        As part of the initialization procedure on some cameras (i.e. Classic, 
        iStar and earlier iXion) the DLL will need access to a DETECTOR.ini 
        which contains information relating to the detector head, number pixels, 
        readout speeds etc. If your system has multiple cameras then see the
        section controlling multiple cameras.
        """
        error, initdir = self.andor_server.initialize(self.serial_number)
        self._log(sys._getframe().f_code.co_name, error)
        return initdir
        
    def IsCoolerOn(self):
        """ This function checks the status of the cooler.

        Returns:
            (int) CoolerStatus: 
                0 Cooler is OFF.
                1 Cooler is ON.
        """
        error, iCoolerStatus = self.andor_server.is_cooler_on(
                self.serial_number)
        self._log(sys._getframe().f_code.co_name, error)
        return iCoolerStatus

    def SetAccumulationCycleTime(self, time):
        """ This function will set the accumulation cycle time to the nearest 
        valid value not less than the given value. The actual cycle time used 
        is obtained by GetAcquisitionTimings.

        Args:
            time (float): the accumulation cycle time in seconds.
        """
        error = self.andor_server.set_accumulation_cycle_time(
                self.serial_number, time)
        self._log(sys._getframe().f_code.co_name, error)
        return 

    def SetAcquisitionMode(self, mode):
        """ This function will set the acquisition mode to be used on the next 
        StartAcquisition.

        Args:
            mode (int): acquisition mode.
                1 Single Scan
                2 Accumulate
                3 Kinetics
                4 Fast Kinetics
                5 Run till abort
        """
        error = self.andor_server.set_acquisition_mode(self.serial_number, mode)
        self._log(sys._getframe().f_code.co_name, error)
        return
        
    def SetADChannel(self, channel):
        """ This function will set the AD channel to one of the possible A-Ds of 
        the system. This AD channel will be used for all subsequent operations 
        performed by the system.

        Args:
            index (int): the channel to be used. 0 to GetNumberADChannels-1
        """
        error = self.andor_server.set_ad_channel(self.serial_number, channel)
        self._log(sys._getframe().f_code.co_name, error)
        return 
        
    def SetCoolerMode(self, mode):
        """ This function determines whether the cooler is switched off when 
        the camera is shut down.

        Args:
            mode (int): 
                1 Temperature is maintained on ShutDown
                0 Returns to ambient temperature on ShutDown
        """
        error = self.andor_server.set_cooler_mode(self.serial_number, mode)
        self._log(sys._getframe().f_code.co_name, error)
        return
        
    def SetCurrentCamera(self, cameraHandle):
        """ Select which camera is currently active.
        
        When multiple Andor cameras are installed this function allows the user 
        to select which camera is currently active. Once a camera has been 
        selected the other functions can be called as normal but they will only 
        apply to the selected camera. If only 1 camera is installed calling this 
        function is not required since that camera will be selected by default.

        Args:
            cameraHandle (int): Selects the active camera.
        """
        error = self.andor_server.set_current_camera(self.serial_number, 
                                                     cameraHandle)
        self._log(sys._getframe().f_code.co_name, error)
        return

    def SetEMAdvanced(self, gainAdvanced):
        """ This function turns on and off access to higher EM gain levels 
        within the SDK. Typically, optimal signal to noise ratio and dynamic 
        range is achieved between x1 to x300 EM Gain. Higher gains of > x300 
        are recommended for single photon counting only. Before using higher 
        levels, you should ensure that light levels do not exceed the regime of 
        tens of photons per pixel, otherwise accelerated ageing of the sensor 
        can occur.

        Args:
            state (int): Enables/Disables access to higher EM gain levels.
                1 Enable access
                0 Disable access
        """
        error = self.andor_server.set_em_advanced(self.serial_number, 
                                                  gainAdvanced)
        self._log(sys._getframe().f_code.co_name, error)
        return

    def SetEMCCDGain(self, gain):
        """ Allows the user to change the gain value. The valid range for the 
        gain depends on what gain mode the camera is operating in. See 
        SetEMGainMode to set the mode and GetEMGainRange to get the valid range 
        to work with. To access higher gain values (>x300) see SetEMAdvanced.

        Args:
            gain (int): amount of fain applied.
        """
        error = self.andor_server.set_emccd_gain(self.serial_number, gain)
        self._log(sys._getframe().f_code.co_name, error)
        return
        
    def SetEMGainMode(self, mode):
        """ Set the EM Gain mode to one of the following possible settings. To 
        access higher gain values (if available) it is necessary to enable 
        advanced EM gain, see SetEMAdvanced.
        
        Args:
            mode (int):
                0 The EM Gain is controlled by DAC settings in the range 0-255. 
                    Default mode.
                1 The EM Gain is controlled by DAC settings in the range 0-4095.
                2 Linear mode.
                3 Real EM gain
        """
        error = self.andor_server.set_em_gain_mode(self.serial_number, mode)
        self._log(sys._getframe().f_code.co_name, error)
        return
        
    def SetExposureTime(self, time):
        """ This function will set the exposure time to the nearest valid value 
        not less than the given value. The actual exposure time used is 
        obtained by GetAcquisitionTimings.

        Args:
            time (float): the exposure time in seconds.
        """
        error = self.andor_server.set_exposure_time(self.serial_number, time)
        self._log(sys._getframe().f_code.co_name, error)
        return

    def SetFanMode(self, mode):
        """ Allows the user to control the mode of the camera fan. If the 
        system is cooled, the fan should only be turned off for short periods 
        of time. During this time the body of the camera will warm up which 
        could compromise cooling capabilities. If the camera body reaches too 
        high a temperature, depends on camera, the buzzer will sound. If this 
        happens, turn off the external power supply and allow the system to 
        stabilize before continuing.

        Args:
            mode (int): 
                0 fan on full
                1 fan on low
                2 fan off
        """
        error = self.andor_server.set_fan_mode(self.serial_number, mode)
        self._log(sys._getframe().f_code.co_name, error)
        return
    
    def SetFastKinetics(self, exposedRows, seriesLength, time, mode, hbin, 
            vbin):
        """ This function will set the parameters to be used when taking a fast 
        kinetics acquisition.

        Args:
            exposedRows (int): sub-area height in rows.
            seriesLength (int): number in series.
            time (float): exposure time in seconds.
            mode (int): binning mode (0 - FVB , 4 - Image).
            hbin (int): horizontal binning.
            vbin (int): vertical binning (only used when in image mode).
        """
        error = self.andor_server.set_fast_kinetics(
                self.serial_number, exposedRows, seriesLength, time, mode, hbin, 
                vbin)
        self._log(sys._getframe().f_code.co_name, error)
        return 

    def SetFastKineticsEx(self, exposedRows, seriesLength, time, mode, hbin, 
            vbin, offset):
        """ This function is the same as SetFastKinetics with the addition of
        an Offset parameter, which will inform the SDK of the first row to be used.

        Args:
            exposedRows (int): sub-area height in rows.
            seriesLength (int): number in series.
            time (float): exposure time in seconds.
            mode (int): binning mode (0 - FVB , 4 - Image).
            hbin (int): horizontal binning.
            vbin (int): vertical binning (only used when in image mode).
            offset (int): offset of first row to be used in Fast Kinetics from 
                the bottom of the CCD.
        """
        error = self.andor_server.set_fast_kinetics_ex(
                self.serial_number, exposedRows, seriesLength, time, mode, hbin, 
                vbin, offset)
        self._log(sys._getframe().f_code.co_name, error)
        return 

    def SetFrameTransferMode(self, mode):
        """ This function will set whether an acquisition will readout in Frame 
        Transfer Mode. If the acquisition mode is Single Scan or Fast Kinetics 
        this call will have no affect.

        Args:
            mode (int): mode
                0 OFF
                1 ON
        """ 
        error = self.andor_server.set_frame_transfer_mode(self.serial_number, 
                                                          mode)
        self._log(sys._getframe().f_code.co_name, error)
        return 
        
    def SetHSSpeed(self, typ, index):
        """ This function will set the speed at which the pixels are shifted 
        into the output node during the readout phase of an acquisition. 
        Typically your camera will be capable of operating at several horizontal 
        shift speeds. To get the actual speed that an index corresponds to use
        the GetHSSpeed function.

        Args:
            typ (int): output amplification.
                0 electron multiplication/Conventional(clara).
                1 conventional/Extended NIR mode(clara).
            index (int): the horizontal speed to be used. 
                0 to GetNumberHSSpeeds()-1
        """
        error = self.andor_server.set_hs_speed(self.serial_number, typ, index)
        self._log(sys._getframe().f_code.co_name, error)
        return
        
    def SetImage(self, hbin, vbin, hstart, hend, vstart, vend):
        """ This function will set the horizontal and vertical binning to be 
        used when taking a full resolution image.

        Args:
            hbin (int): number of pixels to bin horizontally.
            vbin (int): number of pixels to bin vertically.
            hstart (int): Start column (inclusive).
            hend (int): End column (inclusive).
            vstart (int): Start row (inclusive).
            vend (int): End row (inclusive).
        """
        error = self.andor_server.set_image(self.serial_number, hbin, vbin, 
                                            hstart, hend, vstart, vend)
        self._log(sys._getframe().f_code.co_name, error)
        return 

    def SetImageFlip(self, iHFlip, iVFlip):
        """ This function will cause data output from the SDK to be flipped on 
        one or both axes. This flip is not done in the camera, it occurs after 
        the data is retrieved and will increase processing overhead. If flipping 
        could be implemented by the user more efficiently then use of this 
        function is not recomended. E.g writing to file or displaying on screen.
        
        Args:
            iHFlip (int): Sets horizontal flipping.
                1 Enables Flipping
                0 Disables Flipping
            iVFlip (int): Sets vertical flipping..
                1 Enables Flipping
                0 Disables Flipping
        """
        error = self.andor_server.set_image_flip(self.serial_number, iHFlip, 
                                                 iVFlip)
        self._log(sys._getframe().f_code.co_name, error)
        return

    def SetImageRotate(self, iRotate):
        """ This function will cause data output from the SDK to be rotated on 
        one or both axes. This rotate is not done in the camera, it occurs after 
        the data is retrieved and will increase processing overhead. If the 
        rotation could be implemented by the user more efficiently then use of 
        this function is not recomended. E.g writing to file or displaying on 
        screen.

        If this function is used in conjunction with the SetImageFlip function 
        the rotation will occur before the flip regardless of which order the 
        functions are called. 180 degree rotation can be achieved using the 
        SetImageFlip function by selecting both horizontal and vertical 
        flipping.

        Args:
            iRotate (int): Rotation setting
                0 No rotation
                1 Rotate 90 degrees clockwise
                2 Rotate 90 degrees anti-clockwise
        """
        error = self.andor_server.set_image_rotate(self.serial_number, iRotate)
        self._log(sys._getframe().f_code.co_name, error)
        return

    def SetKineticCycleTime(self, time):
        """ This function will set the kinetic cycle time to the nearest valid 
        value not less than the given value. The actual time used is obtained 
        by GetAcquisitionTimings.

        Args:
            time (float): the kinetic cycle time in seconds.
        """
        error = self.andor_server.set_kinetic_cycle_time(self.serial_number, time)
        self._log(sys._getframe().f_code.co_name, error)
        return 

    def SetNumberAccumulations(self, number):
        """ This function will set the number of scans accumulated in memory. 
        This will only take effect if the acquisition mode is either Accumulate 
        or Kinetic Series.

        Args:
            number (int): number of scans to accumulate
        """
        error = self.andor_server.set_number_accumulations(self.serial_number, 
                                                           number)
        self._log(sys._getframe().f_code.co_name, error)
        return 

    def SetNumberKinetics(self, number):
        """ This function will set the number of scans (possibly accumulated 
        scans) to be taken during a single acquisition sequence. This will 
        only take effect if the acquisition mode is Kinetic Series.

        Args:
            number (int): number of scans to store.
        """
        error = self.andor_server.set_number_kinetics(self.serial_number, 
                                                      number)
        self._log(sys._getframe().f_code.co_name, error)
        return 

    def SetOutputAmplifier(self, index):
        """ Some EMCCD systems have the capability to use a second output 
        amplifier. This function will set the type of output amplifier to be 
        used when reading data from the head for these systems.

        Args: 
            typ (int): the type of output amplifier.
                0 Standard EMCCD gain register (default)/Conventional(clara).
                1 Conventional CCD register/Extended NIR mode(clara).
        """
        error = self.andor_server.set_output_amplifier(self.serial_number, 
                                                       index)
        self._log(sys._getframe().f_code.co_name, error)
        return 
        
    def SetPreAmpGain(self, index):
        """ This function will set the pre amp gain to be used for subsequent 
        acquisitions. The actual gain factor that will be applied can be found 
        through a call to the GetPreAmpGain function. The number of Pre Amp 
        Gains available is found by calling the GetNumberPreAmpGains function.

        Args:
            index (int): index pre amp gain table. 0 to GetNumberPreAmpGains-1
        """
        error = self.andor_server.set_pre_amp_gain(self.serial_number, index)
        self._log(sys._getframe().f_code.co_name, error)
        return

    def SetReadMode(self, mode):
        """ This function will set the readout mode to be used on the subsequent 
        acquisitions.
        
        Args:
            mode (int): readout mode.
                0 Full Vertical Binning
                1 Multi-Track
                2 Random-Track
                3 Single-Track
                4 Image
        """
        error = self.andor_server.set_read_mode(self.serial_number, mode)
        self._log(sys._getframe().f_code.co_name, error)
        return

    def SetShutter(self, typ, mode, closingtime, openingtime):
        """ This function controls the behaviour of the shutter. The typ 
        parameter allows the user to control the TTL signal output to an 
        external shutter. The mode parameter configures whether the shutter 
        opens & closes automatically (controlled by the camera) or is 
        permanently open or permanently closed. The opening and closing time 
        specify the time required to open and close the shutter.

        Args:
            typ (int): 
                0 Output TTL low signal to open shutter
                1 Output TTL high signal to open shutter
            mode (int):
                0 Fully Auto
                1 Permanently Open
                2 Permanently Closed
                4 Open for FVB series
                5 Open for any series
            closingtime (int): Time shutter takes to close (milliseconds)
            openingtime (int): Time shutter takes to open (milliseconds)
        """ 
        error = self.andor_server.set_shutter(self.serial_number, typ, mode, 
                                              closingtime, openingtime)
        self._log(sys._getframe().f_code.co_name, error)
        return 

    def SetShutterEx(self, typ, mode, closingtime, openingtime, extmode):
        """ This function expands the control offered by SetShutter to allow an 
        external shutter and internal shutter to be controlled independently 
        (only available on some cameras - please consult your Camera User 
        Guide). The typ parameter allows the user to control the TTL signal 
        output to an external shutter. The opening and closing times specify 
        the length of time required to open and close the shutter (this 
        information is required for calculating acquisition timings - see 
        SHUTTER TRANSFER TIME).

        The mode and extmode parameters control the behaviour of the internal 
        and external shutters. To have an external shutter open and  close 
        automatically in an experiment, set the mode parameter to "Open" and set 
        the extmode parameter to "Auto". To have an internal shutter open and 
        close automatically in an experiment, set the extmode parameter to 
        "Open" and set the mode parameter to "Auto". To not use any shutter in 
        the experiment, set both shutter modes to permanently open. 

        Args:
            typ (int):
                0 Output TTL low signal to open shutter
                1 Output TTL high signal to open shutter
            mode (int):
                0 Fully Auto
                1 Permanently Open
                2 Permanently Closed
                4 Open for FVB series
                5 Open for any series
            closingtime (int): time shutter takes to close (milliseconds)
            openingtime (int): Time shutter takes to open (milliseconds)
            mode (int):
                0 Fully Auto
                1 Permanently Open
                2 Permanently Closed
                4 Open for FVB series
                5 Open for any series
        """
        error = self.andor_server.set_shutter_ex(self.serial_number, typ, mode, 
                                                 closingtime, openingtime, 
                                                 extmode)
        self._log(sys._getframe().f_code.co_name, error)
        return 
        
    def SetTemperature(self, temperature):
        """ This function will set the desired temperature of the detector. To 
        turn the cooling ON and OFF use the CoolerON and CoolerOFF function 
        respectively.

        Args:
            temperature (int): the temperature in Centigrade.
                Valid range is given by GetTemperatureRange
        """
        error = self.andor_server.set_temperature(self.serial_number, temperature)
        self._log(sys._getframe().f_code.co_name, error)
        return

    def SetTriggerMode(self, mode):
        """ This function will set the trigger mode that the camera will 
        operate in. 

        Args:
            mode (int): trigger mode.
                0 Internal
                1 External
                6 External Start
                7 External Exposure (Bulb)
                9 External FVB EM (only valid for EM Newton models in FVB mode)
                10 Software Trigger
                12 External Charge Shifting
        """ 
        error = self.andor_server.set_trigger_mode(self.serial_number, mode)
        self._log(sys._getframe().f_code.co_name, error)
        return

    def SetVSSpeed(self, index):
        """ This function will set the vertical speed to be used for subsequent 
        acquisitions        

        Args: 
            index (int): index into the vertical speed table. 
                0 to GetNumberVSSpeeds-1
        """
        error = self.andor_server.set_vs_speed(self.serial_number, index)
        self._log(sys._getframe().f_code.co_name, error)
        return
    
    def ShutDown(self):
        """ This function will close the AndorMCD system down. """
        error = self.andor_server.shut_down(self.serial_number)
        self._log(sys._getframe().f_code.co_name, error)
        return
        
    def StartAcquisition(self):
        """ This function starts an acquisition. The status of the acquisition 
        can be monitored via GetStatus().
        """
        error = self.andor_server.start_acquisition(self.serial_number)
        self._log(sys._getframe().f_code.co_name, error)
        return 

    def WaitForAcquisition(self):
        """ WaitForAcquisition can be called after an acquisition is started 
        using StartAcquisition to put the calling thread to sleep until an 
        Acquisition Event occurs. This can be used as a simple alternative to 
        the functionality provided by the SetDriverEvent function, as all Event 
        creation and handling is performed internally by the SDK library. Like 
        the SetDriverEvent functionality it will use less processor resources 
        than continuously polling with the GetStatus function. If you wish to 
        restart the calling thread without waiting for an Acquisition event, 
        call the function CancelWait. An Acquisition Event occurs each time a 
        new image is acquired during an Accumulation, Kinetic Series or 
        Run-Till-Abort acquisition or at the end of a Single Scan Acquisition. 
        If a second event occurs before the first one has been acknowledged, 
        the first one will be ignored. Care should be taken in this case, as 
        you may have to use CancelWait to exit the function.
        """
        error = self.andor_server.wait_for_acquisition(self.serial_number)
        self._log(sys._getframe().f_code.co_name, error)
        return 


    # Update for Sr1 starts here. 
    def SetSingleTrack(self, center, height):
        """Description:
            This function will set the single track parameters. The parameters are validated in the following order: centre row and then track height.
        Parameters:
            int centre: centre row of track
                Valid range 1 to number of vertical pixels.
            int height: height of track
                Valid range > 1 (maximum value depends on centre row and number of vertical pixels).

        """
        error = self.andor_server.set_single_track(self.serial_number, center, height)
        self._log(sys._getframe().f_code.co_name, error)
        return

    def SetBaselineClamp(self, state):
        """Description:
            This function turns on and off the baseline clamp functionality. With this feature enabled the baseline level of each scan in a kinetic series will be more consistent across the sequence.
        Parameters:
            int state: Enables/Disables Baseline clamp functionality
                1 - Enable Baseline Clamp
                0 - Disable Baseline Clamp
        """
        error = self.andor_server.set_baseline_clamp(self.serial_number, state)
        self._log(sys._getframe().f_code.co_name, error)
        return


    def WaitForAcquisitionTimeOut(self, iTimeOutMs):
        """ 
        Description:
            WaitForAcquisitionTimeOut can be called after an acquisition is started using
            StartAcquisition to put the calling thread to sleep until an Acquisition Event occurs. This
            can be used as a simple alternative to the functionality provided by the SetDriverEvent
            function, as all Event creation and handling is performed internally by the SDK library. Like
            the SetDriverEvent functionality it will use less processor resources than continuously
            polling with the GetStatus function. If you wish to restart the calling thread without waiting
            for an Acquisition event, call the function CancelWait. An Acquisition Event occurs each
            time a new image is acquired during an Accumulation, Kinetic Series or Run-Till-Abort
            acquisition or at the end of a Single Scan Acquisition. If an Acquisition Event does not
            occur within _TimeOutMs milliseconds, WaitForAcquisitionTimeOut returns
            DRV_NO_NEW_DATA
        Parameters:
             int iTimeOutMs: Time before returning DRV_NO_NEW_DATA if no Acquisition Event
            occurs.
        Return:
            DRV_SUCCESS             Acquisition Event occurred.
            DRV_NO_NEW_DATA         Non-Acquisition Event occurred.(eg CancelWait () called, time out) 
        """
        error = self.andor_server.wait_for_acquisition_timeout(self.serial_number, iTimeOutMs)
        self._log(sys._getframe().f_code.co_name, error)
        return 


