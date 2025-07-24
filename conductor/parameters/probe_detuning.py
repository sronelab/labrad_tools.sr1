from conductor.parameter import ConductorParameter

class ProbeDetuning(ConductorParameter):
    priority = 5 #Must be higer than clock_aom.hr_frequency and clock_fiber_aom.hr_demod_frequency
    autostart = False
    call_in_thread = False

    def initialize(self,config):
        self.connect_to_labrad()
        self.value =-235623697.25

    def update(self):
        if self.value is not None:
            request = {'si_demod': {}}
            mjm_comb_demod = self.server._get_parameter_values(request, all=False)['si_demod']
            f_vco = 155.504e6/2.0

            SL_FNC_table_AOM = 30.0e6
            #SL_FNC_comb = 95.524640e6 + 2*SL_FNC_table_AOM # this is the equation for the old distribution center
            SL_FNC_comb = 95.520e6 + 2.*SL_FNC_table_AOM # this is the equation for the current distribution center (2021-04-15)
            f_fnc = 2.0*(-1.0*float(self.value)  + SL_FNC_comb/2.0 - mjm_comb_demod)
            f_steer = f_fnc/2.0 - f_vco
            print "f_fnc: %f"%f_fnc
            print "f_steer: %f"%f_steer
            request = {
                    'clock_aom.hr_frequency': float(f_steer),
                    'clock_fiber_aom.hr_demod_frequency': float(f_fnc/2.0),
                    }
            self.server._set_parameter_values(request)


Parameter = ProbeDetuning
