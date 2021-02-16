import ok
import struct
import time
import numpy as np

bitfilepath = "/mnt/srdata/ross/tmp/ad669_sequencer.bit"

devices = ok.okCFrontPanelDevices()
xem = devices.Open()
err = xem.ConfigureFPGA(bitfilepath)
if err:
    raise Exception(err)

def ticks_to_bytes(ticks):
    lsb = list(struct.unpack('4B', struct.pack('<I', int(ticks))))
    return lsb[2:] + lsb[:2]

def bits_to_bytes(bits):
    return struct.unpack('BB', struct.pack('h', bits))

def shift_times(byte_list):
    for i in range(0, len(byte_list) - 3, 4):
        byte_list[i+0], byte_list[i+1], byte_list[i+2], byte_list[i+3] = byte_list[i+2], byte_list[i+3], byte_list[i+0], byte_list[i+1]
    return byte_list

def shift_outs(byte_list):
    for i in range(0, len(byte_list) - 3, 4):
        byte_list[i+0], byte_list[i+1], byte_list[i+2], byte_list[i+3] = byte_list[i+2], byte_list[i+3], byte_list[i+0], byte_list[i+1]
    return byte_list

delta = 0b11111000111010
times = ticks_to_bytes(111.111e6) * 2**10
outs = (bits_to_bytes(2**15 - 1) + bits_to_bytes(delta - 1) + bits_to_bytes(2**15 - 1) + bits_to_bytes(-delta)) * 2**9
outs2 = (bits_to_bytes(2**15 - 1) + bits_to_bytes(-delta) + bits_to_bytes(2**15 - 1) + bits_to_bytes(delta - 1)) * 2**9
#outs2 = shift_outs(outs2)

print([bin(x) for x in bits_to_bytes(2**7 - 1)])
print([bin(x) for x in bits_to_bytes(-2**7)])

t0 = time.time()
xem.WriteToPipeIn(0x80, bytearray(times))
xem.WriteToPipeIn(0x81, bytearray(outs))
xem.WriteToPipeIn(0x82, bytearray(outs2))
xem.WriteToPipeIn(0x83, bytearray(outs))
xem.WriteToPipeIn(0x84, bytearray(outs2))
xem.WriteToPipeIn(0x85, bytearray(outs))
xem.WriteToPipeIn(0x86, bytearray(outs2))
xem.WriteToPipeIn(0x87, bytearray(outs))
xem.WriteToPipeIn(0x88, bytearray(outs2))
print(time.time() - t0)


#print(3)
#for i in range(3)[::-1]:
#    time.sleep(1)
#    print(i)
xem.SetWireInValue(0x00, 0b001)
xem.SetWireInValue(0x01, 2**15 - 1 + 2**14)
xem.SetWireInValue(0x02, 2**15 - 1 )
xem.UpdateWireIns()
#time.sleep(3)

#xem.SetWireInValue(0x01, 2**14 - 1)
#xem.SetWireInValue(0x00, 0b11)
#xem.UpdateWireIns()
#
#time.sleep(3)
#xem.SetWireInValue(0x00, 0b1)
#xem.UpdateWireIns()
