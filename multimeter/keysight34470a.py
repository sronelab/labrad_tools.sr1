"""
Provides access to Keysight 34470A multimeters.

..
    ### BEGIN NODE INFO
    [info]
    name = keysight34470a
    version = 1
    description = server for Keysight 34470A multimeter
    instancename = %LABRADNODE%_keysight34470a

    [startup]
    cmdline = %PYTHON% %FILE%
    timeout = 20

    [shutdown]
    message = 987654321
    timeout = 20
    ### END NODE INFO
"""

import sys
from datetime import datetime
from labrad.server import LabradServer, setting
from twisted.internet.reactor import callInThread
import json
import vxi11
import os
from labrad import connect

class keysight34470aServer(LabradServer):
    """Provides access to keysight34470a multimeters."""
    name = '%LABRADNODE%_keysight34470a'
    sesame_street_ip = '192.168.1.118' # on sesame street on yebert.
    recording = False
    data_path = os.path.join(os.getenv('PROJECT_DATA_PATH'), 'data')
    verbose = True
    
    def initServer(self):
        self.inst = vxi11.Instrument(self.sesame_street_ip)
        # set trigger mode
        self.inst.write('*RST')
        self.inst.write('TRIG:SOUR EXT;SLOP POS')
        self.inst.write('CONF:VOLT:DC 10') # important to fix the range to do a fast readout.
        self.inst.timeout = 30
        # self.connect_to_labrad()

    # def connect_to_labrad(self, host=os.getenv("LABRADHOST"),password = os.getenv("LABRADPASSWORD") ):
    #     self.cxn = connect(name=self.name, host=host, password=password)

    def stopServer(self):
        self.inst.close()

    @setting(1, NPLC='s')
    def read_voltage(self, c, NPLC):
        """
        Read voltage from the multimeter with aperture of NPLC. 
        Require external trigger.
        """
        self.inst.write('SENS:VOLT:DC:NPLC {}'.format(NPLC))
        try:
            self.inst.write('INIT')
            data = self.inst.ask("FETC?")
        except:
            data = "0.0"

        return data
    
    def _read_voltage(self, NPLC):
        """private one"""
        self.inst.write('SENS:VOLT:DC:NPLC {}'.format(NPLC))
        try:
            self.inst.write('INIT')
            data = float(self.inst.ask("FETC?"))
        except:
            data = "NODATA"

        return data
    
    @setting(10, rel_data_path='s')
    def record(self, c, rel_data_path):
        self.recording_name = rel_data_path
        if self.recording:
            raise Exception('already recording')
        callInThread(self.do_record_data, rel_data_path)

    def do_record_data(self, rel_data_path):
        self.recording = True
        data = self._read_voltage(self._get_NPLC())
        self.recording = False
        processed_data = {"voltage":data}

        abs_data_dir = os.path.join(self.data_path, os.path.dirname(rel_data_path))
        if not os.path.isdir(abs_data_dir):
            os.makedirs(abs_data_dir)
    
        abs_data_path = os.path.join(self.data_path, rel_data_path)         
        if self.verbose:
            print("saving processed data to {}".format(abs_data_path))

        json_path = abs_data_path + '.json'
        with open(json_path, 'w') as outfile:
            json.dump(processed_data, outfile, default=lambda x: x.tolist())
        # print(json_path)
            
    def _get_NPLC(self):
        # # compute NPLC based on T_rabi. Take 0.7 of T_rabi considering possible delays. Can be changed later.
        # Trabi = float(json.loads(self.cxn.conductor.get_parameter_values(json.dumps({'sequencer.T_rabi':None})))["sequencer.T_rabi"])
        # NPLC = str(Trabi  * 60.0 * 0.7)
        NPLC = str(10)
        return NPLC

if __name__ == '__main__':
    from labrad import util
    util.runServer(keysight34470aServer())