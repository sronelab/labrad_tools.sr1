import sequencer.devices.yesr_analog_board.device
reload(sequencer.devices.yesr_analog_board.device)
import sequencer.devices.yesr_analog_board.channel
reload(sequencer.devices.yesr_analog_board.channel)
from sequencer.devices.yesr_analog_board.device import YeSrAnalogBoard
from sequencer.devices.yesr_analog_board.channel import YeSrAnalogChannel

class BoardF(YeSrAnalogBoard):
    conductor_servername = 'conductor'
    ok_servername = 'yeelmo_ok'
    ok_interface = '1744000K23'
    sequence_directory = "/home/srgang/J/sequences/{}/"

    autostart = True
    is_master = True

    channels = [
        YeSrAnalogChannel(loc=0, name='DC Stark D', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=1, name='SG382 mF clock FM', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=2, name='11/2 Intensity', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=3, name='9/2 Intensity', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=4, name='Fixed 813 setpoint -540mV', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=5, name='9/2 FM', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=6, name='11/2 FM', mode='auto', manual_output=0.0),
        YeSrAnalogChannel(loc=7, name='ANC13', mode='auto', manual_output=0.0),
        ]


Device = BoardF
