from sequencer.clients.sequencer_control import SequencerClient

class TestClient(SequencerClient):
    conductor_servername = 'conductor'
    sequencer_servername = 'sequencer'
#    sequence_directory = '/home/yertle/sequences/{}/'
    sequence_directory = '/home/yertle/srqdata/sequences/{}/'
    master_channel = 'Trigger@D15'
    timing_channel = 'Trigger@D15'

    qt_style = 'Gtk+'
    
if __name__ == '__main__':
    from PyQt4 import QtGui
    app = QtGui.QApplication([])
    import client_tools.qt4reactor as qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    widget = TestClient(reactor)
    app.setStyle(QtGui.QStyleFactory.create(widget.qt_style))
    widget.show()
    reactor.run()
