import sys, os, time, queue, numpy as np
from datetime import datetime
from vimba import *
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, 
                             QHBoxLayout, QWidget, QSpinBox, QDoubleSpinBox, QFormLayout, 
                             QPushButton, QCheckBox, QComboBox, QLineEdit, QSizePolicy,
                             QTextEdit, QTabWidget)
from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal, Qt, QThread, QCoreApplication
from PyQt6.QtGui import QFont, QPalette, QColor
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from matplotlib.patches import Ellipse
from mpl_toolkits.axes_grid1 import make_axes_locatable
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
    

class MakoCamera(QObject):
    data_ready = pyqtSignal(np.ndarray, int, dict)
    log_message = pyqtSignal(str)
    labrad_trigger_signal = pyqtSignal()

    def __init__(self, cam_id, defaults, fit_method):
        super().__init__()
        self.cam_id = cam_id
        self.defaults = defaults
        self.params = defaults.copy()
        self.running = False
        self.is_busy = False
        self.res_queue = queue.Queue()
        
        self.trigger_mode = "Labrad"
        self.trigger_interval = 2.0
        self.last_trigger_time = 0
        self.is_fitting = True 
        
        self.fit_method = fit_method
        self.fit_params = {"x":674, "y":441, "sigma_x": 183, "sigma_x": 110, "theta":0, "offset":0, "roi_size":500} #just for 2d

        self.labrad_trigger_signal.connect(self.execute_labrad_trigger)
        self.last_valid_data = ([0.0, 0.0], [0.0, 0.0])

    def init_camera(self, cam):
        try:
            self.log_message.emit('Initial camera: {}'.format(self.cam_id))
            cam.TriggerMode.set("On")
            cam.TriggerSource.set("Software")
            cam.AcquisitionMode.set("Continuous")
            cam.set_pixel_format(PixelFormat.Mono12)
            for key, val in self.defaults.items():
                getattr(cam, key).set(val)
        except Exception as e:
            self.log_message.emit("Camera Param Init Error: {}".format(e))
            
    @pyqtSlot()
    def start_streaming(self):
        self.running = True
        
        with Vimba.get_instance() as vimba:
            time.sleep(0.1)
            try:
                self.cam = vimba.get_camera_by_id(self.cam_id)
            except Exception as e:
                self.log_message.emit("Camera Opening Error: {}".format(e))
                return
            with self.cam as cam:
                try: 
                    self.init_camera(cam)
                    cam.start_streaming(self.handler, buffer_count=5)
                    while self.running:
                        QCoreApplication.processEvents()
                                
                        if self.trigger_mode == "GUI":
                            now = time.time()
                            if now - self.last_trigger_time >= self.trigger_interval:
                                try:
                                    cam.TriggerSoftware.run()
                                    self.last_trigger_time = now
                                except Exception as e: 
                                    self.log_message.emit(f"GUI Trigger Error: {e}")
                        time.sleep(0.01)
                finally:
                    cam.stop_streaming()
    

    def handler(self, cam, frame):
        if frame and frame.get_status() == FrameStatus.Complete:
            self.frame_id = frame.get_id()
            buffer = frame.get_buffer()
            h, w = frame.get_height(), frame.get_width()
            imag = (np.frombuffer(buffer, dtype=np.uint16).reshape(h, w)).astype(np.int16).copy()
            cam.queue_frame(frame)

            if self.is_fitting:
                fit_result = self.perform_fit(imag, self.fit_method)
            else:
                fit_result = self.get_empty_fit()
            
            self.data_ready.emit(imag, self.frame_id, fit_result)
            if self.trigger_mode == "Labrad":
                # self.last_valid_data = ([fit_result['x0'], fit_result['y0']], [fit_result['sigma_x'], fit_result['sigma_y']])
                self.res_queue.put(([fit_result['x0'], fit_result['y0']], [fit_result['sigma_x'], fit_result['sigma_y']]))
            else:
                self.res_queue.put(self.last_valid_data)
        else:
            cam.queue_frame(frame)
        self.is_busy = False

    @pyqtSlot()
    def execute_labrad_trigger(self):
        if self.running and self.trigger_mode == "Labrad":
            if self.is_busy:
                self.log_message.emit("Labrad Trigger Error: Camera is busy (Trigger sent too fast)")
                self.res_queue.put(self.last_valid_data)
                return
                
            try:
                self.is_busy = True
                self.cam.TriggerSoftware.run()
            except Exception as e:
                self.is_busy = False
                self.log_message.emit(f"Labrad Trigger Error: {e}")
                self.res_queue.put(self.last_valid_data)

    @pyqtSlot(dict)
    def update_params(self, new_params):
        try:
            self.cam.stop_streaming()
        except Exception:
            pass

        for key, value in new_params.items():
            try:
                if getattr(self.cam, key).get() != value:
                    getattr(self.cam, key).set(value)
                    self.log_message.emit(f"Updated {key}: {value}")
                    self.params[key] = value
            except Exception as e:
                self.log_message.emit(f"Parameter Update Error {key}: {e}")

        try:
            self.cam.start_streaming(self.handler)
        except Exception as e:
            self.log_message.emit(f"Failed to restart streaming: {e}")

    @pyqtSlot(str, float)
    def update_trigger_mode(self, mode, interval):
        if self.trigger_mode != mode:
            self.trigger_mode = mode
            self.log_message.emit(f"Updated trigger mode: {mode}")
        if self.trigger_interval != interval:
            self.trigger_interval = interval
            self.log_message.emit(f"Updated trigger interval: {interval}")

    @pyqtSlot(bool)
    def update_fitting_enable(self, enabled):
        self.is_fitting = enabled

    def stop_camera(self):
        print(f"Stopping camera {self.cam_id}")
        self.running = False

    def perform_fit(self, imag, method='2d'):
        try:
            if method=="1d":
                proj_x = np.sum(imag, axis=0)
                proj_y = np.sum(imag, axis=1)
                x_axis = np.arange(len(proj_x))
                y_axis = np.arange(len(proj_y))
                
                guess_x = get_initial_guess(x_axis, proj_x, method='1d')
                popt_x, pcov_x = curve_fit(gaussian_1d, x_axis, proj_x, p0=guess_x, maxfev=2000)
                perr_x = np.sqrt(np.diag(pcov_x))
                _, mu_x, sigma_x, _ = popt_x
                err_mu_x = perr_x[1]
                err_sigma_x = perr_x[2]

                guess_y = get_initial_guess(y_axis, proj_y, method='1d')
                popt_y, pcov_y = curve_fit(gaussian_1d, y_axis, proj_y, p0=guess_y, maxfev=2000)
                perr_y = np.sqrt(np.diag(pcov_y))
                _, mu_y, sigma_y, _ = popt_y
                err_mu_y = perr_y[1]
                err_sigma_y = perr_y[2]

                return {
                    "x0": mu_x + self.params.get("OffsetX", 0),
                    "y0": mu_y + self.params.get("OffsetY", 0),
                    "sigma_x": np.abs(sigma_x),
                    "sigma_y": np.abs(sigma_y),
                    "theta": 0,  
                    "x0_error": err_mu_x,
                    "y0_error": err_mu_y,
                    "sigma_x_error": err_sigma_x,
                    "sigma_y_error": err_sigma_y,
                    "theta_error": 0,
                }
                
            elif method=="1d_modulated":
                proj_x = np.sum(imag, axis=0)
                proj_y = np.sum(imag, axis=1)
                x_axis = np.arange(len(proj_x))
                y_axis = np.arange(len(proj_y))
                
                guess_x = get_initial_guess(x_axis, proj_x, method='1d_modulated')
                popt_x, pcov_x = curve_fit(gaussian_1d_modulated, x_axis, proj_x, p0=guess_x, maxfev=2000)
                perr_x = np.sqrt(np.diag(pcov_x))
                _, mu_x, sigma_x, _, phase, _, _ = popt_x
                err_mu_x = perr_x[1]
                err_sigma_x = perr_x[2]
                err_phase = perr_x[4]

                guess_y = get_initial_guess(y_axis, proj_y, method='1d')
                popt_y, pcov_y = curve_fit(gaussian_1d, y_axis, proj_y, p0=guess_y, maxfev=2000)
                perr_y = np.sqrt(np.diag(pcov_y))
                _, mu_y, sigma_y, _ = popt_y
                err_mu_y = perr_y[1]
                err_sigma_y = perr_y[2]

                return {
                    "x0": mu_x + self.params.get("OffsetX", 0),
                    "y0": mu_y + self.params.get("OffsetY", 0),
                    "sigma_x": np.abs(sigma_x),
                    "sigma_y": np.abs(sigma_y),
                    "theta": 0,  
                    "x0_error": err_mu_x,
                    "y0_error": err_mu_y,
                    "sigma_x_error": err_sigma_x,
                    "sigma_y_error": err_sigma_y,
                    "theta_error": 0,
                    "phase": phase, 
                    "phase_error": err_phase,
                }
                
            elif method=="2d":
                height, width = imag.shape[:2]
                if self.fit_params is None:
                    y = np.arange(height)
                    x = np.arange(width)
                    x, y = np.meshgrid(x, y)
                    x0_init = np.average(x, weights=imag)
                    y0_init = np.average(y, weights=imag)
                else:
                    x0_init = self.fit_params["x"]-self.params["OffsetX"]
                    y0_init = self.fit_params["y"]-self.params["OffsetY"]
                    
                roi_size = self.fit_params["roi_size"]
                x_min = max(int(x0_init - roi_size), 0)
                x_max = min(int(x0_init + roi_size), width)
                y_min = max(int(y0_init - roi_size), 0)
                y_max = min(int(y0_init + roi_size), height)
                imag_roi = imag[y_min:y_max, x_min:x_max]
            
                amp_init = np.max(imag_roi)
                sigma_x_init = self.fit_params["sigma_x"]
                sigma_y_init = self.fit_params["sigma_y"]
                theta_init = self.fit_params["theta"]
                offset_init = self.fit_params["offset"]
                
                y = np.arange(y_min,y_max)
                x = np.arange(x_min,x_max)
                x, y = np.meshgrid(x, y)
                xdata = np.vstack((x.ravel(), y.ravel()))
                ydata = imag_roi.ravel()

                p0 = [amp_init, x0_init, y0_init, sigma_x_init, sigma_y_init, theta_init, offset_init]
                lower_bounds = [0, 0, 0, 1, 1, -np.pi/2, -np.inf]
                upper_bounds = [np.inf, width-1, height-1, width, height, np.pi/2, np.inf]
                
                
                popt, pcov = curve_fit(gaussian_2d, xdata, ydata, p0=p0, bounds=(lower_bounds, upper_bounds),max_nfev=60,ftol=0.2,xtol=0.2)
                _, x0, y0, sigma_x, sigma_y, theta, _ = popt
                _, x0_err, y0_err, sigma_x_err, sigma_y_err, theta_err, _ = np.sqrt(np.diag(pcov))
                
                return {
                    "x0": x0+self.params["OffsetX"],
                    "y0": y0+self.params["OffsetY"],
                    "sigma_x": sigma_x,
                    "sigma_y": sigma_y,
                    "theta": theta,
                    "x0_error": x0_err,
                    "y0_error": y0_err,
                    "sigma_x_error": sigma_x_err,
                    "sigma_y_error": sigma_y_err,
                    "theta_error": theta_err,
                }
                
            else:
                self.log_message.emit(f"Fit Method Error: {method}")
                return self.get_empty_fit()
        except Exception as e:
            self.log_message.emit(f"Fit Error: {e}")
            return self.get_empty_fit()

    def get_empty_fit(self):
        keys = ["x0", "y0", "sigma_x", "sigma_y", "theta", 
                "x0_error", "y0_error", "sigma_x_error", "sigma_y_error", "theta_error", "phase", "phase_error"]
        return {k: 0.0 for k in keys}

def gaussian_1d(x, amp, mu, sigma, offset):
    return amp * np.exp(-((x - mu) ** 2) / (2 * sigma ** 2)) + offset

def gaussian_1d_modulated(x, amp, mu, sigma, k, phi, vis, offset):
    envelope = np.exp(-((x - mu) ** 2) / (2 * sigma ** 2))
    interference = vis * (np.cos(k * (x - mu) + phi) ** 2) + (1 - vis)
    return amp * envelope * interference + offset

def gaussian_2d(xy, amp, x0, y0, sigma_x, sigma_y, theta, offset):
    x, y = xy
    x0, y0 = float(x0), float(y0)
    a = (np.cos(theta)**2)/(2*sigma_x**2) + (np.sin(theta)**2)/(2*sigma_y**2)
    b = -(np.sin(2*theta))/(4*sigma_x**2) + (np.sin(2*theta))/(4*sigma_y**2)
    c = (np.sin(theta)**2)/(2*sigma_x**2) + (np.cos(theta)**2)/(2*sigma_y**2)
    return amp * np.exp( - (a*((x-x0)**2) + 2*b*(x-x0)*(y-y0) + c*((y-y0)**2)) ) + offset   

def get_initial_guess(x, data, method):
    if method == "1d":
        margin = max(1, int(len(data) * 0.1))
        offset_guess = np.mean(np.concatenate((data[:margin], data[-margin:])))
        amp_guess = np.max(data) - offset_guess
        clean_data = np.maximum(data - offset_guess, 0)
        total_mass = np.sum(clean_data)
        if total_mass == 0:
            mu_guess = np.mean(x)
        else:
            mu_guess = np.sum(x * clean_data) / total_mass
        if total_mass == 0:
            sigma_guess = len(data) / 2.0
        else:
            sigma_guess = np.sqrt(np.sum(clean_data * (x - mu_guess)**2) / total_mass)
            
        return [amp_guess, mu_guess, sigma_guess, offset_guess]
    
    elif method == "1d_modulated":
        margin = max(1, int(len(data) * 0.1))
        offset_guess = np.mean(np.concatenate((data[:margin], data[-margin:])))
        clean_data = np.maximum(data - offset_guess, 0)
        amp_guess = np.max(clean_data)
        
        total_mass = np.sum(clean_data)
        if total_mass == 0:
            return [0, 0, 1, 0, np.pi/2, 0]
        mu_guess = np.sum(x * clean_data) / total_mass
        sigma_guess = np.sqrt(np.sum(clean_data * (x - mu_guess)**2) / total_mass)

        dx = x[1] - x[0]
        fft_vals = np.abs(np.fft.rfft(clean_data))
        fft_freqs = np.fft.rfftfreq(len(clean_data), d=dx)
        
        if sigma_guess > 0:
            start_idx = int(1.0 / (2 * sigma_guess * (fft_freqs[1] - fft_freqs[0])))
            start_idx = np.clip(start_idx, 1, len(fft_freqs)-1)
        else:
            start_idx = 1
        if start_idx < len(fft_freqs):
            peak_idx = np.argmax(fft_vals[start_idx:]) + start_idx
            k_guess = np.pi * fft_freqs[peak_idx]
        else:
            k_guess = 0.03

        idx_at_center = (np.abs(x - mu_guess)).argmin()
        val_at_center = clean_data[idx_at_center]
        relative_intensity = val_at_center / (amp_guess + 1e-9)
        try:
            phi_guess = np.arccos(np.sqrt(np.clip(relative_intensity, 0, 1)))
        except:
            phi_guess = 1.6

        vis_guess = 0.6

        return [amp_guess, mu_guess, sigma_guess, k_guess, phi_guess, vis_guess, offset_guess]

    else: return None 
 
class MplCanvas(FigureCanvas):
    def __init__(self):
        fig, ax = plt.subplots(1)
        self.fig = fig
        self.ax = ax
        # self.fig.set_tight_layout(True)
        self.fig.subplots_adjust(left=0.05, right=0.9, top=0.95, bottom=0.1)
        super().__init__(self.fig)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.updateGeometry()

class CameraGui(QMainWindow):
    request_params_update = pyqtSignal(dict)
    request_trigger_mode_change = pyqtSignal(str, float)
    request_fitting_enable = pyqtSignal(bool)
    window_closed = pyqtSignal()

    def __init__(self, defaults, info):
        super().__init__()
        self.defaults = defaults
        self.params = defaults.copy()
        self.title = info["title"]
        self.pixel_size = info["pixel size"]
        self.max_width = info["max width"]
        self.max_height = info["max height"]
        
        # database credentials
        url = "http://10.100.1.10:8086"
        token = "yelabtoken"
        self.org = "yelab"
        self.bucket = "sr1_mako_camero" # If bucket not exists, create it from the database UI.
        self.measurement = info["measurement name"]
        self.client = InfluxDBClient(url=url, token=token, org=self.org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.last_upload_time = None
        
        self.base_font_size = 12
        self.base_width = 1100
        self.init_gui()

    def init_gui(self):
        self.setWindowTitle(self.title)
        self.image_id_label = QLabel("Image ID: -")
        self.canvas = MplCanvas()
        self.initial_image()
        
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.image_id_label)
        left_layout.addWidget(self.canvas)
        
        self.fit_label = QLabel("Waiting for data...")
        self.fit_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Labrad", "GUI"])
        self.mode_combo.currentTextChanged.connect(self.on_trigger_mode_change)
        
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.1, 10.0)
        self.interval_spin.setValue(2.0)
        self.interval_spin.setSuffix(" s")
        self.interval_spin.valueChanged.connect(self.on_trigger_mode_change)
        
        self.fit_check = QCheckBox("Enable Fit")
        self.fit_check.setChecked(True)
        self.fit_check.toggled.connect(self.on_fitting_enable)

        # Checkbox to toggle marker visibility
        self.show_marker_check = QCheckBox("Show markers")
        self.show_marker_check.setChecked(True)
        self.fit_check.toggled.connect(self.on_marker_enable)

        # vmax control
        self.vmax_edit = QLineEdit()
        self.vmax_edit.setPlaceholderText("Colorbar vmax (auto if empty)")
        self.vmax_edit.setFixedWidth(120)
        self.vmax_edit.setText("")
        self.vmax_edit.editingFinished.connect(self.edit_vmax)
        self.vmax_user = None  # None means auto, otherwise float
        
        self.gain_box = self.create_spin(0, 40, self.params['Gain'])
        self.exposure_box = self.create_spin(16, 1000000, self.params['ExposureTimeAbs'])
        self.width_box = self.create_spin(1, self.max_width, self.params['Width'])
        self.height_box = self.create_spin(1, self.max_height, self.params['Height'])
        self.offsetx_box = self.create_spin(0, self.max_width, self.params['OffsetX'])
        self.offsety_box = self.create_spin(0, self.max_height, self.params['OffsetY'])
        
        self.width_box.valueChanged.connect(self.update_offsetx_range)
        self.height_box.valueChanged.connect(self.update_offsety_range)
        self.offsetx_box.valueChanged.connect(self.ensure_offsetx_even)
        self.offsety_box.valueChanged.connect(self.ensure_offsety_even)
        
        form = QFormLayout()
        form.addRow("Trigger Mode:", self.mode_combo)
        form.addRow("Trigger Interval:", self.interval_spin)
        form.addRow(self.fit_check)
        form.addRow(self.show_marker_check)
        form.addRow("Colorbar vmax:", self.vmax_edit)
        form.addRow(QLabel(""))
        form.addRow(QLabel("--- Camera Params ---"))
        form.addRow("Gain:", self.gain_box)
        form.addRow("Exposure Time (us):", self.exposure_box)
        form.addRow("Width:", self.width_box)
        form.addRow("Height:", self.height_box)
        form.addRow("Offset X:", self.offsetx_box)
        form.addRow("Offset Y:", self.offsety_box)
        
        btn_layout = QHBoxLayout()
        update_btn = QPushButton("Update Params")
        update_btn.clicked.connect(self.on_param_update)
        reset_btn = QPushButton("Reset Defaults")
        reset_btn.clicked.connect(self.reset_params)
        btn_layout.addWidget(update_btn)
        btn_layout.addWidget(reset_btn)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(100)
        self.log_text.setPlaceholderText("System Log:")
        self.log_text.setFont(QFont("Monospace", 9))
        self.log_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.fit_label)
        right_layout.addLayout(form)
        right_layout.addLayout(btn_layout)
        right_layout.addWidget(QLabel("System Log:"))
        right_layout.addWidget(self.log_text)

        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        right_widget.setMaximumWidth(450)

        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout, stretch=1)
        main_layout.addWidget(right_widget, stretch=0)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
        self.resize(1100, 800)

    def create_spin(self, min_v, max_v, val):
        sb = QSpinBox()
        sb.setRange(min_v, max_v)
        sb.setValue(val)
        return sb

    def on_trigger_mode_change(self):
        mode = self.mode_combo.currentText()
        interval = self.interval_spin.value()
        self.interval_spin.setEnabled(mode == "GUI")
        self.request_trigger_mode_change.emit(mode, interval)

    def on_fitting_enable(self, checked):
        self.request_fitting_enable.emit(checked)
        if not checked:
            self.fit_label.setText("Fitting Disabled")
            self.line1.set_visible(False)
            self.line2.set_visible(False)
            self.ellipse.set_visible(False)
            self.canvas.draw_idle()
    
    def on_marker_enable(self, checked):
        if not checked:
            self.line1.set_visible(False)
            self.line2.set_visible(False)
            self.ellipse.set_visible(False)
            self.canvas.draw_idle()

    def on_param_update(self):
        new_params = {
            "Gain": self.gain_box.value(),
            "ExposureTimeAbs": self.exposure_box.value(),
            "Width": self.width_box.value(),
            "Height": self.height_box.value(),
            "OffsetX": self.offsetx_box.value(),
            "OffsetY": self.offsety_box.value()
        }
        
        self.params.update(new_params)
        self.update_axis()
        self.request_params_update.emit(new_params)

    def reset_params(self):
        self.gain_box.setValue(self.defaults["Gain"])
        self.exposure_box.setValue(self.defaults["ExposureTimeAbs"])
        self.width_box.setValue(self.defaults["Width"])
        self.height_box.setValue(self.defaults["Height"])
        self.offsetx_box.setValue(self.defaults["OffsetX"])
        self.offsety_box.setValue(self.defaults["OffsetY"])
        self.on_param_update()

    def update_axis(self):
        width,height,offsetx,offsety = self.params["Width"],self.params["Height"],self.params["OffsetX"],self.params["OffsetY"]
        self.im.set_extent((0, width, height, 0))
        self.canvas.ax.set_xlim(0, width)
        self.canvas.ax.set_ylim(height, 0)
        xticks = np.linspace(0, width, 6)
        yticks = np.linspace(height, 0, 6)
        self.canvas.ax.set_xticks(xticks)
        self.canvas.ax.set_yticks(yticks)
        self.canvas.ax.set_xticklabels([str(int(x + offsetx)) for x in xticks])
        self.canvas.ax.set_yticklabels([str(int(y + offsety)) for y in yticks])
        
    def edit_vmax(self):
        text = self.vmax_edit.text().strip()
        if text == "":
            self.vmax_user = None
        else:
            try:
                self.vmax_user = float(text)
            except ValueError:
                self.vmax_user = None
                self.vmax_edit.setText("")

    def initial_image(self):
        width = self.params["Width"]
        height = self.params["Height"]
        initial_img = np.zeros((width, height))
        self.im = self.canvas.ax.imshow(initial_img, cmap='plasma', aspect='auto',extent=(0,width,height,0))
        divider = make_axes_locatable(self.canvas.ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        self.cbar = self.canvas.fig.colorbar(self.im, cax=cax)
        self.vmax = 0
        self.canvas.ax.set_xlim(0, width)
        self.canvas.ax.set_ylim(height, 0)
        xticks = np.linspace(0, width, 6)
        yticks = np.linspace(height, 0, 6)
        self.canvas.ax.set_xticks(xticks)
        self.canvas.ax.set_yticks(yticks)
        self.canvas.ax.set_xticklabels([str(int(x + self.params["OffsetX"])) for x in xticks])
        self.canvas.ax.set_yticklabels([str(int(y + self.params["OffsetY"])) for y in yticks])
        self.canvas.ax.set_xlabel("X (pixels)")
        self.canvas.ax.set_ylabel("Y (pixels)")
        self.line1, = self.canvas.ax.plot([], [], color='k', linestyle='--', lw=2, alpha=0.3)
        self.line2, = self.canvas.ax.plot([], [], color='k', linestyle='--', lw=2, alpha=0.3)
        self.ellipse = Ellipse((0, 0), width=0, height=0, angle=0, edgecolor='k', facecolor='none', linestyle='--', lw=2, alpha=0.3)
        self.canvas.ax.add_patch(self.ellipse)
        
    
        
    @pyqtSlot(np.ndarray, int, dict)
    def update_image(self, imag, imag_id, fit_result):
        self.image_id_label.setText(f"Image ID: {imag_id}")
        self.im.set_data(imag)
        
        if self.vmax_user is not None:
            vmax = self.vmax_user
        else:
            vmax = np.max(imag)
        self.im.set_clim(vmin=0, vmax=vmax)
        ticks = np.linspace(0, vmax, 6)
        self.cbar.set_ticks(ticks)
        self.cbar.set_ticklabels([f"{tick:.0f}" for tick in ticks])
        self.vmax = vmax
        
        x0 = fit_result['x0']-self.params["OffsetX"]
        y0 = fit_result['y0']-self.params["OffsetY"]
        sigma_x = fit_result['sigma_x']
        sigma_y = fit_result['sigma_y']
        theta = fit_result['theta']
        
        if self.fit_check.isChecked():
            fit_text = (
                "<html><head/><body>"
                "<p style='line-height:120%'>"
                "<b>Gaussian Fit:</b><br>"
                "x<sub>0</sub> = {:.3f} &plusmn; {:.3f}<br>"
                "y<sub>0</sub> = {:.3f} &plusmn; {:.3f}<br>"
                "&sigma;<sub>x</sub> = {:.3f} &plusmn; {:.3f}<br>"
                "&sigma;<sub>y</sub> = {:.3f} &plusmn; {:.3f}<br>"
                "&theta; = {:.3f}&deg; &plusmn; {:.3f}&deg;"
                "</p></body></html>"
            ).format(
                fit_result['x0']*self.pixel_size, fit_result["x0_error"]*self.pixel_size,
                fit_result['y0']*self.pixel_size, fit_result["y0_error"]*self.pixel_size,
                sigma_x*self.pixel_size, fit_result["sigma_x_error"]*self.pixel_size,
                sigma_y*self.pixel_size, fit_result["sigma_y_error"]*self.pixel_size,
                theta * 180 / np.pi, fit_result["theta_error"] * 180 / np.pi
            )
            self.fit_label.setText(fit_text)
                
            if self.show_marker_check.isChecked():
                dx1 = sigma_x * np.cos(theta) * 2
                dy1 = sigma_x * np.sin(theta) * 2
                dx2 = -sigma_y * np.sin(theta) * 2
                dy2 = sigma_y * np.cos(theta) * 2
                self.line1.set_data([x0 - dx1, x0 + dx1], [y0 + dy1, y0 - dy1])
                self.line2.set_data([x0 - dx2, x0 + dx2], [y0 + dy2, y0 - dy2])
                self.ellipse.set(center=(x0, y0), width=2*sigma_x, height=2*sigma_y, angle=-theta*180/np.pi)
                self.line1.set_visible(True)
                self.line2.set_visible(True)
                self.ellipse.set_visible(True)
            else:
                self.line1.set_visible(False)
                self.line2.set_visible(False)
                self.ellipse.set_visible(False)
        else:
            self.fit_label.setText("Fitting Disabled")
            self.line1.set_visible(False)
            self.line2.set_visible(False)
            self.ellipse.set_visible(False)
        
        self.canvas.draw_idle()
        # self.save_data(fit_result)
        self.upload_data(fit_result)
        
    def save_data(self, fit_result):
        """
        Save current data and parameters to the log file.
        
        Args:
            fit_result (dict): Gaussian fit parameters
        """
        # Initialize logging system to record parameters and fit results
        try:
            now = time.time()
            if self.last_upload_time is None or (now - self.last_upload_time) >= 10:
                now = datetime.now()
                year_str = now.strftime("%Y")
                month_str = now.strftime("%m")
                date_str = now.strftime("%Y%m%d")
                base_dir = os.path.dirname(__file__)
                target_dir = os.path.join(base_dir, self.measurement, year_str, month_str)

                if not os.path.exists(target_dir):
                    os.makedirs(target_dir, exist_ok=True)

                log_filename = os.path.join(target_dir, f"{date_str}.txt")
                file_exists = os.path.isfile(log_filename)
                if hasattr(self, 'log_file') and self.log_file:
                    if not self.log_file.closed and getattr(self, 'log_filename', None) != log_filename:
                        self.log_file.close()
                        self.log_filename = log_filename
                        self.log_file = open(self.log_filename, "a", encoding="utf-8")
                else:
                    self.log_filename = log_filename
                    self.log_file = open(self.log_filename, "a", encoding="utf-8")


                # Write header to log file if it's a new file
                if not file_exists:
                    header = [
                        "time", "x0", "y0", "theta_err", "x0_error", "y0_error", "theta_error"
                    ]
                    self.log_file.write("\t".join(header) + "\n")
                    self.log_file.flush()
                    
                time_str = now.strftime("%H:%M:%S")
                data = [
                    time_str,
                    f"{fit_result['x0']*self.pixel_size:.3f}",
                    f"{fit_result['y0']*self.pixel_size:.3f}",
                    f"{fit_result['theta']:.3f}",
                    f"{fit_result['x0_error']*self.pixel_size:.3f}",
                    f"{fit_result['y0_error']*self.pixel_size:.3f}",
                    f"{fit_result['theta_error']:.3f}",
                ]
                self.log_file.write("\t".join(data) + "\n")
                self.log_file.flush()
            else:
                pass
        except Exception as e:
            self.show_log(self, e)
        
    def upload_data(self, fit_result):
        """
        Save current data and parameters to YeMonitor every 10s.
        
        Args:
            fit_result (dict): Gaussian fit parameters
        """
        try:
            now = time.time()
            if self.last_upload_time is None or (now - self.last_upload_time) >= 10:
                if self.title=="Mako Lattice Far":
                    message = (
                        f"{self.measurement},host=myhost "
                        f"x0={fit_result['x0']*self.pixel_size},"
                        f"y0={fit_result['y0']*self.pixel_size},"
                        f"theta={fit_result['theta']},"
                        f"phase={fit_result['phase']},"
                        f"x0_error={fit_result['x0_error']*self.pixel_size},"
                        f"y0_error={fit_result['y0_error']*self.pixel_size},"
                        f"theta_error={fit_result['theta_error']},"
                        f"phase_error={fit_result['phase_error']}"
                    )
                else:
                    message = (
                        f"{self.measurement},host=myhost "
                        f"x0={fit_result['x0']*self.pixel_size},"
                        f"y0={fit_result['y0']*self.pixel_size},"
                        f"theta={fit_result['theta']},"
                        f"x0_error={fit_result['x0_error']*self.pixel_size},"
                        f"y0_error={fit_result['y0_error']*self.pixel_size},"
                        f"theta_error={fit_result['theta_error']}"
                    )
                self.write_api.write(self.bucket, self.org, message)
                self.last_upload_time = now
            else:
                pass
        except Exception as e:
            self.show_log(self, e)
        
    def closeEvent(self, event):
        print("Closing window, stopping camera...")
        if hasattr(self, "log_file") and self.log_file:
            self.log_file.close()
        if hasattr(self, "client") and self.client:
            self.client.close()
        self.window_closed.emit()
        event.accept()
        super().closeEvent(event)

    def resizeEvent(self, event):
        new_width = event.size().width()
        scale_factor = new_width / self.base_width
        
        new_font_size = int(self.base_font_size * scale_factor)
        new_font_size = max(8, min(new_font_size, 20))
        font = QApplication.font()
        font.setPointSize(new_font_size)
        QApplication.setFont(font)
        
        super().resizeEvent(event)

    @pyqtSlot(str)
    def show_log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if "Error" in msg or "Exception" in msg:
            formatted_msg = f"<span style='color:red'>[{timestamp}] {msg}</span>"
        else:
            formatted_msg = f"<span style='color:white'>[{timestamp}] {msg}</span>"
        self.log_text.append(formatted_msg)
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        print(f"[{timestamp}] {msg}")
        
    def update_offsetx_range(self):
        """
        Update the range of OffsetX spin box based on current Width value.
        Ensures OffsetX + Width doesn't exceed maximum camera width (1936).
        """
        width = self.width_box.value()
        max_offsetx = self.max_width - width
        self.offsetx_box.setRange(0, max_offsetx)
        if self.offsetx_box.value() > max_offsetx:
            self.offsetx_box.setValue(max_offsetx)

    def update_offsety_range(self):
        """
        Update the range of OffsetY spin box based on current Height value.
        Ensures OffsetY + Height doesn't exceed maximum camera height (1216).
        """
        height = self.height_box.value()
        max_offsety = self.max_height - height
        self.offsety_box.setRange(0, max_offsety)
        if self.offsety_box.value() > max_offsety:
            self.offsety_box.setValue(max_offsety)
    
    def ensure_offsetx_even(self):
        """
        Ensure OffsetX value is even (required by some camera hardware).
        """
        value = self.offsetx_box.value()
        if value % 2 != 0:
            self.offsetx_box.setValue(value - 1)
    
    def ensure_offsety_even(self):
        """
        Ensure OffsetY value is even (required by some camera hardware).
        """
        value = self.offsety_box.value()
        if value % 2 != 0:
            self.offsety_box.setValue(value - 1)

class LatticeMaster(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mako Lattice Control System")
        self.resize(1100, 800)

        self.base_width = 1100
        self.base_font_size = 12

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.setMovable(True)
        
        self.tabs.setStyleSheet("QTabBar::tab { height: 40px; width: 150px; font-size: 14px; }")
        self.setCentralWidget(self.tabs)

        self.adjust_font_size()

    def add_camera_gui(self, gui):
        self.tabs.addTab(gui, gui.title)

    def resizeEvent(self, event):
        self.adjust_font_size()
        super().resizeEvent(event)

    def adjust_font_size(self):
        current_width = self.width()
        
        scale_factor = current_width / self.base_width
        
        new_font_size = int(self.base_font_size * scale_factor)
        
        new_font_size = max(10, min(new_font_size, 16))
        
        font = QApplication.font()
        font.setPointSize(new_font_size)
        QApplication.setFont(font)

    def closeEvent(self, event):
        print("Main window closing, cleaning up tabs...")
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if widget:
                widget.close()
        event.accept()

class MakoLattice():
    def __init__(self):
        cam_id_far = "DEV_000F315E443A"
        defaults_far = {
                "Gain": 0,              # Camera gain setting
                "ExposureTimeAbs": 120, # Exposure time in microseconds
                "OffsetX": 500,          # X offset for ROI
                "OffsetY": 50,          # Y offset for ROI
                "Width": 1300,            # ROI width
                "Height": 900,           # ROI height
                # "AcquisitionFrameRateAbs": 0.5,
            }
        info_far = {
            "title": "Mako Lattice Far",
            "pixel size": 5.86,
            "max width": 1936,
            "max height": 1216,
            "measurement name": "lattice_far",
            "fit_method": "1d_modulated"
        }

        cam_id_near = "DEV_000F315BA562"
        defaults_near = {
                "Gain": 0,              # Camera gain setting
                "ExposureTimeAbs": 20, # Exposure time in microseconds
                "OffsetX": 0,          # X offset for ROI
                "OffsetY": 200,          # Y offset for ROI
                "Width": 680,            # ROI width
                "Height": 600,           # ROI height
                # "AcquisitionFrameRateAbs": 0.5,
            }
        info_near = {
            "title": "Mako Lattice Near",
            "pixel size": 3.75,
            "max width": 1292,
            "max height": 964,
            "measurement name": "lattice_near",
            "fit_method": "1d"
        }
        
        self.master_window = LatticeMaster()
        self.camera_near, self.gui_near = self.init_mako_lattice(cam_id_near, defaults_near, info_near)
        self.master_window.add_camera_gui(self.gui_near)
        time.sleep(0.1)
        self.camera_far, self.gui_far = self.init_mako_lattice(cam_id_far, defaults_far, info_far)
        self.master_window.add_camera_gui(self.gui_far)
        self.master_window.show()

    def init_mako_lattice(self, cam_id, defaults, info):
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        fit_method = info["fit_method"]
        
        print(f"Initializing camera {info['title']}...")
        camera = MakoCamera(cam_id, defaults, fit_method)
        print(f"Initializing GUI {info['title']}...")
        gui = CameraGui(defaults, info)
        thread = QThread()
        camera.moveToThread(thread)
        thread.started.connect(camera.start_streaming)
        camera.data_ready.connect(gui.update_image)
        gui.request_fitting_enable.connect(camera.update_fitting_enable)
        gui.request_trigger_mode_change.connect(camera.update_trigger_mode)
        gui.request_params_update.connect(camera.update_params)
        camera.log_message.connect(gui.show_log)

        def cleanup():
            print(f"Starting cleanup {info["title"]}...")
            camera.stop_camera()
            
            thread.quit()
            if not thread.wait(1000):
                print("Warning: Thread did not finish cleanly, forcing termination.")
                thread.terminate()
            else:
                print("Camera thread stopped successfully.")

        gui.window_closed.connect(cleanup)
        app.aboutToQuit.connect(cleanup)
        thread.start()
        return camera, gui


    def Acquire(self, camera):
        while not camera.res_queue.empty():
            try:
                camera.res_queue.get_nowait()
            except queue.Empty:
                break
            
        camera.labrad_trigger_signal.emit()
        try:
            result = camera.res_queue.get(timeout=1.0)
            return result 
        except queue.Empty:
            camera.log_message.emit("Acquisition Error: Queue Timeout")
            return [0,0], [0,0]
            
        except Exception as e:
            camera.log_message.emit(f"Acquisition Error: {type(e).__name__} - {e}")
            return [0,0], [0,0]
    