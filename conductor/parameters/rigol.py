from conductor.parameter import ConductorParameter
import json
import threading

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
        self.running_lock = threading.Lock()

    def update(self):
        if self.value is not None:
            if self.running_lock.acquire(blocking=False):
                try:
                    self.value = json.loads(self.cxn.yezoe_rigol.acquire_data())
                finally:
                    self.running_lock.release()
            else:
                self.value = {
                'scope1': defult_value,
                'scope2': defult_value,
                }
        

Parameter =  Rigol