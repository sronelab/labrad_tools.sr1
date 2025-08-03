
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import matplotlib
from scipy.optimize import curve_fit
import pickle
import sys
import os
import datetime
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

print("This script uses python 3. Check the version below.")
print("python version: " + sys.version)

font = {'family' : 'DejaVu Sans',
        'weight' : 'normal',
        'size'   : 16}

matplotlib.rc('font', **font)

fig = plt.figure(figsize = (12, 12), num = 'Camera live monitor')

ax1 = fig.add_subplot(2,1,1)
ax2 = fig.add_subplot(2,1,2)

oldata = None

#Define the Gaussian function
def gauss(x, H, A, x0, sigma):
    return H + A * np.exp(-(x - x0) ** 2 / (2 * sigma ** 2))

#Divide by 0 protection from internet
def div0( a, b ):
    """ ignore / 0, div0( [-1, 0, 1], 0 ) -> [0, 0, 0] """
    with np.errstate(divide='ignore', invalid='ignore'):
        c = np.true_divide( a, b )
        c[ ~ np.isfinite( c )] = 0  # -inf inf NaN
    return c

def animate(i):
    # file_name = r'/home/srgang/J/data/andor_live.pickle'
    dir_name = os.path.dirname(__file__)
    file_name = os.path.join(dir_name, "andor_live.pickle")
    try:
        with open(file_name, "rb") as file:
            data = pickle.load(file)

        # do nothing if data == oldata
        global oldata
        if data == oldata:
            print("no new data")
            return
        bg = np.array(data['bg'])
        gnd = np.array(data['g']) - bg
        exc = np.array(data['e'])- bg
        tot = gnd + exc

        # frac = np.nan_to_num(np.divide( (exc - bg), (exc + gnd - 2*bg)))

        frac = div0((exc),(gnd + exc))

        x = np.linspace(0, 512*6*1e-3, num = 512)
        xpix = np.linspace(0, 512, num = 512)

        # Finding <x> and Var[x] for the initial guess.
        # p0 = [0.0, np.max(tot), np.average(x, weights=tot), np.sqrt(np.average(x**2, weights=tot) - np.average(x, weights=tot)**2)]
        pfit, pfitcov = curve_fit(gauss, xpix, tot, p0=[0.0, 20.0, 256.0, 50.0])
        
        Ntot = (np.sum(exc[0:-1]) + np.sum(gnd[0:-1]))/10

        
        # Send data to the database  
        token = 'yelabtoken'
        org = 'yelab'
        bucket = 'data_logging'
        with InfluxDBClient(url="http://yesnuffleupagus.colorado.edu:8086", token=token, org=org, debug=False) as client:
            try:
                write_api = client.write_api(write_options=SYNCHRONOUS)
                write_api.write(bucket, org, "Andor,Area=Integrated Ntot={}".format(Ntot))
            except:
                print("Error uploading to influxdb")

        sites_per_pixel = 6/0.813*2
        ax1.clear()
        ax1.plot(x, gauss(xpix, *pfit)/10/sites_per_pixel, ls='--', alpha = 0.5, label = "tot-fit", color= "black")
        ax1.axvline((pfit[2] + 1.5*pfit[3])*6*1e-3, ls = "--", color= "black")
        ax1.axvline((pfit[2] - 1.5*pfit[3])*6*1e-3, ls = "--", color= "black")
        ax1.fill_between(x,  bg/10/sites_per_pixel, label = "background", color="C2", lw = 2, alpha=0.7)
        ax1.fill_between(x, gnd/10/sites_per_pixel, label = "$^1 S _0, |g\\rangle$", color="C0", lw = 2, alpha=0.7)
        ax1.fill_between(x,  exc/10/sites_per_pixel, label = "$^3 P_0, |e\\rangle$", color="C1", lw = 2, alpha=0.7)
        ax1.plot(x, tot/10/sites_per_pixel, color="black", label = "$N_{tot }$", lw = 2, alpha=1)
        ax1.legend(bbox_to_anchor=(1.05, 1.0), loc='upper left')
        ax1.set_ylabel("Atoms/ lattice site",)
        ax1.set_xlabel("z [mm]")
        ax1.grid()
        ax1.set_title("$N_{tot}$: " + str(int(Ntot))+", Center = "+str(np.round((pfit[2])*6*1e-3, decimals  = 2))+" mm, $\\sigma$ = "+str(np.round((pfit[3])*6*1e-3, decimals  = 2))+" mm",
        fontsize=30
        )
        ax1.set_xlim([np.min(x), np.max(x)])

        # ax1.set_ylim([-1, 100])
        mean_frac = np.mean(exc[0:-1]) / (np.mean(exc[0:-1]) + np.mean(gnd[0:-1]))
        ax2.clear()
        ax2.plot(x, frac, ls = "none", marker = '.', label="data")
        N = 11
        ax2.plot(x, np.convolve(frac, np.ones(N)/N)[int((N-1)/2):-int((N-1)/2)], color="C0", alpha=0.5, label="box. avg.")
        ax2.set_title("$\\langle \\rho^{ee}(z)\\rangle_{0 mm}^{2 mm}$: " + str(np.round(mean_frac, decimals=4)),
        fontsize=30,  )
        ax2.set_ylabel("$\\rho^{ee}$")
        ax2.axvline((pfit[2] + 1.5*pfit[3])*6*1e-3, ls = "--",color= "black")
        ax2.axvline((pfit[2] - 1.5*pfit[3])*6*1e-3, ls = "--", color= "black")
        ax2.set_xlabel("z [mm]")
        ax2.set_ylim([-0.1, 1.1])
        ax2.grid()
        ax2.set_xlim([np.min(x), np.max(x)])
        ax2.legend(bbox_to_anchor=(1.05, 1.0), loc='upper left')

        fig.tight_layout()

        oldata = data

    except:
        print("wait")

ani = animation.FuncAnimation(fig, animate, interval=1234)
plt.show()