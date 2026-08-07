"""
Provides access to LabJack T7 DAQ.
"""

r"""
    ### BEGIN NODE INFO
    [info]
    name = LabJack_Server
    version = 1
    description = server for LabJack T8 DAQ
    instancename = %LABRADNODE%_labjack 

    [startup]
    cmdline = %PYTHON% %FILE%
    timeout = 20

    [shutdown]
    message = 987654321
    timeout = 20
    ### END NODE INFO
"""



from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.reactor import callInThread

from labrad.server import LabradServer, setting
from labrad.util import getNodeName
from labrad import connect

import sys
import os
import json
from datetime import datetime

# # test imports
# print(sys.executable)
# print(sys.path)

from labjack import ljm


class LabJackServer(LabradServer):
    """Provides access to LabJack T8 DAQ."""
    name = '%LABRADNODE%_labjack'
    sesame_street_ip = '192.168.1.133'
    data_path = os.path.join(os.getenv('PROJECT_DATA_PATH'), 'data')
    verbose = True

    def __init__(self):
        self.name = "{}_labjack".format(getNodeName())
        super(LabJackServer, self).__init__()

        self.handle = ljm.openS("T8", "ETHERNET", self.sesame_street_ip)

        info = ljm.getHandleInfo(self.handle)
        print("Opened a LabJack with Device type: %i, Connection type: %i,\n"
        "Serial number: %i, IP address: %s, Port: %i,\nMax bytes per MB: %i" %
        (info[0], info[1], info[2], ljm.numberToIP(info[3]), info[4], info[5]))

    def stopServer(self):
        """
        Run when the LabRAD server is stopped. Closes the connection to the LabJack.
        """
        ljm.close(self.handle)


    # @inlineCallbacks
    @setting(1, names='*s', returns='*v')
    def read_names(self, c, names):
        """
        Read values from multiple named registers on the LabJack.
        """
        values = ljm.eReadNames(self.handle, len(names), names)
        # print(values)
        return values

 
        

if __name__ == "__main__":
    from labrad import util
    util.runServer(LabJackServer())