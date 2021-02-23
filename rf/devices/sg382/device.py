from device_server.device import DefaultDevice

import vxi11

class SG382(DefaultDevice):
    vxi11_address = None
    
    frequency = None
    frequency_range = (1e-6, 30e6)

    update_parameters = ['frequency']
    
    def initialize(self, config):
        super(SG382, self).initialize(config)
        self.vxi11 = vxi11.Instrument(self.vxi11_address)
        self.do_update_parameters()

    def do_update_parameters(self):
        self.frequency = self.get_frequency()
    
    def set_frequency(self, frequency):
        frequency = sorted([min(self.frequency_range), 
            max(self.frequency_range), frequency])[1]
        command = 'FREQ {}'.format(frequency)
        self.vxi11.write(command)

    def get_frequency(self):
        command = 'FREQ?'
        ans = self.vxi11.ask(command)
        self.frequency = float(ans)
        return self.frequency
