import sequencer.devices.yesr_analog_board.device
reload(sequencer.devices.yesr_analog_board.device)
import sequencer.devices.yesr_analog_board.channel
reload(sequencer.devices.yesr_analog_board.channel)
from sequencer.devices.yesr_analog_board.device import YeSrAnalogBoard
from sequencer.devices.yesr_analog_board.channel import YeSrAnalogChannel

class BoardE(YeSrAnalogBoard):
    conductor_servername = 'conductor'
    ok_servername = 'yeelmo_ok'
    ok_interface = '1744000K2I'
    sequence_directory = "/home/srgang/J/sequences/{}/"

    autostart = True
    is_master = False #was True, 05/06/2022
    channels = [
        YeSrAnalogChannel(loc=0, name='MOT Ramp', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=1, name='813 Intensity', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=2, name='X-bias', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=3, name='Y-bias', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=4, name='Z-bias top', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=5, name='DC Stark A', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=6, name='DC Stark B', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=7, name='Fixed 813 setpoint', mode='manual', manual_output=-0.54), # lattice voltage zero level.
        ]

Device = BoardE
