#!/usr/bin/env python
"""
Simple web-based Andor plotter for Python 2.7
Uses basic Flask without WebSockets - polls for updates
"""

import json
import time
import threading
from datetime import datetime
import numpy as np
from scipy.optimize import curve_fit

# Flask imports (basic)
from flask import Flask, render_template, jsonify

# Twisted/LabRAD imports (Python 2)
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from client_tools.connection import connection

app = Flask(__name__)

class SimpleAndorPlotter:
    def __init__(self):
        self.current_data = None
        self.last_update_time = None
        self.update_count = 0
        self.processed_data = None

        # LabRAD connection
        self.cxn = None
        self.update_server = None

        # Threading for reactor
        self.reactor_thread = None
        self.is_connected = False

    def gauss(self, x, H, A, x0, sigma):
        """Gaussian function for fitting"""
        return H + A * np.exp(-(x - x0) ** 2 / (2 * sigma ** 2))

    def div0(self, a, b):
        """Division with zero protection"""
        with np.errstate(divide='ignore', invalid='ignore'):
            c = np.true_divide(a, b)
            c[~np.isfinite(c)] = 0
        return c

    @inlineCallbacks
    def connect_to_update_server(self):
        """Connect to the update server"""
        try:
            print("Connecting to LabRAD...")
            self.cxn = yield connection().connect(name='andor_web_simple')

            print("Connecting to update server...")
            self.update_server = yield self.cxn.get_server('update')

            # Register for andor data
            yield self.update_server.register('andor_data')
            print("Registered for andor_data channel")

            # Setup signal listener
            signal_id = 9999  # Use a different unique ID
            print("Setting up signal listener with ID: {}".format(signal_id))
            yield self.update_server.signal__signal(signal_id)
            yield self.update_server.addListener(
                listener=self.on_data_received,
                source=None,
                ID=signal_id
            )
            print("Signal listener registered successfully")

            self.is_connected = True
            print("Simple web plotter connected to update server")

        except Exception as e:
            print("Error connecting to update server: {}".format(e))
            self.is_connected = False

    def on_data_received(self, context, data):
        """Handle incoming andor data from update server"""
        try:
            print("Received signal data, attempting to parse...")
            parsed_data = json.loads(data)

            if parsed_data.get('data_type') == 'fluorescence_1D':
                print("Found fluorescence_1D data, processing...")
                # Store raw data
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

                # Process data for web display
                self.process_data()

                print("Web plotter received update #{} - Ntot: {:.1f}".format(
                    self.update_count, andor_data['ntot_estimate']))
            else:
                print("Received data but not fluorescence_1D type: {}".format(parsed_data.get('data_type', 'unknown')))

        except Exception as e:
            print("Error processing data: {}".format(e))
            import traceback
            print("Full traceback:")
            traceback.print_exc()

    def process_data(self):
        """Process the data for web display"""
        if self.current_data is None:
            return

        try:
            data = self.current_data

            # Process the data (same as desktop version)
            bg = data['bg']
            gnd = data['g'] - bg
            exc = data['e'] - bg
            tot = gnd + exc

            frac = self.div0(exc, (gnd + exc))

            x = np.linspace(0, 512*6*1e-3, num=512).tolist()
            xpix = np.linspace(0, 512, num=512)

            # Gaussian fitting
            try:
                pfit, pfitcov = curve_fit(self.gauss, xpix, tot, p0=[0.0, 20.0, 256.0, 50.0])
            except:
                pfit = [0.0, 20.0, 256.0, 50.0]

            Ntot = (np.sum(exc[0:-1]) + np.sum(gnd[0:-1]))/10
            sites_per_pixel = 6/0.813*2

            # Prepare data for web display
            self.processed_data = {
                'x': x,
                'background': (bg/10/sites_per_pixel).tolist(),
                'ground': (gnd/10/sites_per_pixel).tolist(),
                'excited': (exc/10/sites_per_pixel).tolist(),
                'total': (tot/10/sites_per_pixel).tolist(),
                'fit': (self.gauss(xpix, *pfit)/10/sites_per_pixel).tolist(),
                'fraction': frac.tolist(),
                'fraction_smoothed': np.convolve(frac, np.ones(11)/11)[5:-5].tolist(),
                'x_fraction': x[5:-5],  # Adjusted for smoothing
                'fit_params': {
                    'center': float((pfit[2])*6*1e-3),
                    'sigma': float((pfit[3])*6*1e-3),
                    'center_plus': float((pfit[2] + 1.5*pfit[3])*6*1e-3),
                    'center_minus': float((pfit[2] - 1.5*pfit[3])*6*1e-3)
                },
                'statistics': {
                    'ntot': int(Ntot),
                    'mean_fraction': float(np.mean(exc[0:-1]) / (np.mean(exc[0:-1]) + np.mean(gnd[0:-1]))),
                    'camera_temp': str(data['camera_temp']),
                    'emccd_gain': str(data['emccd_gain']),
                    'update_count': self.update_count,
                    'timestamp': datetime.fromtimestamp(data['timestamp']).strftime('%H:%M:%S'),
                    'time_ago': time.time() - self.last_update_time if self.last_update_time else 0
                }
            }

        except Exception as e:
            print("Error processing data for web: {}".format(e))

    def start_reactor(self):
        """Start the Twisted reactor in a separate thread"""
        def run_reactor():
            reactor.callWhenRunning(self.connect_to_update_server)
            reactor.run(installSignalHandlers=False)

        self.reactor_thread = threading.Thread(target=run_reactor)
        self.reactor_thread.daemon = True
        self.reactor_thread.start()

    def stop(self):
        """Clean up connections"""
        try:
            if self.cxn:
                self.cxn.disconnect()
            if reactor.running:
                reactor.stop()
        except:
            pass

# Global plotter instance
plotter = SimpleAndorPlotter()

@app.route('/')
def index():
    """Main page"""
    return render_template('andor_simple.html')

@app.route('/api/status')
def get_status():
    """Get current status"""
    return jsonify({
        'connected': plotter.is_connected,
        'update_count': plotter.update_count,
        'last_update': plotter.last_update_time,
        'has_data': plotter.processed_data is not None
    })

@app.route('/api/data')
def get_current_data():
    """Get current processed data"""
    if plotter.processed_data:
        return jsonify(plotter.processed_data)
    else:
        return jsonify({'error': 'No data available'})

def main():
    """Main function"""
    print("Starting Simple Andor Web Plotter (Python 2)...")
    print("Uses polling instead of WebSockets for Python 2.7 compatibility")

    # Start the reactor in background
    plotter.start_reactor()

    # Give reactor time to start
    time.sleep(2)

    try:
        print("Web server starting on http://localhost:5000")
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        plotter.stop()

if __name__ == '__main__':
    main()
