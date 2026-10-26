import json
import struct

from device_server.device import DefaultDevice

from sequencer.devices.yesr_sequencer_board.device import YeSrSequencerBoard
from sequencer.devices.yesr_analog_board.ramps import RampMaker
from sequencer.devices.yesr_analog_board.helpers import seconds_to_ticks
from sequencer.devices.yesr_analog_board.helpers import volts_to_bits
from sequencer.devices.yesr_analog_board.helpers import get_ramp_bytes

# max timestep for digital sequencer
# (2**32 - 2**8) / (50 MHz)
T_TRIGGER = 85.8993408 # [s]

class YeSrAnalogBoard(YeSrSequencerBoard):
    sequencer_type = 'analog'
    ok_bitfilename = 'ad669_sequencer.bit'
    clk = 100e6
    
    def update_channel_modes(self):
        cm_list = [c.mode for c in self.channels]
        value = sum([2**(j+1) for j, m in enumerate(cm_list) if m == 'manual'])
        value = 0b0000000000000000 | value
        self.fp.SetWireInValue(0x00, value, 0b111111110)
        self.fp.UpdateWireIns()
    
    def update_channel_manual_outputs(self): 
        for i, c in enumerate(self.channels):
            v = volts_to_bits(c.manual_output - min(c.dac_voltage_range), c.dac_voltage_range, c.dac_bits)
            self.fp.SetWireInValue(i + 1, v)
        self.fp.UpdateWireIns()
    
    def default_sequence_segment(self, channel, dt):
        return {'dt': dt, 'type': 's', 'vf': channel.manual_output}

    def make_sequence_bytes(self, sequence):
        for channel in self.channels:
            sequence[channel.key] = [s for s in sequence[channel.key] if s['dt'] < T_TRIGGER]
            channel_sequence = sequence[channel.key]
            channel.set_sequence(channel_sequence)

        t_bytes = []
        v_bytes = [[] for _ in range(8)]
        
        for i, channel in enumerate(self.channels):
            for ramp in channel.programmable_sequence:
                if channel == self.channels[0]:
                    dt_ticks = seconds_to_ticks(ramp['dt'], self.clk)
                    t_bytes += ticks_to_bytes(dt_ticks)
                vi_bits = volts_to_bits(ramp['vi'], channel.dac_voltage_range, channel.dac_bits)
                vf_bits = volts_to_bits(ramp['vf'], channel.dac_voltage_range, channel.dac_bits)
                dv_bits = vf_bits - vi_bits
                v_bytes[i] += bits_to_bytes(vi_bits) + bits_to_bytes(dv_bits)

        t_bytes = t_bytes + [0, 0, 0, 0] * (2**12 - len(t_bytes))
        v_bytes = [cv_bytes + cv_bytes[-4:] * (2**12 - len(cv_bytes)) for cv_bytes in v_bytes]

        return t_bytes, v_bytes

    def set_raw_sequence(self, raw_sequence):
        self.raw_sequence = raw_sequence
        parameter_names = self.get_sequence_parameter_names(raw_sequence)
        parameter_values = self.get_sequence_parameter_values(parameter_names)
        programmable_sequence = self.substitute_sequence_parameters(raw_sequence, parameter_values)
        t_bytes, v_bytes = self.make_sequence_bytes(programmable_sequence)

        self.fp.SetWireInValue(0, 0, 1)
        self.fp.UpdateWireIns()
        self.fp.WriteToPipeIn(0x80, [bytes([x]) for x in t_bytes])
        for i, cv_bytes in enumerate(v_bytes):
            self.fp.WriteToPipeIn(0x81 + i, [bytes([x]) for x in cv_bytes])
        self.fp.SetWireInValue(0, 1, 1)
        self.fp.UpdateWireIns()

def ticks_to_bytes(ticks):
    lsb = list(struct.unpack('4B', struct.pack('<I', int(ticks))))
    return lsb[2:] + lsb[:2]

def bits_to_bytes(bits):
    return struct.unpack('BB', struct.pack('h', bits))
