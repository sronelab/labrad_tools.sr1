import ok
import struct
import time
import numpy as np

bitfilepath = "C:\\Users\\Ye Lab\\Desktop\\digital-sequencer\\vivado\\digital-sequencer.runs\\impl_1\\digital_sequencer.bit"

class DigitalSequencerError(Exception):
    pass

class DigitalSequencer(object):
    _clkfreq = 100e6
    _fifodepth = 2**12

    def __init__(self, bitfilepath, serialno=None):
        devices = ok.okCFrontPanelDevices()
        self._xem = devices.Open()
        self._xem.ConfigureFPGA(bitfilepath)

    def enable_manual(self, channel, enable):
        ep = channel >> 4
        bit = channel % 16
        self._xem.SetWireInValue(ep, manual, 1 << bit)

    def set_manual_state(self, channel, state):
        ep = (channel >> 4) + 4
        bit = channel % 16
        self._xem.SetWireInValue(ep, state, 1 << bit)

    def program_sequence(self, times, outs):
        if len(times) != self._fifodepth:
            raise DigitalSequencerError(f'Invalid sequence length: {len(times)}')
        if len(outs) != self._fifodepth:
            raise DigitalSequencerError(f'Invalid sequence length: {len(outs)}')

        self._xem.SetWireInValue(0x00, 0b0)
        self._xem.UpdateWireIns()

        t_bytes = bytearray(sum([ticks_to_bytes(int(dt * self._clkfreq)) for dt in times], []))
        o_bytes = bytearray(sum([outs_to_bytes(o) for o in outs], []))
        self._xem.WriteToPipeIn(0x80, t_bytes)
        self._xem.WriteToPipeIn(0x81, o_bytes)

        self._xem.SetWireInValue(0x00, 0b1)
        self._xem.UpdateWireIns()
    
    def wait_out_empty(self, sampling_interval=0.01):
        ti = time.time()
        self._xem.UpdateTriggerOuts()
        triggered = False
        while not triggered:
            self._xem.UpdateTriggerOuts()
            triggered = self._xem.IsTriggered(0x60, 0b1)
            time.sleep(sampling_interval)
        return time.time() - ti
    
    def wait_in_empty(self, sampling_interval=0.01):
        ti = time.time()
        self._xem.UpdateTriggerOuts()
        triggered = False
        while not triggered:
            self._xem.UpdateTriggerOuts()
            triggered = self._xem.IsTriggered(0x60, 0b10)
            time.sleep(sampling_interval)
        return time.time() - ti
        
        

def ticks_to_bytes(ticks):
    tmp = list(struct.unpack('4B', struct.pack('>I', ticks)))
    tmp[0::2], tmp[1::2] = tmp[1::2], tmp[0::2]
    return tmp

def outs_to_bytes(outs):
    tmp = list(struct.unpack('8B', struct.pack('>Q', outs)))
    tmp[0::2], tmp[1::2] = tmp[1::2], tmp[0::2]
    return tmp

times = [.001] * 2**12
outs = ([1] + [0]) * 2**11

seq = DigitalSequencer(bitfilepath)
seq.program_sequence(times, outs)
seq.program_sequence(times, outs)
#duration = seq.wait_in_empty()
duration = seq.wait_out_empty()
print('done!', duration)
