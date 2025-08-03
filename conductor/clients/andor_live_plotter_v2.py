#!/usr/bin/env python
"""
Real-time Andor live plotter using update server instead of file polling
Combines the live plotting functionality with update server data feed
"""

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import matplotlib
from scipy.optimize import curve_fit
import sys
import os
import datetime
import json
import time
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

# Twisted/LabRAD imports
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from client_tools.connection import connection

print("Real-time Andor Live Plotter with Update Server")
print("Python version: " + sys.version)

font = {'family': 'DejaVu Sans',
        'weight': 'normal',
        'size': 16}

matplotlib.rc('font', **font)

# Use a backend that works with threading
matplotlib.use('Qt5Agg')

class RealTimeAndorPlotter:
    def __init__(self):
        self.fig = plt.figure(figsize=(12, 12), num='Andor Real-Time Monitor')
        self.ax1 = self.fig.add_subplot(2, 1, 1)
        self.ax2 = self.fig.add_subplot(2, 1, 2)
        
        # Data storage
        self.current_data = None
        self.last_update_time = None
        self.update_count = 0
        
        # LabRAD connection
        self.cxn = None
        self.update_server = None
        
        # Animation
        self.ani = None
        
    def gauss(self, x, H, A, x0, sigma):
        """Gaussian function for fitting"""
        return H + A * np.exp(-(x - x0) ** 2 / (2 * sigma ** 2))

    def div0(self, a, b):
        """Division with zero protection"""
        with np.errstate(divide='ignore', invalid='ignore'):
            c = np.true_divide(a, b)
            c[~np.isfinite(c)] = 0  # -inf inf NaN
        return c

    @inlineCallbacks
    def connect_to_update_server(self):
        """Connect to the update server and register for andor data"""
        try:
            print("Connecting to LabRAD...")
            self.cxn = yield connection().connect(name='andor_live_plotter_realtime')
            
            print("Connecting to update server...")
            self.update_server = yield self.cxn.get_server('update')
            
            # Register for andor data
            yield self.update_server.register('andor_data')
            print("Registered for andor_data channel")
            
            # Setup signal listener
            signal_id = 1001  # Unique ID
            yield self.update_server.signal__signal.connect(signal_id)
            yield self.update_server.addListener(
                listener=self.on_data_received,
                source=None,
                ID=signal_id
            )
            
            print("Signal listener setup complete")
            print("Waiting for andor data...")
            
        except Exception as e:
            print("Error connecting to update server: {}".format(e))
            
    def on_data_received(self, context, data):
        """Handle incoming andor data from update server"""
        try:
            # Parse JSON data
            parsed_data = json.loads(data)
            
            # Check if this is andor fluorescence data
            if parsed_data.get('data_type') == 'fluorescence_1D':
                # Convert image arrays back from lists
                andor_data = {
                    'g': np.array(parsed_data['temp_image_g']),
                    'e': np.array(parsed_data['temp_image_e']),
                    'bg': np.array(parsed_data['temp_image_bg']),
                    'timestamp': parsed_data['timestamp'],
                    'camera_temp': parsed_data.get('camera_temp', 'N/A'),
                    'emccd_gain': parsed_data.get('emccd_gain', 'N/A'),
                    'ntot_estimate': parsed_data.get('ntot_estimate', 0),
                    'fraction_estimate': parsed_data.get('fraction_estimate', 0)
                }
                
                self.current_data = andor_data
                self.last_update_time = time.time()
                self.update_count += 1
                
                print("Received update #{} - Ntot: {:.1f}, Fraction: {:.3f}".format(
                    self.update_count, 
                    andor_data['ntot_estimate'], 
                    andor_data['fraction_estimate']
                ))
                
        except Exception as e:
            print("Error processing data: {}".format(e))

    def animate(self, i):
        """Animation function called by matplotlib"""
        if self.current_data is None:
            # Show waiting message
            self.ax1.clear()
            self.ax2.clear()
            self.ax1.text(0.5, 0.5, 'Waiting for andor data...', 
                         transform=self.ax1.transAxes, ha='center', va='center', fontsize=20)
            self.ax2.text(0.5, 0.5, 'Update count: {}'.format(self.update_count), 
                         transform=self.ax2.transAxes, ha='center', va='center', fontsize=16)
            return

        try:
            data = self.current_data
            
            # Process the data (same as original)
            bg = data['bg']
            gnd = data['g'] - bg
            exc = data['e'] - bg
            tot = gnd + exc
            
            frac = self.div0(exc, (gnd + exc))
            
            x = np.linspace(0, 512*6*1e-3, num=512)
            xpix = np.linspace(0, 512, num=512)
            
            # Gaussian fitting
            try:
                pfit, pfitcov = curve_fit(self.gauss, xpix, tot, p0=[0.0, 20.0, 256.0, 50.0])
            except:
                pfit = [0.0, 20.0, 256.0, 50.0]  # Use default if fitting fails
            
            Ntot = (np.sum(exc[0:-1]) + np.sum(gnd[0:-1]))/10
            
            # Send data to InfluxDB (same as original)
            try:
                token = 'yelabtoken'
                org = 'yelab'
                bucket = 'data_logging'
                with InfluxDBClient(url="http://yesnuffleupagus.colorado.edu:8086", token=token, org=org, debug=False) as client:
                    write_api = client.write_api(write_options=SYNCHRONOUS)
                    write_api.write(bucket, org, "Andor,Area=Integrated Ntot={}".format(Ntot))
            except:
                pass  # Silently fail if InfluxDB is not available
            
            sites_per_pixel = 6/0.813*2
            
            # Plot 1: Atom distribution
            self.ax1.clear()
            self.ax1.plot(x, self.gauss(xpix, *pfit)/10/sites_per_pixel, ls='--', alpha=0.5, label="tot-fit", color="black")
            self.ax1.axvline((pfit[2] + 1.5*pfit[3])*6*1e-3, ls="--", color="black")
            self.ax1.axvline((pfit[2] - 1.5*pfit[3])*6*1e-3, ls="--", color="black")
            self.ax1.fill_between(x, bg/10/sites_per_pixel, label="background", color="C2", lw=2, alpha=0.7)
            self.ax1.fill_between(x, gnd/10/sites_per_pixel, label="$^1 S _0, |g\\rangle$", color="C0", lw=2, alpha=0.7)
            self.ax1.fill_between(x, exc/10/sites_per_pixel, label="$^3 P_0, |e\\rangle$", color="C1", lw=2, alpha=0.7)
            self.ax1.plot(x, tot/10/sites_per_pixel, color="black", label="$N_{tot }$", lw=2, alpha=1)
            self.ax1.legend(bbox_to_anchor=(1.05, 1.0), loc='upper left')
            self.ax1.set_ylabel("Atoms/ lattice site")
            self.ax1.set_xlabel("z [mm]")
            self.ax1.grid()
            
            # Title with real-time info
            title = "$N_{{tot}}$: {} | Center: {:.2f} mm | $\\sigma$: {:.2f} mm | Updates: {}".format(
                int(Ntot), 
                (pfit[2])*6*1e-3, 
                (pfit[3])*6*1e-3,
                self.update_count
            )
            self.ax1.set_title(title, fontsize=20)
            self.ax1.set_xlim([np.min(x), np.max(x)])
            
            # Plot 2: Excited state fraction
            mean_frac = np.mean(exc[0:-1]) / (np.mean(exc[0:-1]) + np.mean(gnd[0:-1]))
            self.ax2.clear()
            self.ax2.plot(x, frac, ls="none", marker='.', label="data")
            N = 11
            self.ax2.plot(x, np.convolve(frac, np.ones(N)/N)[int((N-1)/2):-int((N-1)/2)], color="C0", alpha=0.5, label="box. avg.")
            
            # Add timing info to title
            if self.last_update_time:
                time_ago = time.time() - self.last_update_time
                timing_info = " | Last update: {:.1f}s ago".format(time_ago)
            else:
                timing_info = ""
                
            title2 = "$\\langle \\rho^{{ee}}(z)\\rangle_{{0 mm}}^{{2 mm}}$: {:.4f}{}".format(mean_frac, timing_info)
            self.ax2.set_title(title2, fontsize=20)
            self.ax2.set_ylabel("$\\rho^{ee}$")
            self.ax2.axvline((pfit[2] + 1.5*pfit[3])*6*1e-3, ls="--", color="black")
            self.ax2.axvline((pfit[2] - 1.5*pfit[3])*6*1e-3, ls="--", color="black")
            self.ax2.set_xlabel("z [mm]")
            self.ax2.set_ylim([-0.1, 1.1])
            self.ax2.grid()
            self.ax2.set_xlim([np.min(x), np.max(x)])
            self.ax2.legend(bbox_to_anchor=(1.05, 1.0), loc='upper left')
            
            self.fig.tight_layout()
            
        except Exception as e:
            print("Error in animation: {}".format(e))

    def start_plotting(self):
        """Start the real-time plotting"""
        # Start animation
        self.ani = animation.FuncAnimation(self.fig, self.animate, interval=1000, cache_frame_data=False)
        
        # Start the plot
        plt.show()

    def cleanup(self):
        """Clean up connections"""
        try:
            if self.cxn:
                self.cxn.disconnect()
        except:
            pass


def main():
    """Main function"""
    plotter = RealTimeAndorPlotter()
    
    def start_plotter():
        """Start the plotter after connecting"""
        d = plotter.connect_to_update_server()
        d.addErrback(lambda failure: print("Connection failed: {}".format(failure)))
    
    # Setup graceful shutdown
    def shutdown(signum=None, frame=None):
        print("Shutting down...")
        plotter.cleanup()
        reactor.stop()
    
    # Handle Ctrl+C
    import signal
    signal.signal(signal.SIGINT, shutdown)
    
    # Connect to update server when reactor starts
    reactor.callWhenRunning(start_plotter)
    
    # Start plotting in a separate thread so reactor can run
    import threading
    plot_thread = threading.Thread(target=plotter.start_plotting)
    plot_thread.daemon = True
    plot_thread.start()
    
    print("Starting real-time Andor plotter...")
    print("Make sure the update server is running and andor parameter is active")
    
    # Run the reactor
    reactor.run()


if __name__ == '__main__':
    main()