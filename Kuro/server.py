"""
### BEGIN NODE INFO
[info]
name = kuro
version = 1.0
description = 
instancename = %LABRADNODE%_kuro

[startup]
cmdline = %PYTHON% %FILE%
timeout = 60

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""
from labrad.server import LabradServer, setting
from Picam import PicamCameraID, PicamModel, PicamComputerInterface
from Kuro import KuroCamera
from collections import deque
import json
import atexit

class KuroServer(LabradServer):
    camera_id = PicamCameraID()
    camera_id.model = PicamModel.Kuro1200B.value
    camera_id.computer_interface = PicamComputerInterface.Usb3.value
    camera_id.sensor_name = 'PI 1200 x 1200 CMOS (B)'.encode('utf-8') 
    camera_id.serial_number = 'K23F203001'.encode('utf-8')

    ini_param = {
        "exposure_time": 3.,
        "ROI_x": 260,
        "ROI_y": 30,
        "ROI_width": 512,
        "ROI_height": 60,
    }
    # for the clock servo. stroing recent 100 data with its filenames.
    name = '%LABRADNODE%_kuro'
    records = deque([])
    max_records = 100

    def initServer(self):
        self.kuro = KuroCamera(camera_id=self.camera_id,param=self.ini_param)
        self.kuro.__enter__()
        atexit.register(self._safe_shutdown)
        super(KuroServer, self).initServer()   
    
    def stopServer(self):
        self._safe_shutdown()
        super(KuroServer, self).stopServer()

    def _safe_shutdown(self):
        if hasattr(self, 'kuro') and self.kuro is not None:
            try:
                self.kuro.__exit__(None, None, None)
                self.kuro = None
            except Exception as e:
                print("Exception during hardware shutdown:", e)
    
    @setting(1)
    def Connect(self, c):
        self.kuro.Connect(camera_id=self.camera_id)

    @setting(2)
    def Disconnect(self, c):
        self.kuro.Disconnect()

    @setting(3)
    def Reconnect(self, c):
        self.kuro.Reconnect()
    
    @setting(4, exposure_time="v")
    def SetExposureTime(self, c, exposure_time):
        self.kuro.SetExposureTime(exposure_time)

    @setting(5, returns="v")
    def GetExposureTime(self, c):
        return self.kuro.GetExposureTime()
    
    @setting(6, trigger_response="i")
    def SetTriggerResponse(self, c, trigger_response):
        self.kuro.SetTriggerResponse(trigger_response)

    @setting(7, returns="i")
    def GetTriggerResponse(self, c):
        return self.kuro.GetTriggerResponse()
    
    @setting(8, x="i", y="i", width="i", height="i")
    def SetROI(self, c, x, y, width, height):
        self.kuro.SetROI(x, y, width, height)

    @setting(9, returns="*i")
    def GetROI(self, c):
        _, rois = self.kuro.GetROI()
        return rois[0]
    
    @setting(10, count="i")
    def SetReadoutCount(self, c, count):
        """Set readout count"""
        self.kuro.SetReadoutCount(count)
    
    @setting(11, returns="i")
    def GetReadoutCount(self, c):
        """Get readout count"""
        return self.kuro.GetReadoutCount()
    
    @setting(12, setpoint="v")
    def SetSensorTemperatureSetPoint(self, c, setpoint):
        """Set readout count"""
        self.kuro.SetSensorTemperatureSetPoint(setpoint)
    
    @setting(13, returns="v")
    def GetSensorTemperatureSetPoint(self, c):
        """Get readout count"""
        return self.kuro.GetSensorTemperatureSetPoint()
    
    @setting(14, returns="v")
    def GetSensorTemperatureReading(self, c):
        """Get readout count"""
        return self.kuro.GetSensorTemperatureReading()

    @setting(15, disable="i")
    def SetDisableCoolingFan(self, c, disable):
        """Set sensor temperature set point"""
        self.kuro.SetDisableCoolingFan(disable)
    
    @setting(16)
    def GetParameters(self, c):
        self.kuro.GetParameters()
    
    @setting(17)
    def CommitParameters(self, c):
        self.kuro.CommitParameters()
    
    @setting(18)
    def StartAcquisition(self, c):
        """Start acquisition"""
        self.kuro.StartAcquisition()
    
    @setting(19)
    def StopAcquisition(self, c):
        """Stop acquisition"""
        self.kuro.StopAcquisition()
    
    @setting(20, returns="b")
    def IsAcquisitionRunning(self, c):
        """Check if acquisition is running"""
        return self.kuro.IsAcquisitionRunning()
    
    @setting(21, readout_count="i", timeout="i", returns="i*i")
    def Acquire(self, c, readout_count = 3, timeout = 60000):
        """Acquire data from camera"""
        return self.kuro.Acquire(readout_count, timeout)
    
    @setting(22, timeout="i", returns="i*i")
    def WaitForAcquisitionUpdate(self, c, timeout = 60000):
        """Acquire data from camera"""
        return self.kuro.WaitForAcquisitionUpdate(timeout)
    
    @setting(23, count='i', data='*i', save_path='s')
    def SaveData(self, c, count, data, save_path):
        self.kuro.SaveData(count, data, save_path)

    @setting(24, data="s")
    def update_records(self, c, data):
        """ Update records."""
        data = json.loads(data)
        if len(self.records) > self.max_records:
            self.records.popleft()
        self.records.append(data)

    @setting(25)
    def retrieve_records(self, c):
        """Retrieve all stored records as a single dictionary."""
        result = {}
        for record in self.records:
            if not isinstance(record, dict) or len(record) != 1:
                continue  # skip malformed entries
            key = next(iter(record))
            result[key] = record[key]
        return json.dumps(result)

Server = KuroServer

if __name__ == "__main__":
    from labrad import util
    util.runServer(Server())