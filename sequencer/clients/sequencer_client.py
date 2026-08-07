from sequencer_control import SequencerClient
import os

class TestClient(SequencerClient):
    conductor_servername = 'conductor'
    sequencer_servername = 'sequencer'
    sequence_directory = os.path.join(os.getenv('PROJECT_DATA_PATH', ''), 'sequences/{}/')
    master_channel = 'Trigger@D15'
    timing_channel = 'Trigger@D15'
    qt_style = 'Fusion' # Gtk+
    
if __name__ == '__main__':
    import sys
    import asyncio
    import qasync
    from twisted.internet import asyncioreactor
    from PyQt6 import QtWidgets
    
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle(QtWidgets.QStyleFactory.create('Fusion'))

    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    asyncioreactor.install(loop)
    from twisted.internet import reactor
    
    widget = TestClient(reactor)
    widget.show()
    
    with loop:
        reactor.run()