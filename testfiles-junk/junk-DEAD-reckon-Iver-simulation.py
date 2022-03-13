import datetime
import logging
import threading
import tkinter as tk
# from tkinter import filedialog
# from queue import Queue
import serial
import sys
import time
from time import monotonic
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from geographiclib.geodesic import Geodesic

sys.path.append("../AVSP")
from AVSP.artgallery import artgallery as ag
from AVSP.supportingfiles import gnssSupport, funcg, IverSupport

# Set up Logging
start_time = datetime.datetime.now().strftime("%Y%m%d-%H%M")
logger = logging.getLogger(__name__)  # set a logger
logger.setLevel(logging.DEBUG)  # set the level
formatter = logging.Formatter('%(asctime)s;%(name)s;%(levelname)s;%(message)s')  # logging format

# file_handler = logging.FileHandler('AVSP-' + start_time + '.log')  # Name of the file to save
# file_handler.setLevel(logging.DEBUG)
# file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)

# logger.addHandler(file_handler)  # save in the file
logger.addHandler(stream_handler)  # Print on the console


class DeadReckon:
    """It returns next position from the current position. It takes  """

    def __init__(self):
        self.geod = Geodesic(6378388, 1 / 297.0)
        self.current_position = {'Latitude': [], 'Longitude': []}
        self.current_time = monotonic()

    def dead_reckon(self, target_waypoint: tuple, speed_m_per_sec: float):
        # current_lat, current_lng = current_position
        wp_lat, wp_lng = target_waypoint
        current_monotonic_time = monotonic()
        tme_dif = current_monotonic_time - self.current_time
        h = self.geod.Inverse(self.current_position['Latitude'], self.current_position['Longitude'], wp_lat, wp_lng)
        position = self.geod.Direct(self.current_position['Latitude'], self.current_position['Longitude'],
                                    azi1=h['azi1'], s12=speed_m_per_sec * tme_dif)
        self.current_position['Latitude'] = position['lat2']
        self.current_position['Longitude'] = position['lon2']
        self.current_time = current_monotonic_time


# now = monotonic()
# dr = DeadReckon().dead_reckon((30.36099, -89.63138), (30.35099, -89.63138), 0, now)
# print(dr)

def read_mission_file(file):
    waypoints = file
    return waypoints


class Iver(DeadReckon):
    def __init__(self, current_position: tuple, waypoints, auv='3089', comport_rf='COM11', comport_ac='COM13'):
        DeadReckon.__init__(self)
        self.auv = auv
        self.ser_rf = serial.Serial(comport_rf, baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1, xonxoff=0)
        self.ser_ac = serial.Serial(comport_ac, baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1, xonxoff=0)
        self.current_position = current_position
        self.waypoints = waypoints
        self.wp_nxt = '1'
        self.omw_clear = False
        self.geod = Geodesic(6378388, 1 / 297.0)

    # def iver_status(self):
    #     # print (nxt_wp)
    #     # 1 m/s = 1.94384 Knot
    #     iver_sta = '$OSI,8080808080,S,' + self.wp_nxt + ',' + \
    #                str(self.current_position['Latitude']) + ',' + str(self.current_position['Longitude']) \
    #                + ',' + str(self.current_position['speed'] * 1.94384) + ',' + str(self.disnc_remaining) \
    #                + ',N,0.000,P0,-1.4743,,0,292.5,0.0,94.3,False,IVER3-3089,2.5,True,False ' + '*'
    #     return '$AC;IVER3-' + self.auv + ';' + iver_sta + IverSupport.check_sum(iver_sta) + '\r\n'
    #
    # def read_comports(self):
    #     while True:
    #         # print('Status: RF: {}, AC {}'.format(self.send_through_rf, self.send_through_ac))
    #         try:
    #             if (self.send_through_rf and self.ser_rf.inWaiting() > 0) or (
    #                     self.send_through_ac and self.ser_ac.inWaiting() > 0):
    #                 received_data_through = 'RF' if self.ser_rf.inWaiting() > 0 else 'AC'
    #                 read_com = self.ser_rf.readline().decode().strip() if received_data_through == 'RF' else self.ser_ac.readline().decode().strip()
    #                 print(datetime.datetime.now(), ':received through: ', received_data_through, read_com)
    #                 # print('Status: RF: {}, AC {}', self.send_through_rf, self.send_through_ac)
    #                 if functions.received_stream(read_com) == 'osd' and functions.osd_req_recvd(read_com) == 0:
    #                     print(datetime.datetime.now(), ": Sending current Status through : ", received_data_through)
    #                     ser_rf.write(self.iver_status().encode()) if received_data_through == 'RF' else ser_ac.write(
    #                         self.iver_status().encode())
    #                     ser_rf.write(self.osd_ACK().encode()) if received_data_through == 'RF' else ser_ac.write(
    #                         self.osd_ACK().encode())
    #                     # print("Time write:{} sec".format(time.perf_counter() - toc_CS))
    #                 elif functions.received_stream(read_com) == 'omw' and functions.omw_req_recvd(read_com) == 0:
    #                     omw_rec = read_com.split(";")[2].split(',')
    #                     ser_rf.write(self.omw_Ack().encode()) if received_data_through == 'RF' else ser_ac.write(
    #                         self.omw_Ack().encode())
    #                     print(datetime.datetime.now(), ': Sending OMW acknowledgement through :', received_data_through,
    #                           self.omw_Ack())
    #                     if re.search('CLEAR', read_com):
    #                         self.q_wp_omw.queue.clear()
    #                         self.omw_clear = True
    #                         self.q_wp_omw.put({'lat': float(omw_rec[2]), 'lon': float(omw_rec[3]),
    #                                            'speed': float(omw_rec[7])})
    #                     else:
    #                         self.q_wp_omw.put({'lat': float(omw_rec[2]), 'lon': float(omw_rec[3]),
    #                                            'speed': float(omw_rec[7])})
    #             else:
    #                 time.sleep(0.5)
    #         except Exception as e:
    #             print(" Exception raised", e)
    #             continue
    #
    # def osd_ack(self):
    #     return '$AC;IVER3-' + self.auv + ';$ACK,8,0,0*5D' + '\r\n'
    #
    # def omw_ack(self):
    #     ack = '$ACK,16,0,0*'
    #     return '$AC;IVER3-' + self.auv + ';' + ack + IverSupport.check_sum(ack) + '\r\n'

    def run(self):
        print(datetime.datetime.now(), ': started')
        wp_lat, wp_lng, wp_speed = 30.360990000000005, -89.63138, 1.5
        self.current_position = {'Latitude': wp_lat, 'Longitude': wp_lng}
        while True:
            t_start = monotonic()
            # speed_i *= 0.51  # * 1 knot = 0.514 m/s
            self.dead_reckon((wp_lat, wp_lng), wp_speed)
            print(self.current_position)

            dt = monotonic() - t_start
            time.sleep(0.5 - dt)


class PlotGeotif(threading.Thread):
    """Plots GeoTif as background"""

    def __init__(self, gal: ag.Gallerist):
        self.gal = gal
        threading.Thread.__init__(self, daemon=True)
        self.start()

    def run(self):
        """Work in progress..."""
        satimage = ag.GeoTifArtist(self.gal, label='Sat plot', zorder=5, alpha=1, add_artist_to_init_func=True)
        # satimage.append_data_to_artist('AVSP/resources/maps/Cat_Island_Low_2.tif')
        satimage.append_data_to_artist('AVSP/resources/maps/Stennis_QW.tif')

        # noaachart = ag.GeoTifArtist(self.gal, label='Cat Island ENC', zorder=6, alpha=0.6, add_artist_to_init_func=True)
        # noaachart.append_data_to_artist('AVSP/resources/maps/Cat_Island_ENC.tif')

        satimage.set_xlim(satimage.geotif_xlim[0], satimage.geotif_xlim[1])
        satimage.set_ylim(satimage.geotif_ylim[0], satimage.geotif_ylim[1])

        while True:
            time.sleep(10)


class StopStartRFAC:
    def __init__(self, stop_rf_ac):
        self.stop_rf_ac = stop_rf_ac
        self.stop_rf_ac = True

    def stop_start(self):
        if self.stop_rf_ac:
            self.stop_rf_ac = False
        elif not self.stop_rf_ac:
            self.stop_rf_ac = True
        return self.stop_rf_ac


def _quit():
    root.quit()
    root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    root.title("Iver-simulation")
    fig = plt.Figure(figsize=(5, 4), dpi=100)
    ax = fig.add_subplot(111)

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    toolbar = NavigationToolbar2Tk(canvas, root)

    button_quit = tk.Button(master=toolbar, text="Quit", command=_quit)
    button_quit.pack(side="right")

    # send_through_rf = True
    # button_RF = tk.Button(master=toolbar, text='RF', command=rf)
    # button_RF.pack(side="right")
    #
    # button_AC = tk.Button(master=toolbar, text='AC', command=ac)
    # button_AC.pack(side="right")

    gal = ag.Gallerist(ax, fig, interval=100)

    PlotGeotif(gal)

    # file = r'AVSP\resources\logfiles\CAT3-IVER3-3089.csv'
    # file = r'AVSP\resources\logfiles\ssc-wamv-log.csv'


    tk.mainloop()
