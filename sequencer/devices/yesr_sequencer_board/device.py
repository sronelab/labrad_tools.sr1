from datetime import date, timedelta
from itertools import chain
import json
import os
import time

from device_server.device import DefaultDevice
from sequencer.devices.yesr_sequencer_board.helpers import time_to_ticks
from sequencer.devices.yesr_sequencer_board.helpers import combine_sequences
from ok_server.proxy import OKProxy


class YeSrSequencerBoard(DefaultDevice):
    sequencer_type = None

    ok_servername = None
    ok_interface = None
    ok_bitfilename = None

    conductor_servername = None

    channels = None

    mode_wire = 0x00
    sequence_pipe = 0x80
    clk = 50e6 # [Hz]

    sequence_directory = None #Now specified in experiment specific device files
    subsequence_names = None
    sequence = None
    raw_sequene = None
    raw_sequence_previous = None
    is_master = False
    master_channel = 'Trigger@D15'
    run_priority = 0

    loading = False
    running = False
    sequence = None
    sequence_bytes = None
    max_sequence_bytes = 24000

    parameter_values_previous = None
    is_device_writing = False

    def initialize(self, config):
        for key, value in config.items():
            setattr(self, key, value)

        for channel in self.channels:
            channel.set_board(self)

        self.connect_to_labrad()
        self.ok_server = self.cxn[self.ok_servername]
        ok = OKProxy(self.ok_server)

        fp = ok.okCFrontPanel()
        fp.OpenBySerial(self.ok_interface)
        fp.ConfigureFPGA(self.ok_bitfilename)
        self.fp = fp

        self.update_mode()
        self.update_channel_modes()
        self.update_channel_manual_outputs()


    def load_sequence(self, sequencename):
        for i in range(365):
            day = date.today() - timedelta(i)
            sequencepath = self.sequence_directory.format(day.strftime('%Y%m%d')) + sequencename
	    # print sequencepath
            if os.path.exists(sequencepath):
                break
        if not os.path.exists(sequencepath):
            raise SequenceNotFoundError(sequence_name)

        with open(sequencepath, 'r') as infile:
            sequence = json.load(infile)
        return sequence

    def save_sequence(self, sequence, sequence_name, tmpdir=True):
        sequence_directory = self.sequence_directory.format(time.strftime('%Y%m%d'))
	# print sequence_directory
        if tmpdir:
            sequence_directory = os.path.join(sequence_directory, '.tmp')
        if not os.path.exists(sequence_directory):
            os.makedirs(sequence_directory)
        sequence_path = os.path.join(sequence_directory, sequence_name)
        with open(sequence_path, 'w+') as outfile:
            json.dump(sequence, outfile)

    def get_channel(self, channel_id, suppress_error=False):
        """
        expect 3 possibilities for channel_id.
        1) name -> return channel with that name
        2) @loc -> return channel at that location
        3) name@loc -> first try name, then location
        """
        channel = None

        nameloc = channel_id.split('@') + ['']
        name = nameloc[0]
        loc = nameloc[1]
        if name:
           for c in self.channels:
               if c.name == name:
                   channel = c
        if not channel:
            for c in self.channels:
                if c.loc == loc:
                    channel = c
        if (channel is None) and not suppress_error:
            raise ChannelNotFound(channel_id)
        return channel

    def match_sequence_key(self, channel_sequences, channel_key):
        channel_nameloc = channel_key.split('@') + ['']
        channel_name = channel_nameloc[0]
        channel_loc = channel_nameloc[1]

        for sequence_key, sequence in channel_sequences.items():
            sequence_nameloc = sequence_key.split('@') + ['']
            if sequence_nameloc == channel_nameloc:
                return sequence_key

        for sequence_key, sequence in channel_sequences.items():
            sequence_name = (sequence_key.split('@') + [''])[0]
            if sequence_name == channel_name:
                return sequence_key

        for sequence_key, sequence in channel_sequences.items():
            sequence_loc = (sequence_key.split('@') + [''])[1]
            if sequence_loc == channel_loc:
                return sequence_key

    def update_channel_modes(self):
        """ to be implemented by child class """

    def update_channel_manual_outputs(self):
        """ to be implemented by child class """

    def default_sequence_segment(self, channel, dt):
        """ to be implemented by child class """


    def fix_sequence_keys(self, subsequence_names, tmpdir):
        for subsequence_name in set(subsequence_names):
            subsequence = self.load_sequence(subsequence_name)
            master_subsequence = subsequence[self.master_channel]
            for channel in self.channels:
                channel_subsequence = None
                matched_key = self.match_sequence_key(subsequence, channel.key)
                if matched_key:
                    channel_subsequence = subsequence.pop(matched_key)
                if not channel_subsequence:
                    channel_subsequence = [
                        self.default_sequence_segment(channel, s['dt'])
                            for s in master_subsequence
                        ]
                subsequence.update({channel.key: channel_subsequence})

            self.save_sequence(subsequence, subsequence_name, tmpdir)


    def set_sequence(self, subsequence_names):
        self.fix_sequence_keys(subsequence_names, False)
        self.subsequence_names = subsequence_names

        subsequence_list = []
        for subsequence_name in subsequence_names:
            subsequence = self.load_sequence(subsequence_name)
            subsequence_list.append(subsequence)
        raw_sequence = combine_sequences(subsequence_list)
        self.set_raw_sequence(raw_sequence)

    def get_sequence(self):
        return self.subsequence_names

    def set_raw_sequence(self, raw_sequence):
        self.raw_sequence = raw_sequence
        parameter_names = self.get_sequence_parameter_names(raw_sequence)
        parameter_values = self.get_sequence_parameter_values(parameter_names)

        # Rewrite if the previous and the current parameter_values are different.
        if True: #(parameter_values != self.parameter_values_previous) | (raw_sequence != self.raw_sequence_previous):
            #print("Rewriting the sequence...")
            self.is_device_writing = True

            #ti = time.time()
            programmable_sequence = self.substitute_sequence_parameters(raw_sequence, parameter_values)
            sequence_bytes = self.make_sequence_bytes(programmable_sequence)
            if len(sequence_bytes) > self.max_sequence_bytes:
                message = "sequence of {} bytes exceeds maximum length of {} bytes".format(len(sequence_bytes), self.max_sequence_bytes)
                raise Exception(message)
            self.sequence_bytes = sequence_bytes
            self.set_loading(True)
            self.fp.WriteToPipeIn(self.sequence_pipe, self.sequence_bytes)
            self.set_loading(False)
            #print(" took {} seconds".format(time.time()-ti))

            self.is_device_writing = False
        else:
            print("Skip rewriting the sequence. Parameter values are the same.")
            self.is_device_writing = False

        #save parameter_values for the next shot
        #self.parameter_values_previous = parameter_values
        #self.raw_sequence_previous = raw_sequence

    def get_raw_sequence(self):
        return self.raw_sequence

    def get_sequence_parameter_names(self, x):
        if type(x).__name__ in ['str', 'unicode'] and x[0] == '*':
            return [x]
        elif type(x).__name__ == 'list':
            return set(list(chain.from_iterable([
                self.get_sequence_parameter_names(xx)
                for xx in x])))
        elif type(x).__name__ == 'dict':
            return set(list(chain.from_iterable([
                self.get_sequence_parameter_names(v)
                for v in x.values()])))
        else:
            return []

    def get_sequence_parameter_values(self, parameter_names):
        if parameter_names:
            request = {
                parameter_name.replace('*', 'sequencer.'): None
                    for parameter_name in parameter_names
                }
            # print request
            conductor_server = self.cxn[self.conductor_servername]
            parameter_values_json = conductor_server.get_next_parameter_values(json.dumps(request))
            parameter_values = json.loads(parameter_values_json)
        else:
            parameter_values = {}
        sequence_parameter_values = {
            name.replace('sequencer.', '*'): value
                for name, value in parameter_values.items()
            }
        return sequence_parameter_values

    def substitute_sequence_parameters(self, x, parameter_values):
        if type(x).__name__ in ['str', 'unicode']:
            if x[0] == '*':
                return parameter_values[x]
            else:
                return x
        elif type(x).__name__ == 'list':
            return [self.substitute_sequence_parameters(xx, parameter_values) for xx in x]
        elif type(x).__name__ == 'dict':
            return {k: self.substitute_sequence_parameters(v, parameter_values) for k, v in x.items()}
        else:
            return x

    def make_sequence_bytes(self, sequence):
        """ to be implemented by child class """

    def update_mode(self):
        mode_word = 0 | 2 * int(self.loading) | self.running
        self.fp.SetWireInValue(self.mode_wire, mode_word)
        self.fp.UpdateWireIns()

    def set_loading(self, loading):
        if loading is not None:
            self.loading = loading
            self.update_mode()

    def get_loading(self):
        return self.running

    def set_running(self, running):
        if running is not None:
            self.running = running
            self.update_mode()

    def get_running(self):
        return self.running

    def get_is_device_writing(self):
        return self.is_device_writing
