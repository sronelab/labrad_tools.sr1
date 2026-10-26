import os

from pmt.clients.pmt_client import PMTViewer


class MyViewer(PMTViewer):
    pmt_name = 'blue_pmt'
    data_dir = os.path.join(os.getenv('PROJECT_DATA_PATH'), 'data')

if __name__ == '__main__':
    from PyQt6 import QtWidgets
    a = QtWidgets.QApplication([])
    import asyncio
    import qasync
    from twisted.internet import asyncioreactor
    loop = qasync.QEventLoop(a)
    asyncio.set_event_loop(loop)
    asyncioreactor.install(loop)
    from twisted.internet import reactor
    widget = MyViewer(reactor)
    widget.show()
    with loop:
        reactor.run()
