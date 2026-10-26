from Picam import *
from typing import Optional
import time
import numpy as np
import h5py
#Kuro camera specific functions
class KuroCamera:
    """Kuro camera specific wrapper with context manager support"""
    
    def __init__(self, camera_id: Optional[PicamCameraID] = None, param = {}):
        self.picam = Picam()
        self.camera = None
        self.camera_id = camera_id
        self.library_initialized = False
        self.camera_opened = False
        self.default_param = {
            "exposure_time": 10.,
            "ROI_x": 300,
            "ROI_y": 195,
            "ROI_width": 512,
            "ROI_height": 60,
        }
        self.param = {}
        for key, value in self.default_param.items():
            self.param[key] = param.get(key, value)
    
    def Connect(self, camera_id: Optional[PicamCameraID] = None) -> bool:
        # Initialize library
        if self.picam.IsLibraryInitialized():
            print("Picam library is already initialized")
        else:
            self.picam.InitializeLibrary()
            print("Picam library initialized")
            self.library_initialized = True

        # Get version
        major, minor, distribution, released = self.picam.GetVersion()
        print(f"Picam version: {major}.{minor}.{distribution}.{released}")
        
        """Connect to Kuro camera"""
        try:
            if camera_id is None:
                # Find Kuro camera
                available_cameras = self.picam.GetAvailableCameraIDs()
                kuro_camera = None
                for cam_id in available_cameras:
                    if cam_id.model in [PicamModel.Kuro1200B, PicamModel.Kuro1608B, PicamModel.Kuro2048B]:
                        kuro_camera = cam_id
                        break
                
                if kuro_camera is None:
                    print(PicamException(PicamError.NoCamerasAvailable))
                
                camera_id = kuro_camera
            
            camera_list = self.picam.GetOpenCameras()
            if len(camera_list):
                self.camera = camera_list[0]
                print("Kuro camera is already connected")
            else:
                self.camera = self.picam.OpenCamera(camera_id)
                print("Kuro camera connected")
            self.camera_id = camera_id
            self.camera_opened = True
            print(f"Camera info: {self.GetCameraInfo()}")
            return True
        except Exception as e:
            print(f"Failed to connect to Kuro camera: {e}")
            self.camera_opened = False
            return False
        except PicamException as e:
            print(f"Failed to connect to Kuro camera: {e}")
            self.camera_opened = False
            return False
    
    def Disconnect(self):
        """Disconnect from camera"""
        if self.camera_opened:
            self.StopAcquisition()
            self.picam.CloseCamera(self.camera)
            self.camera = None
            self.camera_opened = False
            print("Kuro camera disconnected")
        if self.library_initialized:
            self.picam.UninitializeLibrary()
            self.library_initialized = False
            print("Picam library uninitialized")

    def Reconnect(self):
        self.Disconnect()
        self.Connect()
    
    def GetCameraInfo(self) -> dict:
        """Get camera information"""
        camera_id = self.picam.GetCameraID(self.camera)
        return {
            "model": camera_id.model,
            "computer_interface": camera_id.computer_interface,
            "sensor_name": camera_id.sensor_name.decode('utf-8'),
            "serial_number": camera_id.serial_number.decode('utf-8')
        }
    
    def SetExposureTime(self, exposure_time: float):
        """Set exposure time"""
        if self.picam.SetParameterFloatingPointValue(self.camera, PicamParameter.ExposureTime, exposure_time):
            self.param["exposure_time"] = exposure_time

    def GetExposureTime(self) -> float:
        """Get exposure time"""
        return self.picam.GetParameterFloatingPointValue(self.camera, PicamParameter.ExposureTime)

    # def SetTriggerSource(self, id: int):
    #     """Set trigger source"""
    #     self.picam.SetParameterIntegerValue(self.camera, PicamParameter.TriggerSource, id)
    
    # def GetTriggerSource(self) -> str:
    #     """Get trigger source"""
    #     id = self.picam.GetParameterIntegerValue(self.camera, PicamParameter.TriggerSource)
    #     if id == 1:
    #         return "External"
    #     elif id == 2:
    #         return "Internal"
    #     elif id == 3:
    #         return "None_"
    #     else:
    #         return "Unknown"

    def SetTriggerResponse(self, trigger_response: int):
        """Set trigger response"""
        """only suppot 1: NoResponse; 2: ReadoutPerTrigger; 5: StartOnSingleTrigger"""
        self.picam.SetParameterIntegerValue(self.camera, PicamParameter.TriggerResponse, trigger_response)
    
    def GetTriggerResponse(self) -> str:
        """Get trigger response"""
        trigger_response = self.picam.GetParameterIntegerValue(self.camera, PicamParameter.TriggerResponse)
        if trigger_response == 1:
            return "NoResponse"
        elif trigger_response == 2:
            return "ReadoutPerTrigger"
        elif trigger_response == 3:
            return "ShiftPerTrigger"  # unavailable
        elif trigger_response == 4:
            return "ExposeDuringTriggerPulse"  # unavailable
        elif trigger_response == 5:
            return "StartOnSingleTrigger"
        elif trigger_response == 6:
            return "GatePerTrigger"  # unavailable
        else:
            return "Unknown"
        
    # def SetTriggerDetermination(self, id: int):
    #     """Set trigger determination"""
    #     """only suppot id = 3: RisingEdge"""
    #     self.picam.SetParameterIntegerValue(self.camera, PicamParameter.TriggerDetermination, id)
    
    # def GetTriggerDetermination(self) -> str:
    #     """Get trigger determination"""
    #     id = self.picam.GetParameterIntegerValue(self.camera, PicamParameter.TriggerDetermination)
    #     if id == 1:
    #         return "PositivePolarity" 
    #     elif id == 2:
    #         return "NegativePolarity"
    #     elif id == 3:
    #         return "RisingEdge"
    #     elif id == 4:
    #         return "FallingEdge"
    #     elif id == 5:
    #         return "AlternatingEdgeRising"
    #     elif id == 6:
    #         return "AlternatingEdgeFalling"
    #     else:
    #         return "Unknown"
    
    def SetROI(self, x: int, y: int, width: int, height: int, x_binning: int = 1, y_binning: int = 1):
        """Set region of interest"""
        roi = create_roi(x, y, width, height, x_binning, y_binning)
        rois = PicamRois(ctypes.pointer(roi), 1)
        
        if self.picam.SetParameterRoisValue(self.camera, PicamParameter.Rois, rois):
            self.param.update({"ROI_x": x, "ROI_y": y, "ROI_width": width, "ROI_height": height})

    def GetROI(self, is_print=True) -> PicamRois:
        """Get region of interest"""
        rois = self.picam.GetParameterRoisValue(self.camera, PicamParameter.Rois)
        roi_list = []
        for i in range(rois.roi_count):
            roi = rois.roi_array[i]
            if is_print:
                print("ROI {}".format(i+1))
                print("x: {}".format(roi.x))
                print("y: {}".format(roi.y))
                print("width: {}".format(roi.width))
                print("height: {}".format(roi.height))
            roi_list.append([roi.x,roi.y,roi.width,roi.height])
        return rois, roi_list
    
    def SetReadoutCount(self, count: int):
        """Set readout count"""
        self.picam.SetParameterLargeIntegerValue(self.camera, PicamParameter.ReadoutCount, count)
    
    def GetReadoutCount(self) -> int:
        """Get readout count"""
        return self.picam.GetParameterLargeIntegerValue(self.camera, PicamParameter.ReadoutCount)
    
    def GetSensorTemperatureSetPoint(self) -> float:
        """Get sensor temperature set point"""
        return self.picam.GetParameterFloatingPointValue(self.camera, PicamParameter.SensorTemperatureSetPoint)
    
    def SetSensorTemperatureSetPoint(self, setpoint: float):
        """Set sensor temperature set point"""
        self.picam.SetParameterFloatingPointValue(self.camera, PicamParameter.SensorTemperatureSetPoint, setpoint)

    def GetSensorTemperatureReading(self) -> float:
        """Get sensor temperature """
        return self.picam.GetParameterFloatingPointValue(self.camera, PicamParameter.SensorTemperatureReading)
    
    def SetDisableCoolingFan(self, disable: int = 0):
        """Set sensor temperature set point"""
        return self.picam.SetParameterIntegerValue(self.camera, PicamParameter.DisableCoolingFan, disable)
    
    def SetParameters(self, param = {}):
        for key, value in self.param.items():
            self.param[key] = param.get(key, value)
        self.SetExposureTime(self.param["exposure_time"])
        self.SetROI(self.param["ROI_x"],self.param["ROI_y"],self.param["ROI_width"],self.param["ROI_height"])
        
        self.CommitParameters()
        print("Parameters updated")
        for key, value in self.param.items():
            print(key,":",value)
    
    def GetParameters(self):
        params = self.picam.GetParameters(self.camera)
        print(f"[+] Camera has {len(params)} available parameters")
        param_list = {
            "id" : [],
            "name" : [],
            "value" : [],
        }
        for i in range(len(params)):
            param_id = params[i]
            name = PicamParameter(param_id).name
            type = self.picam.GetParameterValueType(self.camera, PicamParameter(param_id))
            if type == 1 or type == 3 or type == 4:
                value = self.picam.GetParameterIntegerValue(self.camera, PicamParameter(param_id))
            elif type == 2:
                value = self.picam.GetParameterFloatingPointValue(self.camera, PicamParameter(param_id))
            elif type == 6:
                value = self.picam.GetParameterLargeIntegerValue(self.camera, PicamParameter(param_id))
            elif type == 5:
                _, value = self.GetROI(is_print=False)
            else:
                value = "Unknown"
            param_list["id"].append(param_id)
            param_list["name"].append(name)
            param_list["value"].append(value)
            print(f"{param_id:6d} | {name:40s} = {value}")
        return param_list
    
    def CommitParameters(self):
        """Commit all parameter changes"""
        failed_parameters = self.picam.CommitParameters(self.camera)
        if failed_parameters:
            print(f"Warning: Failed to commit parameters: {[p.name for p in failed_parameters]}")
    
    def StartAcquisition(self):
        """Start acquisition"""
        self.picam.StartAcquisition(self.camera)
    
    def StopAcquisition(self):
        """Stop acquisition"""
        self.picam.StopAcquisition(self.camera)
    
    def IsAcquisitionRunning(self) -> bool:
        """Check if acquisition is running"""
        return self.picam.IsAcquisitionRunning(self.camera)
    
    def Acquire(self, readout_count: int = 3, timeout: int = 60000) -> PicamAvailableData:
        """Acquire data from camera"""
        data, _ = self.picam.Acquire(self.camera, readout_count, timeout)
        ptr = ctypes.cast(data.initial_readout, ctypes.POINTER(ctypes.c_uint16))
        count = data.readout_count
        image = np.ctypeslib.as_array(ptr, shape=(count*self.param["ROI_height"]*self.param["ROI_width"],))
        print("Acquired readout count: {}".format(count))
        print("Sensor Temperature: {}".format(self.GetSensorTemperatureReading()))
        return count, np.array(image,dtype=np.uint32)
    
    def WaitForAcquisitionUpdate(self, timeout: int = 60000) -> PicamAvailableData:
        """Acquire data from camera"""
        data, _ = self.picam.WaitForAcquisitionUpdate(self.camera, timeout)
        ptr = ctypes.cast(data.initial_readout, ctypes.POINTER(ctypes.c_uint16))
        count = data.readout_count
        image = np.ctypeslib.as_array(ptr, shape=(count*self.param["ROI_height"]*self.param["ROI_width"],))
        print("Acquired readout count: {}".format(count))
        print("Sensor Temperature: {}".format(self.GetSensorTemperatureReading()))
        return count, np.array(image,dtype=np.uint32)
    
    def SaveData(self, count: int, image: np.ndarray, save_path: str):
        image = np.array(image, dtype=np.uint16).reshape((count,self.param["ROI_height"],self.param["ROI_width"]))
        if count == 3:
            images = {key: image[i] for i, key in enumerate(["g", "e", "bg"])}
        else:
            images = {str(i): image[i] for i in range(count)}
        
        with h5py.File(save_path, "w") as h5f:
            for key, value in images.items():
                h5f.create_dataset(key, data=value,compression='gzip',compression_opts=4)
            for key, value in self.param.items():
                h5f.create_dataset(key, data=value)

            h5f.create_dataset("timestamp",data=time.time())
        print("Saved data to {}".format(save_path))
    
    def __enter__(self):
        """Context manager entry - automatically connect to camera"""
        try:
            self.Connect(self.camera_id)
            self.SetReadoutCount(3)
            self.SetTriggerResponse(2)
            self.SetDisableCoolingFan(1)
            self.SetParameters()
            return self
        except:
            self.Disconnect()
            raise
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically disconnect from camera"""
        self.Disconnect()
        return False

    def __del__(self):
        """Context manager del - automatically disconnect from camera"""
        self.Disconnect()
        return False