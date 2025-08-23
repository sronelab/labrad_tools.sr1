from conductor.parameter import ConductorParameter


#This will create a conductor parameters for setting the MOT waveplate voltage



#class for MOT WP setting
class waveplate_MOT(ConductorParameter):

#Normally must initialize for first shot
#    def initialize(self,config):

    priority = 4
    autostart = False
    call_in_thread = False

    def update(self):

        if self.value is not None:
            MOT_voltage = self.value
            # print('MOT WP Voltage (p-p): ' + str(MOT_voltage))
            request = {
                    'doppler_wp.MOT': float(MOT_voltage),
                    }
            self.server._set_parameter_values(request)




Parameter =  waveplate_MOT
