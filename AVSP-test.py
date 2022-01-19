import tkinter as tk
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib import (pyplot as plt, animation)
import threading
import time
import logging
import socket
from queue import Queue
import artgallery as ag
import funcgnss
import funcgnss as fg

__author__ = 'Sanjib Sarkar'
__copyright__ = ''
__credits__ = ['', '']
__license__ = ''
__version__ = '1.0.0'
__date__ = 'Jan11, 2022'
__maintainer__ = 'Sanjib Sarkar'
__email__ = 'sanjib.sarkar@usm.edu'
__status__ = 'test'

UDP_IP = 'localhost'
UDP_PORT = 10000
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((UDP_IP, UDP_PORT))

q_co_lvs = Queue()


def coordinates_wamv():
    while True:
        try:
            # print('inside coordinates')
            data, addr = sock.recvfrom(1350)  # correct the comment :buffer size is 1024
            data = data.decode()
        except Exception as e:
            print('Exception at coordinates function', e)
            continue
        coordinate = fg.gpglldecode(data)
        lat, lng, tme = coordinate['Lat_dd'], coordinate['Lng_dd'], coordinate['time']
        q_co_lvs.put({'lat': lat, 'lng': lng, 'tme': tme})
        print({'lat': lat, 'lng': lng, 'tme': tme})


def lvs():
    latlng_lead = []
    timespan = 6
    time.sleep(2)
    iver_art = ag.ImageArtist(gal, label='wam-v animation', alpha=1, zorder=4)
    trace_art = ag.LineArtist(gal, label='vam-v trace', c='g', alpha=0.6, zorder=3)
    icon_size = 0.02
    iver_art.add_data_to_artist('WAM-V_icon_small.png', icon_size, (0, 0), 0)
    while True:
        lead_loc = q_co_lvs.get()
        latlng_lead.append([lead_loc['lat'], lead_loc['lng'], lead_loc['tme']])
        if len(latlng_lead) >= timespan:
            pass
        new_x_lng, new_y_lat, new_t = latlng_lead[-1][1], latlng_lead[-1][0], latlng_lead[-1][2]
        new_xy = ( new_y_lat, new_x_lng, new_t)
        past_x_lng = latlng_lead[-2][1] if len(latlng_lead) > 2 else 0.00
        past_y_lat = latlng_lead[-2][0] if len(latlng_lead) > 2 else 0.00
        past_t = latlng_lead[-2][2] if len(latlng_lead) > 2 else 0.00
        past_xy = (past_y_lat, past_x_lng, past_t)
        deg_ = fungnss.speed_heading_cal(past_xy, new_xy)
        deg = deg_['ha']  # 65  * (math.cos(2 * (math.pi / x_range) * (x_pos - iver_art.ax.get_xlim()[0])) - 90)
        print('Ha:', deg)
        iver_art.set_position((new_x_lng, new_y_lat), deg=10)
        trace_art.add_data_to_artist(new_xy)
        time.sleep(0.1)


class PlotGeotif(threading.Thread):
    def __init__(self):
       threading.Thread.__init__(self, daemon=True)

    def run(self):
            """Work in progress..."""
            satimage = ag.GeoTifArtist(gal, label='Sat plot', zorder=5, alpha=1, add_artist_to_init_func=True)
            satimage.add_data_to_artist('Cat_Island_Low_2.tif')

            noaachart = ag.GeoTifArtist(gal, label='Cat Island ENC', zorder=6, alpha=0.6, add_artist_to_init_func=True)
            noaachart.add_data_to_artist('Cat_Island_ENC.tif')

            satimage.set_xlim(satimage.geotif_xlim[0], satimage.geotif_xlim[1])
            satimage.set_ylim(satimage.geotif_ylim[0], satimage.geotif_ylim[1])

            while True:
                time.sleep(10)


def _quit():
    root.quit()
    root.destroy()


def holdani(anim):
    while True:
        time.sleep(10)
        print('animation holted')
        anim.pause()
        time.sleep(10)
        anim.resume()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)  # print to console
    root = tk.Tk()
    root.wm_title("plot on map")
    fig = plt.Figure(figsize=(5, 4), dpi=100)
    ax = fig.add_subplot(111)

    gal = ag.Gallerist(ax, fig)

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    toolbar = NavigationToolbar2Tk(canvas, root)
    toolbar.update()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    button = tk.Button(master=root, text="Quit", command=_quit)
    button.pack(side=tk.BOTTOM)

    # Using init function is much faster in terms of updating but slower to rescale. It also is not stable!!!
    anim = animation.FuncAnimation(gal.fig, gal.animate, init_func=gal.init_func, interval=100, blit=True)

    PlotGeotif().start()
    threading.Thread(target=coordinates_wamv, daemon=True).start()
    threading.Thread(target=lvs, daemon=True).start()
    tk.mainloop()

