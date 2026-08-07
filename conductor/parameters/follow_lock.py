from conductor.parameter import ConductorParameter

class FollowLock(ConductorParameter):

    priority = 5
    autostart = True

    def initialize(self, config):
        self.value = 0


    def update(self):
        if self.value is not None:
            request = {
                    'follow_lock': float(self.value),
                    }
            self.server._set_parameter_values(request)

Parameter =  FollowLock

