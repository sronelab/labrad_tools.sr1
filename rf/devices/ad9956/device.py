import time
import struct

from twisted.internet import reactor

from device_server.device import DefaultDevice
from rf.devices.ad9956.helpers import get_instruction_set
from serial_server.proxy import SerialProxy

class AD9956(DefaultDevice):
    """ serial wrapper for controlling AD9959

    this class is meant to be inherited:

    class MyDDS(AD9959):
        serial_address = '/dev/ACM0'
        board_num = 0
        channel_num = 0

    >> my_dds = MyDDS()

    frequencies can then be programmed via
    >> my_dds.set_frequency(100e6)
    or read via
    >> my_dds.get_frequency(100e6)

    """
    serial_servername = None
    serial_address = None
    serial_timeout = 0.05
    serial_baudrate = 9600
    
    board_num = None
    channel_num = None

    sysclk = 400e6
    syncclk = sysclk/4.0

    cfr1_reg = int(0x00)
    cfr2_reg = int(0x01)
    rdftw_reg = int(0x02)
    fdftw_reg = int(0x03)
    rsrr_reg = int(0x04)
    fsrr_reg = int(0x05)
    flow_reg = int(0x06)
    fhigh_reg = int(0x07)
    extra_regs=[int(0x08), int(0x09), int(0x0A), int(0x0B), int(0x0C), int(0x0D)]



    ramprate=None
    frequency_low = None
    frequency_high = None
    extra_freqs=[None, None, None, None, None, None]
    default_frequency = 0
    frequency_range = [0, sysclk / 2]

    update_parameters = ['frequency']
    
    def initialize(self, config):
        super(AD9956, self).initialize(config)
        
        self.connect_to_labrad()
        self.serial_server = self.cxn[self.serial_servername]

        serial = SerialProxy(self.serial_server)
        ser = serial.Serial(self.serial_address)
        ser.timeout = self.serial_timeout
        ser.baudrate = self.serial_baudrate
        self.ser = ser

        time.sleep(0.5) 
        reactor.callInThread(self.delayed_call, 5, self.set_frequency, self.default_frequency)

        # Setting a sinlge frequency manually for debugging
        # reactor.callInThread(self.delayed_call, 5, self.set_frequency, 150e6, 0, "high")
        # reactor.callInThread(self.delayed_call, 5, self.set_frequency, 30e6, 1, "high")
    
    def delayed_call(self, delay, func, *args):
        time.sleep(delay)
        func(*args)

    def make_cfr1w(self, mode):
        """ make control function register 1 word

        specifies either sweep mode or single frequency mode
        also ensures that we continue using 3-wire serial communication

        Args:
            mode (str): 'sweep' for frequency ramp, 'single' for single 
                frequency output.
        Returns:
            list of four bytes
        """

        linear_sweep_no_dwell = 0b0
        sdio_input_only = 0b1 #Configure for 3-wire serial communication
        cfr1w = [None, None, None, None]
        if mode == 'sweep':
            linear_sweep_enable = 0b1
        elif mode == 'single':
            linear_sweep_enable = 0b0
        else:
            linear_sweep_enable = 0b0

        cfr1w[0] = 0x00
        cfr1w[1] = linear_sweep_no_dwell + (linear_sweep_enable << 1) + 0x00
        cfr1w[2] = (sdio_input_only << 6) + 0x00
        cfr1w[3] = 0x00
        return cfr1w

    def make_ftw(self, frequency):
        """ make frequency tuning word

        Args:
            frequency (float): frequency in units of Hz
        Returns:
            list of 8 bytes, specifying frequency in units of SYSCLK. By default 
            the phase is set to zero by setting the first two bytes to zero.
        """
        ftw = hex(int(frequency * 2.**48 / self.sysclk))[2:].zfill(16)
        return [int('0x' + ftw[i:i+2], 0) for i in range(0, 16, 2)]

    
    def make_rsrrw(self, rate=1):
        """ make rising sweep ramp rate word

        Args:
            rate: (int) if <  0, increase time between sweep steps to 
                (rate / SYNC_CLK). minimum rate is 2**16 / SYNCCLK = 1525.879 Hz 
                for 400 MHz SYSCLK.
        Returns:
            list of 2 bytes, specifying sweep step rate in units of SYNCCLK.
        """
        t_step = max(-rate, 1)
        rsrww = hex(int(t_step))[2:].zfill(4)
        return [int('0x' + rsrww[i:i+2], 0) for i in range(0, 4, 2)]

    def make_fsrrw(self, rate=1):
        """ make falling sweep ramp rate word

        Args:
            rate: (int) if <  0, increase time between sweep steps to 
                (rate / SYNC_CLK). minimum rate is 2**16 / SYNCCLK = 1525.879 Hz 
                for 400 MHz SYSCLK.
        Returns:
            list of 2 bytes, specifying sweep step rate in units of SYNCCLK.
        """
        t_step = max(-rate, 1)
        fsrww = hex(int(t_step))[2:].zfill(4)
        return [int('0x' + fsrww[i:i+2], 0) for i in range(0, 4, 2)]
    
    def make_rdftw(self, rate):
        """ make rising delta frequency tuning word 

        Args: 
            rate: frequency step of ramp in Hz. rdftw given by 
                int(freq*SYSCLK/2*24). the minimum step size is 930 mHz for a 
                400 MHz clock. given frequency will be scaled to the nearest 
                integer multiple of the minimum step size
        Returns:
            list of 4 bytes, MSB first, of ramp down word
        """
        step_size = max(rate, 1) 
        rdftw = hex(int(step_size))[2:].zfill(6)
        return [int('0x' + rdftw[i:i+2], 0) for i in range(0, 6, 2)]

    def make_fdftw(self, rate):
        """ make falling delta frequency tuning word 

        Args: 
            freq (float): frequency step of ramp in Hz. fdftw given by 
                int(freq*SYSCLK/2*24) the minimum step size is 93 mHz for a 400 
                MHz clock. given frequency will be scaled to the nearest integer 
                multiple of the minimum step size
        Returns:
            list of 4 bytes, MSB first, of ramp down word
        """
        step_size = max(rate, 1) 
        fdftw = hex(int(step_size))[2:].zfill(6)
        return [int('0x' + fdftw[i:i+2], 0) for i in range(0, 6, 2)]
    
    def set_linear_ramp(self, start=None, stop=None, rate=1):
        """ program triggerable ramp.
        Args:
            start: (float) frequency [Hz] corresponding to logic low
            stop: (float) frequency [Hz] corresponding to logic high
            rate: (int) if > 0, number of sys_clk (100 MHz) cycles per step
                0-65535 (2**16). if < 0, step size from 0-16777215 (2**24)
        Returns:
            None
        """
        if rate == None:
            rate = 1
        self.ramprate=rate
        if stop >= start:
            ftw_start = self.make_ftw(start) #Write start frequency to pcr0
            ftw_stop = self.make_ftw(stop) #Write stop frequency to pcr1
            cfr1w = self.make_cfr1w('sweep') #Enable sweep mode
            rsrr = self.make_rsrrw(rate)
            fsrr = self.make_fsrrw(rate)
            rdw = self.make_rdftw(rate)
            fdw = self.make_fdftw(rate)
            instruction_set = (
                get_instruction_set(self.board_num, self.cfr1_reg, cfr1w)
                + get_instruction_set(self.board_num, self.rdftw_reg, rdw)
                + get_instruction_set(self.board_num, self.fdftw_reg, fdw)
                + get_instruction_set(self.board_num, self.rsrr_reg, rsrr)
                + get_instruction_set(self.board_num, self.fsrr_reg, fsrr)
                + get_instruction_set(self.board_num, self.flow_reg, ftw_start) 
                + get_instruction_set(self.board_num, self.fhigh_reg, ftw_stop) 
                )
            command = ''.join(instruction_set)
            self.ser.write(command)
#            self.serial_server.write(self.serial_address, command)
        else:
            message = "End frequency must be greater than start frequency in current set up."
            raise Exception(message)

    def get_linear_ramp(self):
        # could retunr start stop rate here
        return None

    def set_frequency(self, frequency, board=-1, output=None):
        """ select single frequency output mode at specified frequency

        Args:
            frequency: (float) frequency in units of Hz
        Returns:
            None
        """
        # overwrite board if no input
        if board == -1:
            board = self.board_num
        
        #overwrite output if no input
        if output == None:
            output='low'

        min_freq = min(self.frequency_range)
        max_freq = max(self.frequency_range)
        if not frequency == sorted([frequency, min_freq, max_freq])[1]:
            message = ('frequency: {} Hz is outside of range [{} Hz, {} Hz].'
                    ''.format(frequency, min_freq, max_freq))
            raise Exception(message)
        #Set to single frequency output mode
        cfr1w = self.make_cfr1w('single') 
        #Write frequency word to pcr0 (ramp enable TTL input on DDS box must 
        # be set to FALSE by LABVIEW)
        ftw = self.make_ftw(frequency) 
        if output == 'high':
            instruction_set = (
                get_instruction_set(board, self.cfr1_reg, cfr1w)
                + get_instruction_set(board, self.fhigh_reg, ftw)
                )
        elif output =='low':
            instruction_set = (
                get_instruction_set(board, self.cfr1_reg, cfr1w)
                + get_instruction_set(board, self.flow_reg, ftw)
                )
        else:
            instruction_set = (
                get_instruction_set(board, self.cfr1_reg, cfr1w)
                + get_instruction_set(board, self.extra_regs[output], ftw)
                )       
        command = ''.join(instruction_set)
        self.ser.write(command)
#        self.serial_server.write(self.serial_address, command)
        
        if output == 'low':
            self.frequency_low = frequency
        elif output == 'high':
            self.frequency_high = frequency
        elif (0 <= output and 6 > output ):
            self.extra_freqs[output] = frequency
        else:
            message = ("Specified output channel is out of range")
            raise Exception(message)


    def set_ramprate(self, rate):
        """
        set ramp conditions in operation where cfrw1 is rewritten via a trigger to initiate ramp mode
        
        Args: rate -- integer rate which determines frequency step size and time delay between steps (see command generation functions 
        called below. )
        """
        self.ramprate=rate
        if (rate > -2**16 and rate < 2**24):
            cfr1w = self.make_cfr1w('single') #keep single mode for TTL triggering to ramp mode, what this set_ramprate function is used fo
            rsrr = self.make_rsrrw(rate)
            fsrr = self.make_fsrrw(rate)
            rdw = self.make_rdftw(rate)
            fdw = self.make_fdftw(rate)
            instruction_set = (
                get_instruction_set(self.board_num, self.cfr1_reg, cfr1w)
                + get_instruction_set(self.board_num, self.rdftw_reg, rdw)
                + get_instruction_set(self.board_num, self.fdftw_reg, fdw)
                + get_instruction_set(self.board_num, self.rsrr_reg, rsrr)
                + get_instruction_set(self.board_num, self.fsrr_reg, fsrr)
            )
            command = ''.join(instruction_set)
            self.ser.write(command)
        else:
            message = "ramp rate out of range"
            raise Exception(message)

    def get_frequency(self, output='low'):
        """ get programmed freqeuncy

        Args: 
            None
        Returns:
            frequency: (float) frequency in units of Hz
        """
        frequency = None
        if output == 'low':
            frequency = self.frequency_low
        elif output == 'high':
            frequency = self.frequency_high
        elif (0 <= output and 6 > output ):
            frequency =self.extra_freqs[output]
        else: 
            message = 'output selection: {} is not either "high" or "low" or less than 6'
            raise Exception(message)
        return frequency

    def get_ramprate(self):
        """ get programmed freqeuncy

        Args: 
            None
        Returns:
            frequency: ramp rate
        """
        return self.ramprate