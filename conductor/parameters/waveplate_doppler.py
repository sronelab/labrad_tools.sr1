from conductor.parameter import ConductorParameter


#This will create a conductor parameters for setting the doppler waveplate ASK



#class for MOT WP setting
class waveplate_doppler(ConductorParameter):

#Normally must initialize for first shot
#    def initialize(self,config):

    priority = 4
    autostart = False


    def update(self):

        if self.value is not None:
            ask_voltage = self.value
            print('Doppler WP Voltage (p-p): ' + str(ask_voltage))
            request = {
                    'doppler_wp.doppler_ASK': float(ask_voltage), 
                    }
            self.server._set_parameter_values(request)




Parameter =  waveplate_doppler
