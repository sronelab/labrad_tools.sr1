class FrequencyOutOfBoundsError(Exception):
    pass

class AmplitudeOutOfBoundsError(Exception):
    pass

class DG4000(object):
    _vxi11_address = None
    _source = None

    _frequency_range = (0, float('inf'))
    _amplitude_range = (-float('inf'), float('inf'))
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        if 'vxi11' not in  globals():
            global vxi11
            import vxi11
        self._inst = vxi11.Instrument(self._vxi11_address)

    @property
    def state(self):
        command = 'OUTP{}?'.format(self._source)
        ans = self._inst.ask(command)
        if ans == 'ON':
            state = True
        else:
            state = False
        return state
    
    @state.setter
    def state(self, state):
        command = 'OUTP{}:STAT {}'.format(self._source, int(bool(state)))
        self._inst.write(command)

    @property
    def frequency(self):
        command = 'SOUR{}:FREQ?'.format(self._source)
        ans = self._inst.ask(command)
        return float(ans)
    
    @frequency.setter
    def frequency(self, frequency):
        if frequency < min(self._frequency_range) or frequency > max(self._frequency_range):
            raise FrequencyOutOfBoundsError(frequency)
        command = 'SOUR{}:FREQ {}'.format(self._source, frequency)
        self._inst.write(command)

    @property
    def mod_type(self):
        command = 'SOUR{}:MOD:TYP?'.format(self._source)
        ans = self._inst.ask(command)
        return float(ans)
    
    @mod_type.setter
    def mod_type(self, mod_parameter):
        command = 'SOUR{}:MOD:TYP {}'.format(self._source, mod_parameter)
        self._inst.write(command)
    
    @property
    def fsk_source(self):
        command = 'SOUR{}:MOD:FSK:SOUR?'.format(self._source)
        ans = self._inst.ask(command)
        return float(ans)
    
    @fsk_source.setter
    def fsk_source(self, fsk_source):
        command = 'SOUR{}:MOD:FSK:SOUR {}'.format(self._source, fsk_source)
        self._inst.write(command)

    @property
    def fsk_frequency(self):
        command = 'SOUR{}:MOD:FSK?'.format(self._source)
        ans = self._inst.ask(command)
        return float(ans)
    
    @fsk_frequency.setter
    def fsk_frequency(self, fsk_frequency):
        command = 'SOUR{}:MOD:FSK {}'.format(self._source, fsk_frequency)
        self._inst.write(command)
    
    @property
    def start_frequency(self):
        command = 'SOUR{}:FREQ:STAR?'.format(self._source)
        ans = self._inst.ask(command)
        return float(ans)
    
    @start_frequency.setter
    def start_frequency(self, frequency):
        if frequency < min(self._frequency_range) or frequency > max(self._frequency_range):
            raise FrequencyOutOfBoundsError(frequency)
        command = 'SOUR{}:FREQ:STAR {}'.format(self._source, frequency)
        self._inst.write(command)
    
    @property
    def stop_frequency(self):
        command = 'SOUR{}:FREQ:STOP?'.format(self._source)
        ans = self._inst.ask(command)
        return float(ans)
    
    @stop_frequency.setter
    def stop_frequency(self, frequency):
        if frequency < min(self._frequency_range) or frequency > max(self._frequency_range):
            raise FrequencyOutOfBoundsError(frequency)
        command = 'SOUR{}:FREQ:STOP {}'.format(self._source, frequency)
        self._inst.write(command)
    
    @property
    def amplitude(self):
        command = 'SOUR{}:VOLT?'.format(self._source)
        ans = self._inst.ask(command)
        return float(ans)
    
    @amplitude.setter
    def amplitude(self, amplitude):
        if amplitude < min(self._amplitude_range) or amplitude > max(self._amplitude_range):
            raise AmplitudeOutOfBoundsError(amplitude)
        command = 'SOUR{}:VOLT {}'.format(self._source, amplitude)
        self._inst.write(command)
        
    @property
    def offset(self):
        command = 'SOUR{}:VOLT:OFFS?'.format(self._source)
        ans = self._inst.ask(command)
        return float(ans)
    
    @offset.setter
    def offset(self, offset):
        command = 'SOUR{}:VOLT:OFFS {}'.format(self._source, offset)
        self._inst.write(command)

class DG4000Proxy(DG4000):
    _vxi11_servername = None

    def __init__(self, cxn=None, **kwargs):
        if cxn == None:
            import labrad
            cxn = labrad.connect()
        from vxi11_server.proxy import Vxi11Proxy
        global vxi11
        vxi11 = Vxi11Proxy(cxn[self._vxi11_servername])
        DG4000.__init__(self, **kwargs)
