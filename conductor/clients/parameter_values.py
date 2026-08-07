import json
import numpy as np

from PyQt6 import QtWidgets
from twisted.internet.defer import inlineCallbacks

from client_tools.connection import connection
from client_tools.widgets import NeatSpinBox

class ParameterRow(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__()
        self.boxWidth = parent.boxWidth
        self.boxHeight = parent.boxHeight
        self.boxName = parent.boxName
        self.populateGUI()

    def loadControlConfiguration(self, configuration):
        for key, value in configuration.__dict__.items():
            print(value)
            setattr(self, key, value)

    def populateGUI(self):
        self.nameBox = QtWidgets.QLineEdit()
        self.nameBox.setFixedSize(self.boxWidth, self.boxHeight)
        if self.boxName:
            self.nameBox.setText(self.boxName)
        self.valueBox = NeatSpinBox()
        self.valueBox.setFixedSize(self.boxWidth, self.boxHeight)

        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addWidget(self.nameBox)
        self.layout.addWidget(self.valueBox)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

class ParameterValuesClient(QtWidgets.QGroupBox):
    hasNewValue = False
    free = True

    def __init__(self, reactor, cxn=None):
        super().__init__()
        self.reactor = reactor
        self.cxn = cxn
        self.connect_to_labrad()

    @inlineCallbacks
    def connect_to_labrad(self):
        if self.cxn is None:
            self.cxn = connection()
            cname = '{} - client'.format(self.servername)
            yield self.cxn.connect(name=cname)
        self.context = yield self.cxn.context()
        try:
            self.populateGUI()
            yield self.connectSignals()
        except Exception as e:
            print(e)
            self.setDisabled(True)

    def populateGUI(self):
        names = ['sequencer.Z_zero_top','sequencer.Z_zero_btm', 'sequencer.Y_zero', 'sequencer.X_zero', 'sequencer.Z_mot_top', 'sequencer.Z_mot_btm', 'sequencer.Y_mot', 'sequencer.X_mot', 'sequencer.X_pol', 'sequencer.X_bias', '',
                        'sequencer.T_blue', 'sequencer.T_rabi', 'sequencer.Int813', 'sequencer.Int813_clock', 'sequencer.IntClock', 'sequencer.IntClock_top_mF', 'sequencer.IntClock_btm_mF', '',
                        'f_9_7', 'f_7_5', 'f_5_3', 'f_5_3_ss', '',
                        'sequencer.fm_11_doppler', 'sequencer.fm_11_doppler_p']
        names += ['']*(self.numRows-len(names)) 
        
        self.parameterRows = []
        for i in range(self.numRows):
            self.boxName = names[i] if names[i] else None
            self.parameterRows.append(ParameterRow(self))

        self.layout = QtWidgets.QVBoxLayout()
        for pr in self.parameterRows:
            self.layout.addWidget(pr)
        self.layout.setSpacing(1)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.setFixedSize(2*(self.boxWidth+2), self.numRows*(self.boxHeight+2))
        self.setLayout(self.layout)

    @inlineCallbacks
    def connectSignals(self):
        server = yield self.cxn.get_server(self.servername)
        yield server.signal__update(self.update_id)
        yield server.addListener(listener=self.receive_update, source=None,
                                 ID=self.update_id)
        yield self.cxn.add_on_connect(self.servername, self.reinit)
        yield self.cxn.add_on_disconnect(self.servername, self.disable)

        for pr in self.parameterRows:
            pr.nameBox.returnPressed.connect(self.get_parameter_value(pr))
            pr.valueBox.returnPressed.connect(self.set_parameter_value(pr))
    
    def receive_update(self, c, signal_json):
        signal = json.loads(signal_json)
        for message_type, message in signal.items():
            if message_type in ['get_parameter_values', 'set_parameter_values']:
                for pr in self.parameterRows:
                    parameterName = str(pr.nameBox.text())
                    if parameterName and (parameterName in message):
                        pr.valueBox.display(message[parameterName])

    def set_parameter_value(self, parameterRow):
        @inlineCallbacks
        def spv():
            name = str(parameterRow.nameBox.text())
            value = float(parameterRow.valueBox.value())
            server = yield self.cxn.get_server(self.servername)
            request = {name: value}
            yield server.set_parameter_values(json.dumps(request))
        return spv
    
    def get_parameter_value(self, parameterRow):
        @inlineCallbacks
        def gpv():
            name = str(parameterRow.nameBox.text())
            server = yield self.cxn.get_server(self.servername)
            request = {name: None}
            yield server.get_parameter_values(json.dumps(request))
        return gpv

    @inlineCallbacks
    def set_parameter_values(self):
        server = yield self.cxn.get_server(self.servername)
        request = {str(pr.nameBox.text()): float(pr.valueBox.value()) for pr in self.parameterRows 
                   if str(pr.nameBox.text())}
        yield server.set_parameter_values(json.dumps(request))
    
    @inlineCallbacks
    def get_parameter_values(self):
        server = yield self.cxn.get_server(self.servername)
        request = {str(pr.nameBox.text()): None for pr in self.parameterRows 
                   if str(pr.nameBox.text())}
        yield server.get_parameter_values(json.dumps(request))

    @inlineCallbacks	
    def reinit(self): 
        self.setDisabled(False)
        server = yield self.cxn.get_server(self.servername)
        yield server.signal__update(self.update_id, context=self.context)
        yield server.addListener(listener=self.receive_update, source=None,
                                 ID=self.update_id, context=self.context)

    def disable(self):
        self.setDisabled(True)

    def closeEvent(self, event):
        if self.cxn is not None:
            def cleanup(server):
                server.removeListener(listener=self.receive_update, ID=self.update_id)

            try:
                d_seq = self.cxn.get_server(self.servername)
                d_seq.addCallback(cleanup)
                d_seq.addErrback(lambda f: print("Cleanup skipped (already disconnected)."))
            except Exception as e:
                print(f"Error during shutdown cleanup: {e}")

        if self.reactor.running:
            self.reactor.stop()

        event.accept()