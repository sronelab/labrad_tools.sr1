from picomotor.devices.nf8742.device import NF8742

class Motor(NF8742):
    socket_address = ('192.168.1.22', 23)
    controller_axis = 4

Device = Motor
