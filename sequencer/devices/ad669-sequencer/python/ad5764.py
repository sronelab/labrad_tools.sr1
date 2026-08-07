import numpy as np
import ok
import struct
import time

bitfilepath = "/home/rbh/proj/ad5764-sequencer/vivado/ad5764-sequencer.runs/impl_1/ad5764_sequencer.bit"

def voltage_to_bits(voltage):
    bits = int((voltage + 10) / 20 * 2**16)
    return bits

class AD5764SequencerError(Exception):
    pass

class AD5764Sequencer(object):
    _clkfreq = 100e6
    _fifodepth = 2**12

    def __init__(self, bitfilepath, serialno=None):
        devices = ok.okCFrontPanelDevices()
        self._xem = devices.Open()
        self._xem.ConfigureFPGA(bitfilepath)

    def enable_manual(self, channel, enable):
        ep = 0
        bit = channel + 1
        self._xem.SetWireInValue(ep, enable, 1 << bit)

    def set_manual_state(self, channel, voltage):


