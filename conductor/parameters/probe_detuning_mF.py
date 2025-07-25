from conductor.parameter import ConductorParameter


#Goal is for this to function like probe_detuning.py. It grabs si demod (which we can dedrift on),
#then writes the f_steer for mF and fnc. Note here we don't have a doubleer, we are just using a sg382.


#test class for top clock mF
class ProbeDetuningMF(ConductorParameter):

#Normally must initialize for first shot

    priority = 4
    autostart = False

    # memory for the frequency values
    f_steer = None
    f_fnc = None
    f_9_7 = None
    f_7_5 = None
    f_5_3 = None
    f_bsb_m = None
    f_bsb_p = None

    def initialize(self, config):
        pass


    def update(self):


        # print('probe detuning mF update called')

        if self.value is not None:

            request = {'si_demod': {}}
            mjm_comb_demod = self.server._get_parameter_values(request, all=False)['si_demod']

            #get frequency detunings from sequencer for state preparation--seems to not be dynamic? but it worked before...
            request = {'f_9_7': {}}
            f_9_7 = self.server._get_parameter_values(request, all=False)['f_9_7']
            request = {'f_7_5': {}}
            f_7_5 = self.server._get_parameter_values(request, all=False)['f_7_5']
            request = {'f_5_3': {}}
            f_5_3 = self.server._get_parameter_values(request, all=False)['f_5_3']
            request = {'f_bsb_m': {}}
            f_bsb_m = self.server._get_parameter_values(request, all=False)['f_bsb_m']
            request = {'f_bsb_p': {}}
            f_bsb_p = self.server._get_parameter_values(request, all=False)['f_bsb_p']
            mF_value = self.value


            #If we threw a -1 we want to update mF to follow the dithers.
            if mF_value  == -1:
                print('-1 thrown in probe detunings')
                request = {'clock_servo.control_signals.+9/2':{},'clock_servo.control_signals.-9/2':{}}
                temporary_data = self.server._get_parameter_values(request, all=False)
                f_minus = temporary_data['clock_servo.control_signals.-9/2']
                f_plus = temporary_data['clock_servo.control_signals.+9/2']
                print(f_minus,f_plus)
                mF_value = (f_minus+f_plus)/2.



            f_vco = 155.504e6/2.0

            SL_FNC_table_AOM = 30.0e6
            SL_FNC_comb = 95.520e6 + 2*SL_FNC_table_AOM # updated as of 2021-04-15

            f_fnc = 2.0*(-1.0*float(mF_value)  + SL_FNC_comb/2.0 - mjm_comb_demod)
            f_steer = f_fnc/2.0 - f_vco

            #correcting for mF path. We take +1 order of f steer aftering going through -1 order
            #of 100 MHz aom
	    # Alex's modification 2022/02/02
	    # for top clock path we have a 41MHz AOM

            f_aom_2 = 41.e6 #41 MHz + 1 order
            #f_fnc = 73.504e6 #(f_vco - f_aom_2)*2
    #	    f_fnc = f_fnc - 2*f_steer - f_aom_2*2
    #	    f_steer = f_fnc/2.0 -f_vco + f_aom_2
            f_fnc += (-f_steer - f_aom_2)*2.0
            f_steer = f_steer + f_aom_2
            #f_steer_9_7=f_steer+f_9_7

#            f_fnc += (100.e6-f_steer)*2.
#            f_steer =  100.e6-f_steer

            #print "f_fnc_mF: %f"%f_fnc
            #print "f_steer_mF: %f"%f_steer


            f_steer = float(f_steer)
            f_fnc = float(f_fnc)
            f_9_7 = float(f_9_7)
            f_7_5 = float(f_7_5)
            f_5_3 = float(f_5_3)
            f_bsb_m = float(f_bsb_m)
            f_bsb_p = float(f_bsb_p)
            request = {}

            # request['clock_mF.hr_frequency_mF'] = f_steer
            request['clock_mF.hr_frequency_top_dds'] = f_steer

            # request['clock_mF.hr_demod_frequency_mF'] = f_fnc
            request['clock_mF.hr_demod_top_dds'] = f_fnc

            request['clock_mF.hr_demod_9_7'] = f_fnc
            request['clock_mF.hr_demod_7_5'] = f_fnc
            request['clock_mF.hr_demod_5_3'] = f_fnc

            request['clock_mF.hr_frequency_9_7'] = f_9_7
            request['clock_mF.hr_frequency_7_5'] = f_7_5
            request['clock_mF.hr_frequency_5_3'] = f_5_3
            # request['clock_mF.hr_frequency_bsb_m'] = f_bsb_m
            # request['clock_mF.hr_frequency_bsb_p'] = f_bsb_p

            self.server._set_parameter_values(request)

            self.f_steer = f_steer
            self.f_fnc = f_fnc
            self.f_9_7 = f_9_7
            self.f_7_5 = f_7_5
            self.f_5_3 = f_5_3
            self.f_bsb_m = f_bsb_m
            self.f_bsb_p = f_bsb_p
            # print("ProbeDetuningMF update list: ", request)

Parameter =  ProbeDetuningMF
