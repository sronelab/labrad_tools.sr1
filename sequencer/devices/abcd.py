from sequencer.devices.yesr_digital_board.device import YeSrDigitalBoard
from sequencer.devices.yesr_digital_board.channel import YeSrDigitalChannel

class BoardABCD(YeSrDigitalBoard):
    ok_servername = 'yeelmo_ok'
    ok_interface = '1541000D3S'

    conductor_servername = 'conductor'

    sequence_directory = "/home/srgang/J/sequences/{}/"
    autostart = True
    is_master = True

    channels = [
        YeSrDigitalChannel(loc=['A', 0], name='AH mult A2', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['A', 1], name='AH mult A1', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['A', 2], name='AH mult A0', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['A', 3], name='AH TTL', mode='auto', manual_output=False, invert=True),
        YeSrDigitalChannel(loc=['A', 4], name='Zeeman shutter', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['A', 5], name='Probe shutter', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['A', 6], name='Probe AOM', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['A', 7], name='Blue MOT shutter', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['A', 8], name='Blue MOT AOM', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['A', 9], name='2D MOT shutter', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['A', 10], name='Blue Int SW', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['A', 11], name='Repump', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['A', 12], name='FNC Integrator Enable', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['A', 13], name='FNC DDS Ramp', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['A', 14], name='Vertical Mako', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['A', 15], name='Cam Trig', mode='auto', manual_output=False, invert=False),
        
        YeSrDigitalChannel(loc=['B', 0], name='11/2 AOM', mode='auto', manual_output=False, invert=True),
        YeSrDigitalChannel(loc=['B', 1], name='Axial AOM', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['B', 2], name='9/2 AOM', mode='auto', manual_output=False, invert=True),
        YeSrDigitalChannel(loc=['B', 3], name='Red Int SW', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['B', 4], name='Blue x-MOT arm shutter', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['B', 5], name='NCB5', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['B', 6], name='Polarizing AOM', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['B', 7], name='Clock RF TTL', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['B', 8], name='Polarizing shutter', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['B', 9], name='Axial shutter', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['B', 10], name='9/2 shutter', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['B', 11], name='11/2 shutter', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['B', 12], name='Repump AOM', mode='auto', manual_output=False, invert=True),
        YeSrDigitalChannel(loc=['B', 13], name='11/2 Int Switch', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['B', 14], name='NC', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['B', 15], name='FSK Polarizing', mode='auto', manual_output=False, invert=False),
        
        YeSrDigitalChannel(loc=['C', 0], name='Picoscope Trigger', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['C', 1], name='Uniblitz Shutter', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['C', 2], name='Oven TTL', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['C', 3], name='Clock Intensity', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['C', 4], name='Pol/Rp LC WP', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['C', 5], name='9/2 Gain Switch', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['C', 6], name='11/2 Gain Switch', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['C', 7], name='Top clock shutter', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['C', 8], name='FNC LO switch', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['C', 9], name='f_steer RF switch', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['C', 10], name='ND flipper TTL', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['C', 11], name='NC21', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['C', 12], name='NC22', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['C', 13], name='NC23', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['C', 14], name='NC24', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['C', 15], name='NC25', mode='auto', manual_output=False, invert=False),
        
        YeSrDigitalChannel(loc=['D', 0], name='NC26', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['D', 1], name='NC27', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['D', 2], name='NC28', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['D', 3], name='NC29', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['D', 4], name='NC30', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['D', 5], name='NC31', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['D', 6], name='NC32', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['D', 7], name='NC33', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['D', 8], name='NC34', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['D', 9], name='NC35', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['D', 10], name='NC36', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['D', 11], name='NC37', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['D', 12], name='NC38', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['D', 13], name='NC39', mode='auto', manual_output=False, invert=False),
        YeSrDigitalChannel(loc=['D', 14], name='NC40', mode='auto', manual_output=True, invert=False),
        YeSrDigitalChannel(loc=['D', 15], name='Trigger', mode='auto', manual_output=False, invert=False),
        ]
        
Device = BoardABCD
