from conductor.parameter import ConductorParameter


#Goal is for this to write a FSK frequency to the last AOM on the top clock
#will use this FSK frequency to pump on the blue sideband


#test class for top clock bsb mod
class ProbeDetuningBSB(ConductorParameter):

#Normally must initialize for first shot
#    def initialize(self,config):

    priority = 4
    autostart = False


    def update(self):


        print('top clock BSB FSK called')

        if self.value is not None:
            bsb_value = self.value

            request = {
                    'clock_mF.hr_frequency_bsb': float(bsb_value), 
                    }
            self.server._set_parameter_values(request)




Parameter =  ProbeDetuningBSB
