"""
### BEGIN NODE INFO
[info]
name = mako
version = 1.0
description = 
instancename = %LABRADNODE%_mako

[startup]
cmdline = C:/Users/srgang/venvs/python3_labrad/Scripts/python3.exe %FILE%
timeout = 60

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""

from PyQt6.QtWidgets import QApplication
import atexit, sys
import qasync
import asyncio

app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

if sys.platform == 'win32':
    loop = qasync.QSelectorEventLoop(app)
else:
    loop = qasync.QEventLoop(app)
    
asyncio.set_event_loop(loop)
from twisted.internet import asyncioreactor
asyncioreactor.install(loop)

from labrad.server import LabradServer, setting
from labrad.util import runServer
from twisted.internet.threads import deferToThread
from mako import MakoLattice

class MakoServer(LabradServer):
    # for the clock servo. stroing recent 100 data with its filenames.
    name = '%LABRADNODE%_mako'

    def __init__(self, mako_lattice, **kwargs):
        self.lattice = mako_lattice 
        self.camera_near = mako_lattice.camera_near
        self.camera_far = mako_lattice.camera_far
        super(MakoServer, self).__init__(**kwargs)

    def initServer(self):
        atexit.register(self._safe_shutdown)
        super(MakoServer, self).initServer() 
    
    def stopServer(self):
        self._safe_shutdown()
        super(MakoServer, self).stopServer()

    def _safe_shutdown(self):
        if hasattr(self, 'camera_near') and self.camera_near is not None:
            try:
                self.camera_near.stop_camera()
            except Exception as e:
                print("Exception during camera_near shutdown:", e)
        if hasattr(self, 'camera_far') and self.camera_far is not None:
            try:
                self.camera_far.stop_camera()
            except Exception as e:
                print("Exception during camera_far shutdown:", e)
    
    @setting(1, returns="(*v, *v)") 
    def AcquireNear(self, c):
        return deferToThread(self.lattice.Acquire, self.lattice.camera_near)
        
    @setting(2, returns="(*v, *v)") 
    def AcquireFar(self, c):
        return deferToThread(self.lattice.Acquire, self.lattice.camera_far)


if __name__ == "__main__":    
    mako_lattice = MakoLattice()
    server = MakoServer(mako_lattice)

    with loop:
        runServer(server)