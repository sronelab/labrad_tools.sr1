from conductor.parameter import ConductorParameter
import json
from collections import deque

class Ditherer(object):
    def __init__(self, **kw):
        self.side = None
        for key, value in kw.items():
            setattr(self, key, value)
 
    @property
    def output(self):
        if self.side == 'left':
            return -self.modulation_depth 
        elif self.side == 'right':
            return self.modulation_depth 


class DitherPoint(ConductorParameter):
    """ 
    example_config = {
        'locks': {
            '+9/2': {
                'modulation_depth': 1,
                'control_parameters': ['clock_aom'],
                },
            '-9/2': {
                'modulation_depth': 1,
                'control_parameters': ['clock_aom'],
                },
            },
        }
    """
    locks = {}
    priority = 8
    autostart = True
    value_type = 'list'
    value_log = deque([None, None, None], maxlen=3)
    shot_number_log = deque([None, None, None], maxlen=3)


    def initialize(self, config):
        super(DitherPoint, self).initialize(config)
        for name, settings in self.locks.items():
            self.locks[name] = Ditherer(**settings)

    def _get_lock(self, lock):
        if lock not in self.locks:
            message = 'lock ({}) not defined in {}'.format(lock, self.name)
            raise Exception(message)
        else:
            return self.locks[lock]

    def update(self):
        if self.value is not None:
            name, side = self.value
            # these conditions are for ramsey echo pulses interleaved with locking pulses
            # we assume two locks, a '-9/2a' and '+9/2a' lock and '+/-9/2follow' locks which
            # have no servo feedback but just sit atop the line and executes echo pulses
            if name == '-9/2follow':
                ditherer = self._get_lock(name)
                ditherer.side = side
                request = {'clock_servo.dithers.{}'.format(name): ditherer.output}
                self.server._set_parameter_values(request)
                
                control_loop = self.server._get_parameter('clock_servo.feedback_point')._get_lock('-9/2a')
                output = control_loop.output + ditherer.output
                control_loop.pmt_shot_number = self.server.experiment.get('shot_number')
                
                follow_loop = self.server._get_parameter('clock_servo.feedback_point')._get_lock(name)
                follow_loop.output = control_loop.output

                request = {parameter_name: output 
                        for parameter_name in ditherer.control_parameters}
                self.server._set_parameter_values(request)
                print("-9/2 echo probe frequency: " + str(output))


            elif name == '+9/2follow':
                ditherer = self._get_lock(name)
                ditherer.side = side
                request = {'clock_servo.dithers.{}'.format(name): ditherer.output}
                self.server._set_parameter_values(request)
                
                control_loop = self.server._get_parameter('clock_servo.feedback_point')._get_lock('+9/2a')
                output = control_loop.output + ditherer.output
                control_loop.pmt_shot_number = self.server.experiment.get('shot_number')

                follow_loop = self.server._get_parameter('clock_servo.feedback_point')._get_lock(name)
                follow_loop.output = control_loop.output

                request = {parameter_name: output 
                        for parameter_name in ditherer.control_parameters}
                self.server._set_parameter_values(request)
                print("+9/2 echo probe frequency: " + str(output))


            else:
                ditherer = self._get_lock(name)
                ditherer.side = side
                request = {'clock_servo.dithers.{}'.format(name): ditherer.output}
                self.server._set_parameter_values(request)
                
                control_loop = self.server._get_parameter('clock_servo.feedback_point')._get_lock(name)
                output = control_loop.output + ditherer.output
                control_loop.pmt_shot_number = self.server.experiment.get('shot_number')
                
                request = {parameter_name: output 
                        for parameter_name in ditherer.control_parameters}
                self.server._set_parameter_values(request)
                print("{} probe frequency: {}".format(name, output))

        if self.value_log[-2] is not None:
            value = self.value_log[-2]
            lock, side = value
            shot_number = self.shot_number_log[-2]
            feedback_point_value = [lock, side, shot_number]
            request = {'clock_servo.feedback_point': feedback_point_value}
            self.server._set_parameter_values(request)
        if self.server._get_parameter_value('blue_pmt.recorder'):
            self.value_log.append(self.value)
            self.shot_number_log.append(self.server.experiment.get('shot_number'))


Parameter = DitherPoint

