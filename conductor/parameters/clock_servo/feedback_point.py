from conductor.parameter import ConductorParameter
from control_loops import PID, PIID
import json
import os
 
class FeedbackPoint(ConductorParameter):
    """ 
    example_config = {
        'locks': {
            '+9/2': {
                'type': 'PID',
                'prop_gain': 1,
                ...
                },
            '-9/2': {
                'type': 'PID',
                'prop_gain': 1,
                ...
                },
            },
        }
    """
    locks = {}
    priority = 9
    autostart = True
    value_type = 'list'

    def initialize(self, config):
        super(FeedbackPoint, self).initialize(config)
        self.connect_to_labrad()
        for name, settings in self.locks.items():
            if settings['type'] == 'PID':
                self.locks[name] = PID(**settings)
            if settings['type'] == 'PIID':
                self.locks[name] = PIID(**settings)

    def _get_lock(self, lock):
        if lock not in self.locks:
            message = 'lock ({}) not defined in {}'.format(lock, self.name)
            raise Exception(message)
        else:
            return self.locks[lock]
    def update(self):
        experiment_name = self.server.experiment.get('name')
        if (self.value is not None) and (experiment_name is not None):
            name, side, shot = self.value
            control_loop = self._get_lock(name)

            point_filename = '{}.blue_pmt'.format(shot)
            point_path = os.path.join(experiment_name, point_filename)

            request = {'blue_pmt': point_path}
            response_json = self.cxn.pmt.retrive_records(json.dumps(request))
            response = json.loads(response_json)
            frac = response['blue_pmt']['frac_fit']
            tot = response['blue_pmt']['tot_fit']

            if tot > control_loop.tot_cutoff:
                control_loop.tick(side, frac)

            request = {'clock_servo.control_signals.{}'.format(name): control_loop.output}
            self.server._set_parameter_values(request)

Parameter = FeedbackPoint
