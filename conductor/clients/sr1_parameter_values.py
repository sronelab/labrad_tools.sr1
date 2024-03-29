import json
import numpy as np

from PyQt4 import QtGui, QtCore, Qt
from PyQt4.QtCore import pyqtSignal
from twisted.internet.defer import inlineCallbacks

from conductor.clients.parameter_values import ParameterValuesClient

class MyClient(ParameterValuesClient):
    servername = 'conductor'
    update_id = 461028
    updateTime = 100 # [ms]
    boxWidth = 200
    boxHeight = 25
    numRows = 30

if __name__ == '__main__':
    a = QtGui.QApplication([])
    a.setWindowIcon(QtGui.QIcon('icon_parameter.png'))
    from client_tools import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    widget = MyClient(reactor)
    widget.show()
    reactor.run()
