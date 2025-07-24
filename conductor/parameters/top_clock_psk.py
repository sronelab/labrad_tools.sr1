from conductor.parameter import ConductorParameter


#Top clock PSK on the last AOM


#class for top clock psk
class TopClockPSK(ConductorParameter):

#Normally must initialize for first shot
#    def initialize(self,config):

    priority = 4
    autostart = False


    def update(self):




        if self.value is not None:
            phase = self.value
            # print('top clock PSK (degrees): ' + str(phase))
            request = {
                    'clock_mF.hr_frequency_psk': float(phase),
                    }
            self.server._set_parameter_values(request)




Parameter =  TopClockPSK
