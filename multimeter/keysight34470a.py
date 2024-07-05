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
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.task import LoopingCall

import vxi11

class keysight34470aServer(LabradServer):
    """Provides access to keysight34470a multimeters."""
    name = '%LABRADNODE%_keysight34470a'

    sesame_street_ip = '192.168.1.118'
    
    def initServer(self):
        self.inst = vxi11.Instrument(self.sesame_street_ip)
        # set trigger mode
        self.inst.write('TRIG:SOUR EXT;SLOP POS')
        self.inst.timeout = 30

    def stopServer(self):
        self.inst.close()

    @setting(1, NPLC='i')
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
            data = "NODATA"

        return data

if __name__ == '__main__':
    from labrad import util
    util.runServer(keysight34470aServer())