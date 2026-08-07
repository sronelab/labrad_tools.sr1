from conductor.parameter import ConductorParameter
from rf.devices.dg4000.device import DG4000

#Top clock PM on the last AOM
#set the phase deviation
# +/-2.5V = +/- phase

class Channel1(DG4000):
    _vxi11_address = '192.168.1.37'
    _source = 1

    def update(self, frequency, fsk_frequency):
        self.mod_type = 'FSK'
        self.fsk_source = 'EXT'
        self.amplitude = 1.4159
        self.frequency = frequency
        self.fsk_frequency = fsk_frequency

class Channel2(DG4000):
    _vxi11_address = '192.168.1.37'
    _source = 2

    def update(self, frequency, fsk_frequency):
        self.mod_type = 'FSK'
        self.fsk_source = 'EXT'
        self.amplitude = 1.4159
        self.frequency = frequency
        self.fsk_frequency = fsk_frequency

#class for top clock psk
class Bottom_LO_Detuning(ConductorParameter):

#Normally must initialize for first shot
#    def initialize(self,config):

    priority = 3
    autostart = False


    def initialize(self, config):
        self.value = None

    def update(self):

        if self.value is not None and self.value != 0:
            request = {'f_9_7': {}}
            f_9_7 = self.server._get_parameter_values(request, all=False)['f_9_7']
            request = {'f_7_5': {}}
            f_7_5 = self.server._get_parameter_values(request, all=False)['f_7_5']
            request = {'f_5_3': {}}
            f_5_3 = self.server._get_parameter_values(request, all=False)['f_5_3']
            request = {'f_5_3_ss': {}}
            f_5_3_ss = self.server._get_parameter_values(request, all=False)['f_5_3_ss']

            request = {'probe_detuning_mF': {}}
            mF_value = self.server._get_parameter_values(request, all=False)['probe_detuning_mF']
            print('bottom Lo mf value:')
            print(mF_value)
            request = {'si_demod': {}}
            mjm_comb_demod = self.server._get_parameter_values(request, all=False)['si_demod']

            SL_FNC_table_AOM = 30.0e6
            SL_FNC_comb = 95.520e6 + 2*SL_FNC_table_AOM # updated as of 2021-04-15
            f_lo = -1.0*float(mF_value)  + SL_FNC_comb/2.0 - mjm_comb_demod

            channel1 = Channel1()
            channel2 = Channel2()
            channel1.update(f_lo+f_9_7, f_lo+f_7_5)
            channel2.update(f_lo+f_5_3, f_lo+f_5_3_ss)

Parameter =  Bottom_LO_Detuning
