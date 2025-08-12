from conductor.parameter import ConductorParameter


#Top clock PM on the last AOM
#set the phase deviation
# +/-2.5V = +/- phase

#class for top clock psk
class ShakeAmplitude(ConductorParameter):

#Normally must initialize for first shot
#    def initialize(self,config):

    priority = 4
    autostart = False


    def update(self):




        if self.value is not None:
            shake_amp = self.value
            # print('top clock PM dev: ' + str(phase_dev))
            request = {
                    'clock_mF.hr_shake_vpp': float(shake_amp),
                    }
            self.server._set_parameter_values(request)




Parameter =  ShakeAmplitude

