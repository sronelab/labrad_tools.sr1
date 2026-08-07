"""
### BEGIN NODE INFO
[info]
name = rigol
version = 1.1
description = 
instancename = %LABRADNODE%_rigol

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 947659321
timeout = 20
### END NODE INFO
"""

import json
from labrad.server import LabradServer
from labrad.server import setting
from rigol import RigolOscilloscope
from twisted.internet.threads import deferToThread

class RigolServer(LabradServer):
    name = "%LABRADNODE%_rigol"

    def initServer(self):
        self.scope = RigolOscilloscope()
        super(RigolServer, self).initServer()

    @setting(1, "Acquire Data", returns="s")
    def acquire_data(self, c):
        def task():
            data = self.scope.acquire_and_process()
            return json.dumps(data)
        return deferToThread(task)

    def stopServer(self):
        self.scope.close()
        super(RigolServer, self).stopServer()

if __name__ == "__main__":
    from labrad.util import runServer
    runServer(RigolServer())