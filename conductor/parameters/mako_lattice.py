from conductor.parameter import ConductorParameter

# This class is used to read the tilt sensor through the labjack and store the data in a list
#to add a new tilt sensor, add a new element to the list in initialization and in the update function
pixel_far = 5.86
pixel_near = 3.75

class mako_lattice(ConductorParameter):
    priority=2
    autostart=True
    call_in_thread = True

    def initialize(self,config):
        self.connect_to_labrad()
        self.value = {
            'x_near': 0,
            'y_near': 0,
            'x_far': 0,
            'y_far': 0,
            'error_x_near': 0,
            'error_y_near': 0,
            'error_x_far': 0,
            'error_y_far': 0,
            }

    def update(self):
        try:
            position_near, error_near = self.cxn.yecookiemonster_mako.AcquireNear()
            position_far, error_far = self.cxn.yecookiemonster_mako.AcquireFar()
            self.value = {
                    'x_near': position_near[0]*pixel_near,
                    'y_near': position_near[1]*pixel_near,
                    'x_far': position_far[0]*pixel_far,
                    'y_far': position_far[1]*pixel_far,
                    'error_x_near': error_near[0]*pixel_near,
                    'error_y_near': error_near[1]*pixel_near,
                    'error_x_far': error_far[0]*pixel_far,
                    'error_y_far': error_far[1]*pixel_far,
                    }
        except Exception as e:
            print("Error updating mako lattice: {}".format(e))
            self.value = {
                'x_near': 0,
                'y_near': 0,
                'x_far': 0,
                'y_far': 0,
                'error_x_near': 0,
                'error_y_near': 0,
                'error_x_far': 0,
                'error_y_far': 0,
            }

Parameter = mako_lattice