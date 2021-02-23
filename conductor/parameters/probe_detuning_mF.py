from conductor.parameter import ConductorParameter


#Goal is for this to function like probe_detuning.py. It grabs si demod (which we can dedrift on),
#then writes the f_steer for mF and fnc. Note here we don't have a doubleer, we are just using a sg382.


#test class for top clock mF
class ProbeDetuningMF(ConductorParameter):

#Normally must initialize for first shot
#    def initialize(self,config):

    autostart = False 
    priority = 4


    def update(self):


        if self.value is not None:

            request = {'si_demod': {}} 
            mjm_comb_demod = self.server._get_parameter_values(request, all=False)['si_demod']
            f_vco = 155.504e6/2.0

            SL_FNC_table_AOM = 30.0e6
            SL_FNC_comb = 95.524640e6 + 2*SL_FNC_table_AOM

            f_fnc = 2.0*(-1.0*float(self.value)  + SL_FNC_comb/2.0 - mjm_comb_demod)
            f_steer = f_fnc/2.0 - f_vco

            #correcting for mF path. We take +1 order of f steer aftering going through -1 order 
            #of 100 MHz aom
            f_fnc += (100.e6-f_steer)*2.
            f_steer =  100.e6-f_steer

            print "f_fnc_mF: %f"%f_fnc
            print "f_steer_mF: %f"%f_steer
            request = {
                    'clock_aom.hr_frequency_mF': float(f_steer), 
                    'clock_mF.hr_demod_frequency_mF': float(f_fnc),
                    }
            self.server._set_parameter_values(request)


            self.frequency = self.value



Parameter =  ProbeDetuningMF
