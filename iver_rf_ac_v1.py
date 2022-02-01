""" Read com ports RF and AC"""
import datetime
import socket
import threading
import tkinter as tk
from queue import Queue
import serial
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib import pyplot as plt
import time
import logging
import funciver
import funcgnss
import artgallery as ag

filepath = r"C:\Log_files"
time_now = datetime.datetime.now()
fileName = filepath + '\\' + "log-IVER-WAMv" + str(time_now.year) + str(time_now.month) + str(time_now.day) + \
           str(time_now.hour) + str(time_now.minute) + ".txt"
log_file = open(fileName, "a")
q_log = Queue()

TIMEOUT_RF = 1
TIMEOUT_AC = 1
rf_port, ac_port = 'COM2', 'COM5'
# rf_port, ac_port = 'COM4', 'COM5'
# rf_port = str(input('RF COMPort: '))  # 'COM2'
# ac_port = str(input('AC COMPort: '))  # 'COM5'

ser_rf = serial.Serial(rf_port, baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=TIMEOUT_RF, xonxoff=0)
ser_ac = serial.Serial(ac_port, baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=TIMEOUT_AC, xonxoff=0)

iver = '3089'

send_through_rf_every = 2  # int(input('How often send OSD through RF in sec: '))
send_through_ac_every = 25  # int(input('How often send OSD through AC in sec: '))

# UDP_IP = "192.168.168.3"
# UDP_PORT = 5014

UDP_IP = 'localhost'
UDP_PORT = 10000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((UDP_IP, UDP_PORT))


class LeadV(threading.Thread):
    def __init__(self, gal: ag.Gallerist):
        self.gal = gal
        threading.Thread.__init__(self, daemon=True)

    def run(self):
        line_artist = ag.LineArtist(self.gal, label='WAMv', c='y')
        while True:
            data, addr = sock.recvfrom(1350)  # buffer size is 1024
            data = data.decode()
            print(datetime.datetime.now(), ':WAMv data received:', data)
            if funcgnss.gpglldecode(data) is not None:
                coordinates= funcgnss.gpglldecode(data)
                lat_w_c = coordinates['Lat_dd']
                lng_w_c = coordinates['Lng_dd']
                line_artist.append_data_to_artist((lng_w_c, lat_w_c))
                q_log.put([datetime.datetime.now().strftime("%H:%M:%S:%f"), ': WAMV: ', data])


class ReadRf(threading.Thread):
    def __init__(self, gal: ag.Gallerist):
        self.gal = gal
        threading.Thread.__init__(self, daemon=True)

    def run(self):
        iver_rf_scatter = ag.ScatterArtist(self.gal, label='IVER-RF', c='r', marker='o')
        ser_rf.reset_input_buffer()
        send_through_rf()
        osi_rec, osd_ak = 0, 0
        while True:
            try:
                frm_iver = ser_rf.readline().decode()
                if len(frm_iver) > 1:
                    q_log.put([datetime.datetime.now().strftime("%H:%M:%S.%f"), ': RF: ', frm_iver])
                    if funciver.received_stream(frm_iver) == 'osi':
                        osi_return = funciver.osi(frm_iver)
                        if osi_return is not None:
                            print(datetime.datetime.now(), ': RF:', osi_return)
                            # print(datetime.datetime.now(), ': RF: lat:', osi_return['Latitude'],
                            #       'lng:', osi_return['Longitude'], ', spd:', osi_return['Speed'],
                            #       ', Bat:', osi_return['Battery'], ', nxtWP:', osi_return['NextWp'],
                            #       ', DisNxt WP: ', osi_return['DistanceToNxtWP'])
                            iver_rf_scatter.append_data_to_artist((osi_return['Longitude'], osi_return['Latitude']))
                            q_log.put([datetime.datetime.now().strftime("%H:%M:%S:%f"), ':', osi_return])
                            print(datetime.datetime.now(), f': OSI received RF: {osi_rec} / requested: {rf_i}')
                            osi_rec += 1
                    elif funciver.received_stream(frm_iver) == 'ACK_WITHOUT_ERROR' or 'ACK_WITH_ERROR':
                        q_log.put([datetime.datetime.now().strftime("%H:%M:%S:%f"), ':', 'OSD Ack RF', osd_ak])
                        print(datetime.datetime.now(), ': OSI Ack received RF ', osd_ak)
                        osd_ak += 1
            except Exception as e:
                q_log.put([datetime.datetime.now().strftime("%H:%M:%S:%f"), ':', e])
                ser_rf.reset_input_buffer()
                continue


class ReadAc(threading.Thread):
    def __init__(self, gal: ag.Gallerist):
        self.gal = gal
        threading.Thread.__init__(self, daemon=True)

    def run(self):
        iver_ac_scatter = ag.ScatterArtist(self.gal, label='IVER-RF', c='r', marker='o')
        ser_ac.reset_input_buffer()
        send_through_ac()
        osi_rec, osd_ak = 0, 0
        while True:
            try:
                frm_iver = ser_ac.readline().decode()
                if len(frm_iver) > 1:
                    q_log.put([datetime.datetime.now().strftime("%H:%M:%S.%f"), ': AC: ', frm_iver])
                    if funciver.received_stream(frm_iver) == 'osi':
                        osi_return = funciver.osi(frm_iver)
                        if osi_return is not None:
                            print(datetime.datetime.now(), ': AC: lat:', osi_return)
                            # print(datetime.datetime.now(), ': AC: lat:', osi_return['Latitude'],
                            #       'lng:', osi_return['Longitude'], ', spd:', osi_return['Speed'],
                            #       ', Bat:', osi_return['Battery'], ', nxtWP:', osi_return['NextWp'],
                            #       ', DisNxt WP: ', osi_return['DistanceToNxtWP'])
                            iver_ac_scatter.append_data_to_artist((osi_return['Longitude'], osi_return['Latitude']))
                            q_log.put([datetime.datetime.now().strftime("%H:%M:%S:%f"), ':', osi_return])
                            print(datetime.datetime.now(), f': OSI received RF: {osi_rec} / requested: {rf_i}')
                            osi_rec += 1
                    elif funciver.received_stream(frm_iver) == 'ACK_WITHOUT_ERROR' or 'ACK_WITH_ERROR':
                        q_log.put([datetime.datetime.now().strftime("%H:%M:%S:%f"), ':', 'OSD Ack RF', osd_ak])
                        print(datetime.datetime.now(), ': OSI Ack received RF ', osd_ak)
                        osd_ak += 1
            except Exception as e:
                q_log.put([datetime.datetime.now().strftime("%H:%M:%S:%f"), ':', e])
                ser_ac.reset_input_buffer()
                continue


rf_i = 0


def send_through_rf():
    # send_through_ac_every = 15
    inst_snd = '$AC;Iver3-' + iver + ';' + '$' + funciver.osd() + '\r\n'
    ser_rf.reset_output_buffer()
    ser_rf.write(inst_snd.encode())
    global rf_i
    print(datetime.datetime.now(), ': Sending through RF: ', rf_i)
    q_log.put([datetime.datetime.now().strftime("%H:%M:%S:%f"), ': send trough RF: ', rf_i])
    rf_i += 1
    threading.Timer(send_through_rf_every, send_through_rf).start()


ac_i = 0


def send_through_ac():
    # send_through_ac_every = 25
    inst_snd = '$AC;Iver3-' + iver + ';' + '$' + funciver.osd() + '\r\n'
    ser_ac.reset_output_buffer()
    ser_ac.write(inst_snd.encode())
    global ac_i
    print(datetime.datetime.now(), ': Sending through AC: ', ac_i)
    q_log.put([datetime.datetime.now().strftime("%H:%M:%S:%f"), ': send trough AC: '])
    ac_i += 1
    threading.Timer(send_through_ac_every, send_through_ac).start()


class PlotGeotif(threading.Thread):
    """Plots GeoTif as backgournd"""
    def __init__(self, gal: ag.Gallerist):
       self.gal = gal
       threading.Thread.__init__(self, daemon=True)

    def run(self):
        """Work in progress..."""
        satimage = ag.GeoTifArtist(self.gal, label='Sat plot', zorder=5, alpha=1, add_artist_to_init_func=True)
        satimage.append_data_to_artist('Cat_Island_Low_2.tif')

        noaachart = ag.GeoTifArtist(self.gal, label='Cat Island ENC', zorder=6, alpha=0.6, add_artist_to_init_func=True)
        noaachart.append_data_to_artist('Cat_Island_ENC.tif')

        satimage.set_xlim(satimage.geotif_xlim[0], satimage.geotif_xlim[1])
        satimage.set_ylim(satimage.geotif_ylim[0], satimage.geotif_ylim[1])

        while True:
            time.sleep(10)


def log_data():
    while True:
        log = q_log.get()
        log_file.write(str(log) + '\n')
        log_file.flush()


def stopmission():
    stop_mission = '$OMSTOP,0*06'
    inst_snd = '$AC;Iver3-' + iver + ';' + '$' + stop_mission + '\r\n'
    pass

def _quit():
    root.quit()
    root.destroy()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)  # print to console
    root = tk.Tk()
    root.wm_title("plot IVER & WAMv")
    fig = plt.Figure(figsize=(5, 4), dpi=100)
    ax = fig.add_subplot(111)

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    toolbar = NavigationToolbar2Tk(canvas, root)
    toolbar.update()

    button = tk.Button(master=root, text="Quit", command=_quit)
    button.pack(side=tk.BOTTOM)

    button = tk.Button(master=root, text="Stop mission", command=stopmission)
    button.pack(side=tk.RIGHT)

    gal = ag.Gallerist(ax, fig, interval=100)

    PlotGeotif(gal).start()
    ReadRf(gal).start()
    LeadV(gal).start()
    # ReadAc(gal).start()

    tk.mainloop()
