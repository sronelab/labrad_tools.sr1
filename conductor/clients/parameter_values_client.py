import sys
import asyncio

from PyQt6 import QtWidgets
import qasync
from twisted.internet import asyncioreactor

from parameter_values import ParameterValuesClient

class MyClient(ParameterValuesClient):
    servername = 'conductor'
    update_id = 461028
    updateTime = 100 # [ms]
    boxWidth = 200
    boxHeight = 25
    numRows = 30

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    asyncioreactor.install(loop)
    from twisted.internet import reactor
    
    widget = MyClient(reactor)
    widget.show()
    
    with loop:
        reactor.run()