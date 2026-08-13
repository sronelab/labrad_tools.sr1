import pyvisa
import numpy as np
import time
from datetime import datetime
import matplotlib.pyplot as plt
import json

RIGOL_IP = "192.168.1.114"
TRIG_CHANNEL = 4         
TRIG_LEVEL = .142

TIMEBASE = 0.02
RMS_WINDOW = 0.2
RMS_START = 0.005

SCALE_CH1 = 0.05
OFFSET_CH1 = -0.15
SCALE_CH3 = 0.05
OFFSET_CH3 = -0.65
SCALE_CH4 = 0.1
OFFSET_CH4 = -0.04

def mean_rms(times, volts, start=0, stop=0.5):
    """Compute mean and standard deviation (AC RMS) over a window [start, stop]"""
    mask = (times >= start) & (times <= stop)
    if not np.any(mask):
        return np.nan, np.nan
    mean = np.mean(volts[mask])
    rms = np.sqrt(np.mean((volts[mask] - mean)**2))
    return mean, rms

class RigolOscilloscope:
    def __init__(self):
        self.rm = pyvisa.ResourceManager("@py")
        self.scope = self.rm.open_resource(f"TCPIP0::{RIGOL_IP}::INSTR")
        self.scope.timeout = 2000

        print(f"Connected: {self.scope.query('*IDN?').strip()}")
        self.scope.clear()       
        self.scope.write("*CLS") 

        # Reset horizontal scale and move trigger near the left edge
        self.scope.write(f":TIMebase:MAIN:SCAL {TIMEBASE}")
        # Using -0.095 instead of -0.1 to avoid edge-boundary rejections
        self.scope.write(":TIMebase:OFFSet 0.098") 

        # Force memory depth to 100k
        self.scope.write(":ACQuire:MDEPth 100k") 
        time.sleep(0.5)

        self.configure_channel(1, SCALE_CH1, OFFSET_CH1)
        self.configure_channel(3, SCALE_CH3, OFFSET_CH3)
        self.configure_channel(4, SCALE_CH4, OFFSET_CH4)

        self.scope.write(":TRIG:MODE EDGE")
        self.scope.write(f":TRIG:EDGE:SOUR CHAN{TRIG_CHANNEL}")
        self.scope.write(":TRIG:EDGE:SLOP POS")
        self.scope.write(f":TRIG:EDGE:LEV {TRIG_LEVEL}")


    def configure_channel(self, channel, scale, offset):
        self.scope.write(f":CHAN{channel}:DISP ON")
        self.scope.write(f':CHAN{channel}:SCALE {scale}')
        self.scope.write(f':CHAN{channel}:OFFSET {offset}')

    def arm_and_wait(self):
        """Arms the scope for a single shot and patiently waits for a full sweep."""
        self.scope.clear()
        self.scope.write("*CLS")
        
        self.scope.write(":SINGle")
        # print("Armed! Waiting for trigger event...")
        
        while True:
            status = self.scope.query(":TRIG:STAT?").strip()
            if status == "STOP":
                # print("Sweep 100% Complete! Memory is full and locked.")
                break
            time.sleep(0.1) 

    def acquire_waveform(self, channel):
        """Robust ASCII fetch dynamically reading available points."""
        self.scope.write(f":WAV:SOUR CHAN{channel}")
        self.scope.write(":WAV:MODE NORM")
        self.scope.write(":WAV:FORM ASC")
        
        max_points = int(self.scope.query(":WAV:POIN?").strip())
        
        self.scope.write(":WAV:STAR 1")
        self.scope.write(f":WAV:STOP {max_points}")
        
        preamble_str = self.scope.query(":WAV:PRE?")
        preamble = preamble_str.split(',')
        
        x_increment = float(preamble[4])
        x_origin    = float(preamble[5])
        
        raw_data = self.scope.query(":WAV:DATA?")
        
        if raw_data.startswith('#'):
            header_len = int(raw_data[1]) + 2 
            raw_data = raw_data[header_len:]
            
        data = np.array([float(val) for val in raw_data.split(',') if val.strip()])
        times = x_origin + (np.arange(len(data)) * x_increment)
        
        return times, data
    
    def acquire_and_process(self):
        print("Acquiring data from Rigol scope...")
        try:
            print("Validating scope status...")
            status = self.scope.query(":TRIG:STAT?").strip()
            if status != "STOP":
                self.scope.write(":STOP")
                self.scope.query("*OPC?") 
                time.sleep(0.1)

            self.arm_and_wait()
            
            times_ch1, volts_ch1 = self.acquire_waveform(1)
            times_ch3, volts_ch3 = self.acquire_waveform(3)
            times_ch4, volts_ch4 = self.acquire_waveform(4)

            mean_ch1, rms_ch1 = mean_rms(times_ch1, volts_ch1, start=RMS_START, stop=RMS_WINDOW)
            mean_ch3, rms_ch3 = mean_rms(times_ch3, volts_ch3, start=RMS_START, stop=RMS_WINDOW)
            mean_ch4, rms_ch4 = mean_rms(times_ch4, volts_ch4, start=RMS_START, stop=RMS_WINDOW)

            results = {
                'ch1_mean': mean_ch1,
                'ch1_rms': rms_ch1,
                'ch3_mean': mean_ch3,
                'ch3_rms': rms_ch3,
                'ch4_mean': mean_ch4,
                'ch4_rms': rms_ch4
            }

        except pyvisa.VisaIOError as e:
            print(f"VisaIOError during acquisition: {e}")
            results = {
                'ch1_mean': 0,
                'ch1_rms': 0,
                'ch3_mean': 0,
                'ch3_rms': 0,
                'ch4_mean': 0,
                'ch4_rms': 0
            }
        except Exception as e:
            print(f"Acquisition error: {e}")
            results = {
                'ch1_mean': 0,
                'ch1_rms': 0,
                'ch3_mean': 0,
                'ch3_rms': 0,
                'ch4_mean': 0,
                'ch4_rms': 0
            }

        print(results)
        return results

    def close(self):
        self.scope.close()
        self.rm.close()

if __name__ == "__main__":
    scope = RigolOscilloscope()
    start_time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"scope_log_{start_time_str}.jsonl"

    print(f"Starting acquisition loop. Logging data to: {log_filename}")

    try:
        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            results = scope.acquire_and_process()
            results['time'] = timestamp
            with open(log_filename, "a") as log_file:
                log_file.write(json.dumps(results) + "\n")
    finally:
        scope.close()