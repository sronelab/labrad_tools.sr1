import json

class KuroProxy(object):
    def __init__(self, kuro_server):
        self.kuro_server = kuro_server
    
    def Connect(self):
        self.kuro_server.Connect()

    def Disconnect(self):
        self.kuro_server.Disconnect()

    def Reconnect(self):
        self.kuro_server.Reconnect()
    
    def SetExposureTime(self, exposure_time):
        self.kuro_server.SetExposureTime(exposure_time)

    def GetExposureTime(self):
        return self.kuro_server.GetExposureTime()
    
    def SetTriggerResponse(self, trigger_response):
        self.kuro_server.SetTriggerResponse(trigger_response)

    def GetTriggerResponse(self):
        return self.kuro_server.GetTriggerResponse()
    
    def SetROI(self, x, y, width, height):
        self.kuro_server.SetROI(x, y, width, height)

    def GetROI(self):
        return self.kuro_server.GetROI()
    
    def SetReadoutCount(self, count):
        """Set readout count"""
        self.kuro_server.SetReadoutCount(count)
    
    def GetReadoutCount(self):
        """Get readout count"""
        return self.kuro_server.GetReadoutCount()
    
    def SetSensorTemperatureSetPoint(self, setpoint):
        """Set readout count"""
        self.kuro_server.SetSensorTemperatureSetPoint(setpoint)
    
    def GetSensorTemperatureSetPoint(self):
        """Get readout count"""
        return self.kuro_server.GetSensorTemperatureSetPoint()
    
    def GetSensorTemperatureReading(self):
        """Get readout count"""
        return self.kuro_server.GetSensorTemperatureReading()

    def SetDisableCoolingFan(self, disable):
        """Set sensor temperature set point"""
        self.kuro_server.SetDisableCoolingFan(disable)
    
    def GetParameters(self):
        self.kuro_server.GetParameters()
    
    def CommitParameters(self):
        self.kuro_server.CommitParameters()
    
    def StartAcquisition(self):
        """Start acquisition"""
        self.kuro_server.StartAcquisition()
    
    def StopAcquisition(self):
        """Stop acquisition"""
        self.kuro_server.StopAcquisition()
    
    def IsAcquisitionRunning(self):
        """Check if acquisition is running"""
        return self.kuro_server.IsAcquisitionRunning()
    
    def Acquire(self, readout_count = 3, timeout = 60000):
        """Acquire data from camera"""
        return self.kuro_server.Acquire(readout_count, timeout)
    
    def WaitForAcquisitionUpdate(self, timeout = 60000):
        """Acquire data from camera"""
        return self.kuro_server.WaitForAcquisitionUpdate(timeout)
    
    def SaveData(self, count, data, save_path):
        self.kuro_server.SaveData(count, data, save_path)

    def update_records(self, point_filename, frac, tot):
        """ Send data to server"""
        data = {point_filename:{"frac":frac, "tot":tot}}
        self.kuro_server.update_records(json.dumps(data))