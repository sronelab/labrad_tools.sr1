import pyvisa
import numpy as np
import time
from datetime import datetime
import json


def mean_rms(times, volts, start=0, stop=0.5):
    """Compute mean and AC RMS over a time window."""
    mask = (times >= start) & (times <= stop)
    if not np.any(mask):
        return None, None
    volts_mask = volts[mask]
    mean = np.mean(volts_mask)
    rms = np.std(volts_mask, ddof=1)/np.sqrt(len(volts_mask))
    return mean, rms


class RigolOscilloscope:

    def __init__(self, config):

        self.config = config

        self.ip = config["ip"]
        self.trig_channel = config["trig_channel"]
        self.trig_level = config["trig_level"]
        self.timebase = config["timebase"]
        self.time_offset = config['time_offset']
        self.rms_window = config["rms_window"]
        self.rms_start = config["rms_start"]
        self.channels = config["channels"]

        self.rm = pyvisa.ResourceManager("@py")
        self.scope = self.rm.open_resource(f"TCPIP0::{self.ip}::INSTR")
        self.scope.timeout = 2500

        print(f"Connected: {self.scope.query('*IDN?').strip()}")

        self.scope.clear()
        self.scope.write("*CLS")

        # Horizontal settings
        self.scope.write(f":TIMebase:MAIN:SCAL {self.timebase}")
        

        # Memory depth
        self.scope.write(":ACQuire:MDEPth 100k")
        time.sleep(0.5)

        # Configure channels
        for ch, params in self.channels.items():
            self.configure_channel(ch, params["scale"], params["offset"])

        # Trigger configuration
        self.scope.write(":TRIG:MODE EDGE")
        self.scope.write(f":TRIG:EDGE:SOUR CHAN{self.trig_channel}")
        self.scope.write(":TRIG:EDGE:SLOP POS")
        self.scope.write(f":TRIG:EDGE:LEV {self.trig_level}")

        self.scope.write(f":TIMebase:OFFSet {self.time_offset}")

    def configure_channel(self, channel, scale, offset):

        self.scope.write(f":CHAN{channel}:DISP ON")
        self.scope.write(f":CHAN{channel}:SCALE {scale}")
        self.scope.write(f":CHAN{channel}:OFFSET {offset}")

    def arm_and_wait(self):

        self.scope.clear()
        self.scope.write("*CLS")

        self.scope.write(":SINGle")

        time.sleep(0.1)
        while True:
            status = self.scope.query(":TRIG:STAT?").strip()
            if status == "STOP":
                break
            time.sleep(0.1)

    def acquire_waveform(self, channel):

        self.scope.write(f":WAV:SOUR CHAN{channel}")
        self.scope.write(":WAV:MODE RAW")
        self.scope.write(":WAV:FORM BYTE")

        max_points = int(self.scope.query(":WAV:POIN?").strip())
        self.scope.write(":WAV:STAR 1")
        self.scope.write(f":WAV:STOP {max_points}")

        preamble = self.scope.query(":WAV:PRE?").split(',')
        x_increment = float(preamble[4])
        x_origin = float(preamble[5])
        y_increment = float(preamble[7])
        y_origin = float(preamble[8])
        y_reference = float(preamble[9])

        raw_data = self.scope.query_binary_values(':WAV:DATA?', datatype='B', container=np.array)
        if len(raw_data) == 0:
            print(f"Warning: CH{channel} returned 0 points.")
            return np.array([]), np.array([])

        data = (raw_data.astype(float) - y_reference - y_origin) * y_increment
        
        times = x_origin + (np.arange(len(data)) * x_increment)

        return times, data

    def acquire_and_process(self):

        try:
            status = self.scope.query(":TRIG:STAT?").strip()

            if status != "STOP":
                self.scope.write(":STOP")
                self.scope.query("*OPC?")
                time.sleep(0.1)

            self.arm_and_wait()
            time.sleep(0.1)
            results = {}
            for ch in self.channels.keys():

                times, volts = self.acquire_waveform(ch)
                mean, rms = mean_rms(
                    times,
                    volts,
                    start=self.rms_start,
                    stop=self.rms_start+self.rms_window
                )

                results[f"ch{ch}_mean"] = mean
                results[f"ch{ch}_rms"] = rms

        except pyvisa.VisaIOError as e:

            print(f"VisaIOError during acquisition: {e}")

            results = {}
            for ch in self.channels.keys():
                results[f"ch{ch}_mean"] = 0
                results[f"ch{ch}_rms"] = 0

        except Exception as e:

            print(f"Acquisition error: {e}")

            results = {}
            for ch in self.channels.keys():
                results[f"ch{ch}_mean"] = 0
                results[f"ch{ch}_rms"] = 0

        return results

    def close(self):

        self.scope.close()
        self.rm.close()