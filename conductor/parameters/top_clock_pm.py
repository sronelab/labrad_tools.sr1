from conductor.parameter import ConductorParameter


#Top clock PM on the last AOM
#set the phase deviation
# +/-2.5V = +/- phase

#class for top clock psk
class TopClockPM(ConductorParameter):

#Normally must initialize for first shot
#    def initialize(self,config):

    priority = 4
    autostart = False
    call_in_thread = False

    def update(self):




        if self.value is not None:
            phase_dev = self.value
            # print('top clock PM dev: ' + str(phase_dev))
            request = {
                    'clock_mF.hr_frequency_pm': float(phase_dev),
                    }
            self.server._set_parameter_values(request)




Parameter =  TopClockPM
