"""
### BEGIN NODE INFO
[info]
name = rigol
version = 1.2
description = Rigol oscilloscope server (multi-scope)
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

from twisted.internet.threads import deferToThread
from twisted.internet.defer import inlineCallbacks, returnValue, gatherResults

from rigol_new import RigolOscilloscope
from scope_configs import scope1_config, scope2_config


class RigolServer(LabradServer):

    name = "%LABRADNODE%_rigol"

    def initServer(self):

        print("Initializing Rigol Server...")

        # Create both scopes
        self.scope1 = RigolOscilloscope(scope1_config)
        self.scope2 = RigolOscilloscope(scope2_config)

        super(RigolServer, self).initServer()

    @setting(1, "Acquire Data", returns="s")
    @inlineCallbacks
    def acquire_data(self, c):
        d1 = deferToThread(self.scope1.acquire_and_process)
        d2 = deferToThread(self.scope2.acquire_and_process)
        results_list = yield gatherResults([d1, d2])

        results = {
            "scope1": results_list[0],
            "scope2": results_list[1],
        }
        
        returnValue(json.dumps(results))

    def stopServer(self):

        print("Closing Rigol scopes...")

        try:
            self.scope1.close()
        except Exception:
            pass

        try:
            self.scope2.close()
        except Exception:
            pass

        super(RigolServer, self).stopServer()


if __name__ == "__main__":

    from labrad.util import runServer

    runServer(RigolServer())