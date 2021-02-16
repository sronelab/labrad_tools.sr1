import ok
import struct
import time

bitfilepath = "/home/rbh/proj/ad5765-sequencer/vivado/ad5764-sequencer.runs/impl_1/ad5764_sequencer.bit"

devices = ok.okCFrontPanelDevices()
xem = devices.Open()
err = xem.ConfigureFPGA(bitfilepath)
print(err)

p = 2**14 - 1
q = 2**30 - 1

q0, q1 = struct.unpack('HH', struct.pack('I', q))

xem.SetWireInValue(1, q0)
xem.SetWireInValue(2, q1)
xem.SetWireInValue(3, p)
xem.UpdateWireIns()

for i in range(8):
    print(i)
    time.sleep(1.34)
