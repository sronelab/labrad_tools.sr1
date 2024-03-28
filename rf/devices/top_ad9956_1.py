import rf.devices.ad9956.device
reload(rf.devices.ad9956.device)
from rf.devices.ad9956.device import AD9956

class Channel(AD9956):
    autostart = True
    serial_servername = "yeelmo_serial"
    serial_address = '/dev/ttyACM7583331373335171B241'
    board_num = 1
    #sysclk=1e9
    channel = 0

    default_frequency = 73e6 #Default frequency between 0th order retro and resonance

Device = Channel
