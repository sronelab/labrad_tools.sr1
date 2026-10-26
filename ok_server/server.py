"""
### BEGIN NODE INFO
[info]
name = ok
version = 1.0
description = 
instancename = %LABRADNODE%_ok

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

import json
import os
import threading
import time

from labrad.server import setting

import ok

from hardware_interface_server.server import HardwareInterfaceServer
from hardware_interface_server.exceptions import InterfaceAlreadyOpen
from hardware_interface_server.exceptions import InterfaceNotAvailable
from ok_server.exceptions import BitfileNotFound

class OKServer(HardwareInterfaceServer):
    name = '%LABRADNODE%_ok'
    bitfile_directory = os.path.join(os.getenv('PROJECT_LABRAD_TOOLS_PATH'), 'ok_server', 'bit')
    # FrontPanel calls on a device are not safe to interleave across the server's request threads
    lock = threading.RLock()
    
    def _get_available_interfaces(self):
        open = self._get_open_interfaces()
        available_but_not_open = []
        
        devices = ok.FrontPanelDevices()
        device_count = devices.GetCount()
        for i in range(device_count):
            serial_number = devices.GetSerial(i)
            available_but_not_open.append(serial_number)
        
        return open + available_but_not_open

    def _get_open_interfaces(self):
        with self.lock:
            for interface_id, interface in list(self.interfaces.items()):
                try: 
                    is_open = interface.IsOpen()
                    if not is_open:
                        del self.interfaces[interface_id]
                except:
                    del self.interfaces[interface_id]

            return list(self.interfaces.keys())
        
    def _open_interface(self, interface_id):
        with self.lock:
            open = self._get_open_interfaces()
            if interface_id in open:
                raise InterfaceAlreadyOpen(interface_id)

            fp = ok.FrontPanelDevices().Open(interface_id)
            if not fp:
                raise InterfaceNotAvailable(interface_id)
            fp.LoadDefaultPLLConfiguration()
            self.interfaces[interface_id] = fp

    def _close_interface(self, interface_id):
        with self.lock:
            # don't go through _get_interface: it would open a closed device just to close it
            interface = self.interfaces.pop(interface_id, None)
            if interface is not None:
                interface.Close()

    def _get_data_port(self, interface_id):
        # fetched per call: the port is owned by the device, which reopen_interface replaces
        return self._get_interface(interface_id).GetFPGADataPortClassic()

    @setting(10)
    def configure_fpga(self, c, interface_id, file_name):
        file_path = os.path.join(self.bitfile_directory, file_name)
        if not os.path.isfile(file_path):
            raise BitfileNotFound(file_name)
        with self.lock:
            interface = self._get_interface(interface_id)
            interface.ConfigureFPGA(file_path)
    
    @setting(11)
    def get_wire_out_value(self, c, interface_id, wire_address):
        with self.lock:
            data_port = self._get_data_port(interface_id)
            wire_out_value = data_port.GetWireOutValue(wire_address)
        return wire_out_value
    
    @setting(12)
    def is_triggered(self, c, interface_id, address, mask=0xffffffff):
        with self.lock:
            data_port = self._get_data_port(interface_id)
            is_triggered = data_port.IsTriggered(address, mask)
        return bool(is_triggered)
    
    @setting(13)
    def set_wire_in_value(self, c, interface_id, wire_address, value, mask=0xffffffff):
        with self.lock:
            data_port = self._get_data_port(interface_id)
            data_port.SetWireInValue(wire_address, value, mask)
    
    @setting(14)
    def update_trigger_outs(self, c, interface_id):
        with self.lock:
            data_port = self._get_data_port(interface_id)
            data_port.UpdateTriggerOuts()
    
    @setting(15)
    def update_wire_ins(self, c, interface_id):
        with self.lock:
            data_port = self._get_data_port(interface_id)
            data_port.UpdateWireIns()
    
    @setting(16)
    def update_wire_outs(self, c, interface_id):
        with self.lock:
            data_port = self._get_data_port(interface_id)
            data_port.UpdateWireOuts()
    
    @setting(17, interface_id='s', pipe_address='i', byte_array='*y')
    def write_to_pipe_in(self, c, interface_id, pipe_address, byte_array):
        # py3 pylabrad delivers '*y' as a list of bytes objects, one per byte
        data = bytearray(b''.join(byte_array))
        with self.lock:
            data_port = self._get_data_port(interface_id)
            data_port.WriteToPipeIn(pipe_address, data)

    def _check_trigger(self, interface_id, address, mask):
        # update + read as one step so another thread's UpdateTriggerOuts can't swallow the trigger
        with self.lock:
            data_port = self._get_data_port(interface_id)
            data_port.UpdateTriggerOuts()
            return data_port.IsTriggered(address, mask)

    @setting(101)
    def wait_trigger(self, c, interface_id, address, mask=0xffffffff):
        self._check_trigger(interface_id, address, mask)
        while True:
            # lock is released between polls so other settings keep running
            if self._check_trigger(interface_id, address, mask):
                return
            time.sleep(0.005)

Server = OKServer

if __name__ == "__main__":
    from labrad import util
    util.runServer(Server())
