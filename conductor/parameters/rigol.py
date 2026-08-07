from conductor.parameter import ConductorParameter
import json

defult_value = {
    "ch1_mean": 0,
    "ch1_rms": 0,
    "ch2_mean": 0,
    "ch2_rms": 0,
    "ch3_mean": 0,
    "ch3_rms": 0,
    "ch4_mean": 0,
    "ch4_rms": 0,
}
class Rigol(ConductorParameter):
    priority = 1
    autostart = False
    call_in_thread = True

    def initialize(self,config):
        self.connect_to_labrad()
        self.value = {
            'scope1': defult_value,
            'scope2': defult_value,
            }
        self.is_running = False

    def update(self):
        if self.value is not None:
            if not self.is_running:
                self.is_running = True
                try:
                    self.value = json.loads(self.cxn.yezoe_rigol.acquire_data())
                finally:
                    self.is_running = False
            else:
                self.value = {
                'scope1': defult_value,
                'scope2': defult_value,
                }
        

Parameter =  Rigol