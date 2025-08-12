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
    def wave_type(self):
        command = 'SOUR{}:APPL?'.format(self._source)
        ans = self._inst.ask(command)
        return float(ans)
    
    @wave_type.setter
    def wave_type(self, waveform):
        command = 'SOUR{}:APPL: {}'.format(self._source, waveform)
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
    def psk_source(self):
        command = 'SOUR{}:MOD:PSK:SOUR?'.format(self._source)
        ans = self._inst.ask(command)
        return float(ans)
    
    @psk_source.setter
    def psk_source(self, psk_source):
        command = 'SOUR{}:MOD:PSK:SOUR {}'.format(self._source, psk_source)
        self._inst.write(command)

    @property
    def psk_phase(self):
        command = 'SOUR{}:MOD:PSK:PHAS?'.format(self._source)
        ans = self._inst.ask(command)
        return float(ans)
    
    @psk_phase.setter
    def psk_phase(self, psk_phase):
        command = 'SOUR{}:MOD:PSK:PHAS {}'.format(self._source, psk_phase)
        self._inst.write(command)

    @property
    def pm_source(self):
        command = 'SOUR{}:MOD:PM:SOUR?'.format(self._source)
        ans = self._inst.ask(command)
        return float(ans)
    
    @pm_source.setter
    def pm_source(self, pm_source):
        command = 'SOUR{}:MOD:PM:SOUR {}'.format(self._source, pm_source)
        self._inst.write(command)

    @property
    def pm_dev(self):
        command = 'SOUR{}:MOD:PM?'.format(self._source)
        ans = self._inst.ask(command)
        return float(ans)
    
    @pm_dev.setter
    def pm_dev(self, pm_dev):
        command = 'SOUR{}:MOD:PM {}'.format(self._source, pm_dev)
        self._inst.write(command)


    @property
    def ask_source(self):
        command = 'SOUR{}:MOD:ASK:SOUR?'.format(self._source)
        ans = self._inst.ask(command)
        return float(ans)
    
    @ask_source.setter
    def ask_source(self, ask_source):
        command = 'SOUR{}:MOD:ASK:SOUR {}'.format(self._source, ask_source)
        self._inst.write(command)

    @property
    def ask_polarity(self):
        command = 'SOUR{}:MOD:ASK:POL?'.format(self._source)
        ans = self._inst.ask(command)
        return float(ans)
    
    @ask_polarity.setter
    def ask_polarity(self, ask_pol):
        command = 'SOUR{}:MOD:ASK:POL {}'.format(self._source, ask_pol)
        self._inst.write(command)

    @property
    def ask_amplitude(self):
        command = 'SOUR{}:MOD:ASK:AMPL?'.format(self._source)
        ans = self._inst.ask(command)
        return float(ans).amplit
    
    @ask_amplitude.setter
    def ask_amplitude(self, ask_amp):
        command = 'SOUR{}:MOD:ASK:AMPL {}'.format(self._source, ask_amp)
        self._inst.write(command)

    @property
    def duty_cycle(self):
        command = 'SOUR{}:PULSe:DCYCle?'.format(self._source)
        ans = self._inst.ask(command)
        return float(ans)
    
    @duty_cycle.setter
    def duty_cycle(self, duty_cycle):
        command = 'SOUR{}:PULSe:DCYCle {}'.format(self._source, duty_cycle)
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
        # Ensure unit is set to VPP before querying
        self._inst.write('SOUR{}:VOLT:UNIT VPP'.format(self._source))
        command = 'SOUR{}:VOLT?'.format(self._source)
        ans = self._inst.ask(command)
        return float(ans)

    @amplitude.setter
    def amplitude(self, amplitude):
        if amplitude < min(self._amplitude_range) or amplitude > max(self._amplitude_range):
            raise AmplitudeOutOfBoundsError(amplitude)
        # Ensure unit is set to VPP before setting
        self._inst.write('SOUR{}:VOLT:UNIT VPP'.format(self._source))
        command = 'SOUR{}:VOLT {}'.format(self._source, amplitude)
        self._inst.write(command)

    # @property
    # def amplitude(self):
    #     command = 'SOUR{}:VOLT?'.format(self._source)
    #     ans = self._inst.ask(command)
    #     return float(ans)
    
    # @amplitude.setter
    # def amplitude(self, amplitude):
    #     if amplitude < min(self._amplitude_range) or amplitude > max(self._amplitude_range):
    #         raise AmplitudeOutOfBoundsError(amplitude)
    #     command = 'SOUR{}:VOLT {}'.format(self._source, amplitude)
    #     self._inst.write(command)
        
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
